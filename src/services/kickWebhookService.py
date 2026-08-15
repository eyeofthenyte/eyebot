"""Authenticate Kick webhook requests and reject stale or duplicate events."""

from __future__ import annotations

import base64
import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


KICK_PUBLIC_KEY = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAq/+l1WnlRrGSolDMA+A8
6rAhMbQGmQ2SapVcGM3zq8ANXjnhDWocMqfWcTd95btDydITa10kDvHzw9WQOqp2
MZI7ZyrfzJuz5nhTPCiJwTwnEtWft7nV14BYRDHvlfqPUaZ+1KR4OCaO/wWIk/rQ
L/TjY0M70gse8rlBkbo2a8rKhu69RQTRsoaf4DVhDPEeSeI5jVrRDGAMGL3cGuyY
6CLKGdjVEM78g3JfYOvDU/RvfqD7L89TZ3iN94jrmWdGz34JNlEI5hqK8dd7C5EF
BEbZ5jgB8s8ReQV8H+MkuffjdAj3ajDDX3DOJMIut1lBrUVD1AaSrGCKHooWoL2e
twIDAQAB
-----END PUBLIC KEY-----
"""
KICK_PUBLIC_KEY_URL = "https://api.kick.com/public/v1/public-key"

REQUIRED_HEADERS = (
    "Kick-Event-Message-Id",
    "Kick-Event-Subscription-Id",
    "Kick-Event-Signature",
    "Kick-Event-Message-Timestamp",
    "Kick-Event-Type",
    "Kick-Event-Version",
)


class KickWebhookError(ValueError):
    """Base class for rejected Kick webhooks."""


class KickWebhookAuthenticationError(KickWebhookError):
    """The webhook signature or timestamp is invalid."""


class KickWebhookDuplicateError(KickWebhookError):
    """The webhook message ID was already accepted."""


@dataclass(frozen=True)
class KickWebhookEvent:
    message_id: str
    subscription_id: str
    event_type: str
    event_version: str
    timestamp: datetime
    payload: dict


class KickWebhookService:
    def __init__(
        self,
        state_path: str | Path,
        *,
        public_key_pem: bytes = KICK_PUBLIC_KEY,
        freshness_seconds: int = 300,
        duplicate_ttl_seconds: int = 86400,
        now=None,
    ):
        self.state_path = Path(state_path)
        self.public_key = serialization.load_pem_public_key(public_key_pem)
        self.freshness = timedelta(seconds=freshness_seconds)
        self.duplicate_ttl = timedelta(seconds=duplicate_ttl_seconds)
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._lock = threading.RLock()
        self._seen = self._load_state()
        self._inflight: set[str] = set()

    async def refresh_public_key(self, session) -> bool:
        """Refresh Kick's verification key over HTTPS, retaining the bundled fallback."""
        async with session.get(KICK_PUBLIC_KEY_URL) as response:
            body = await response.json(content_type=None)
            if not 200 <= response.status < 300:
                raise KickWebhookAuthenticationError(
                    f"Unable to refresh Kick public key: HTTP {response.status}"
                )
        data = body.get("data", {}) if isinstance(body, dict) else {}
        pem = data.get("public_key") if isinstance(data, dict) else None
        if not pem:
            raise KickWebhookAuthenticationError("Kick public-key response is invalid")
        self.public_key = serialization.load_pem_public_key(str(pem).encode("utf-8"))
        return True

    def _load_state(self) -> dict[str, str]:
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}
        return {
            str(key): str(timestamp)
            for key, timestamp in value.items()
            if isinstance(key, str) and isinstance(timestamp, str)
        } if isinstance(value, dict) else {}

    @staticmethod
    def _header(headers, name: str) -> str:
        for key, value in headers.items():
            if str(key).casefold() == name.casefold():
                return str(value).strip()
        return ""

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise KickWebhookAuthenticationError(
                "Kick webhook timestamp is invalid"
            ) from error
        if parsed.tzinfo is None:
            raise KickWebhookAuthenticationError(
                "Kick webhook timestamp must include a timezone"
            )
        return parsed.astimezone(timezone.utc)

    def authenticate(self, raw_body: bytes, headers) -> KickWebhookEvent:
        missing = [name for name in REQUIRED_HEADERS if not self._header(headers, name)]
        if missing:
            raise KickWebhookError(
                "Kick webhook is missing required headers: " + ", ".join(missing)
            )
        message_id = self._header(headers, "Kick-Event-Message-Id")
        timestamp_text = self._header(headers, "Kick-Event-Message-Timestamp")
        timestamp = self._parse_timestamp(timestamp_text)
        now = self._now().astimezone(timezone.utc)
        if timestamp < now - self.freshness or timestamp > now + timedelta(seconds=60):
            raise KickWebhookAuthenticationError("Kick webhook timestamp is stale")
        try:
            signature = base64.b64decode(
                self._header(headers, "Kick-Event-Signature"), validate=True
            )
        except (ValueError, TypeError) as error:
            raise KickWebhookAuthenticationError(
                "Kick webhook signature is invalid"
            ) from error
        signed_message = b".".join(
            (message_id.encode("utf-8"), timestamp_text.encode("utf-8"), raw_body)
        )
        try:
            self.public_key.verify(
                signature,
                signed_message,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except InvalidSignature as error:
            raise KickWebhookAuthenticationError(
                "Kick webhook signature is invalid"
            ) from error
        try:
            payload = json.loads(raw_body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise KickWebhookError("Kick webhook body is not valid JSON") from error
        if not isinstance(payload, dict):
            raise KickWebhookError("Kick webhook body must be a JSON object")
        with self._lock:
            self._prune(now)
            if message_id in self._seen or message_id in self._inflight:
                raise KickWebhookDuplicateError("Duplicate Kick webhook event")
        return KickWebhookEvent(
            message_id=message_id,
            subscription_id=self._header(headers, "Kick-Event-Subscription-Id"),
            event_type=self._header(headers, "Kick-Event-Type"),
            event_version=self._header(headers, "Kick-Event-Version"),
            timestamp=timestamp,
            payload=payload,
        )

    def remember(self, event: KickWebhookEvent) -> None:
        self.remember_message_id(event.message_id)

    def claim(self, event: KickWebhookEvent) -> None:
        with self._lock:
            if event.message_id in self._seen or event.message_id in self._inflight:
                raise KickWebhookDuplicateError("Duplicate Kick webhook event")
            self._inflight.add(event.message_id)

    def release(self, message_id: str) -> None:
        with self._lock:
            self._inflight.discard(message_id)

    def remember_message_id(self, message_id: str) -> None:
        with self._lock:
            now = self._now().astimezone(timezone.utc)
            self._prune(now)
            if message_id in self._seen:
                raise KickWebhookDuplicateError("Duplicate Kick webhook event")
            self._inflight.discard(message_id)
            self._seen[message_id] = now.isoformat()
            self._save_state()

    def _prune(self, now: datetime) -> None:
        retained = {}
        for message_id, timestamp in self._seen.items():
            try:
                seen = datetime.fromisoformat(timestamp).astimezone(timezone.utc)
            except ValueError:
                continue
            if seen >= now - self.duplicate_ttl:
                retained[message_id] = timestamp
        self._seen = retained

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as output:
            json.dump(self._seen, output, indent=2, sort_keys=True)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, self.state_path)
