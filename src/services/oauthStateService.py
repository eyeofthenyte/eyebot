"""Short-lived, signed, single-use OAuth state and PKCE management."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from pathlib import Path


MAX_STATE_AGE_SECONDS = 600


def resolve_oauth_state_key() -> bytes:
    """Resolve a dedicated key or derive one from the existing master key."""
    import os

    configured = os.getenv("EYEBOT_OAUTH_STATE_KEY")
    if configured:
        return configured.encode("utf-8")
    key_file = os.getenv("EYEBOT_OAUTH_STATE_KEY_FILE")
    if key_file and Path(key_file).is_file():
        return Path(key_file).read_bytes().strip()
    master_file = os.getenv("EYEBOT_MASTER_KEY_FILE")
    if master_file and Path(master_file).is_file():
        return hmac.new(
            Path(master_file).read_bytes().strip(),
            b"eyebot-oauth-state-v1",
            hashlib.sha256,
        ).digest()
    raise RuntimeError(
        "OAuth requires EYEBOT_OAUTH_STATE_KEY or the configured master key file"
    )


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


@dataclass(frozen=True)
class OAuthState:
    guild_id: str
    platform: str
    moderator_id: str
    nonce: str
    issued_at: int
    code_verifier: str


class OAuthStateService:
    def __init__(self, signing_key: str | bytes, *, max_age=MAX_STATE_AGE_SECONDS):
        key = signing_key.encode("utf-8") if isinstance(signing_key, str) else signing_key
        if not key or len(key) < 32:
            raise ValueError("OAuth state signing key must contain at least 32 bytes")
        self.key = key
        self.max_age = max_age
        self._pending: dict[str, OAuthState] = {}
        self._used_start_nonces: set[str] = set()

    def issue(self, guild_id: str, platform: str, moderator_id: str) -> tuple[str, OAuthState]:
        state = OAuthState(
            guild_id=str(guild_id),
            platform=platform.casefold(),
            moderator_id=str(moderator_id),
            nonce=secrets.token_urlsafe(24),
            issued_at=int(time.time()),
            code_verifier=secrets.token_urlsafe(64),
        )
        payload = json.dumps(
            {
                "g": state.guild_id,
                "p": state.platform,
                "u": state.moderator_id,
                "n": state.nonce,
                "iat": state.issued_at,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        encoded = _b64encode(payload)
        signature = _b64encode(hmac.new(self.key, encoded.encode("ascii"), hashlib.sha256).digest())
        token = f"{encoded}.{signature}"
        self._pending[state.nonce] = state
        return token, state

    def sign_start_request(self, guild_id: str, platform: str, moderator_id: str) -> str:
        payload = json.dumps(
            {
                "g": str(guild_id),
                "p": platform.casefold(),
                "u": str(moderator_id),
                "iat": int(time.time()),
                "n": secrets.token_urlsafe(16),
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        encoded = _b64encode(payload)
        signature = _b64encode(
            hmac.new(self.key, encoded.encode("ascii"), hashlib.sha256).digest()
        )
        return f"{encoded}.{signature}"

    def verify_start_request(self, token: str) -> dict[str, str]:
        try:
            encoded, supplied = token.split(".", 1)
            expected = _b64encode(
                hmac.new(self.key, encoded.encode("ascii"), hashlib.sha256).digest()
            )
            if not hmac.compare_digest(supplied, expected):
                raise ValueError("signature mismatch")
            payload = json.loads(_b64decode(encoded))
            if int(time.time()) - int(payload["iat"]) > self.max_age:
                raise ValueError("request expired")
            nonce = str(payload["n"])
            if nonce in self._used_start_nonces:
                raise ValueError("request already used")
            self._used_start_nonces.add(nonce)
            return {
                "guild_id": str(payload["g"]),
                "platform": str(payload["p"]),
                "moderator_id": str(payload["u"]),
            }
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError("OAuth start request is invalid or expired") from error

    def consume(self, token: str) -> OAuthState:
        try:
            encoded, supplied_signature = token.split(".", 1)
            expected = _b64encode(hmac.new(self.key, encoded.encode("ascii"), hashlib.sha256).digest())
            if not hmac.compare_digest(supplied_signature, expected):
                raise ValueError("OAuth state signature is invalid")
            payload = json.loads(_b64decode(encoded))
            nonce = str(payload["n"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError("OAuth state is invalid") from error
        state = self._pending.pop(nonce, None)
        if state is None:
            raise ValueError("OAuth state is unknown, expired, or already used")
        if int(time.time()) - state.issued_at > self.max_age:
            raise ValueError("OAuth state has expired")
        return state

    @staticmethod
    def code_challenge(state: OAuthState) -> str:
        return _b64encode(hashlib.sha256(state.code_verifier.encode("ascii")).digest())
