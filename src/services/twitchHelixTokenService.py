"""Issue and renew Twitch app tokens used by public Helix detectors."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping


TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TOKEN_EXPIRY_SKEW_SECONDS = 300


class TwitchHelixTokenService:
    """Cache a client-credentials token separately from the Twitch chat token."""

    def __init__(self, settings: Mapping | None, logger=None) -> None:
        self.settings = dict(settings or {})
        self.logger = logger
        self._token = ""
        self._expires_at = 0.0
        self._lock = asyncio.Lock()

    @property
    def uses_app_token(self) -> bool:
        return bool(self.settings.get("client_id") and self.settings.get("client_secret"))

    def invalidate(self) -> None:
        self._token = ""
        self._expires_at = 0.0

    async def access_token(self, session, *, force=False) -> str:
        """Return a valid app token, or the legacy user token when unconfigured."""
        if not self.uses_app_token:
            return str(self.settings.get("tmi_token") or "").removeprefix("oauth:")
        now = time.monotonic()
        if not force and self._token and now < self._expires_at:
            return self._token
        async with self._lock:
            now = time.monotonic()
            if not force and self._token and now < self._expires_at:
                return self._token
            async with session.post(
                TWITCH_TOKEN_URL,
                data={
                    "client_id": str(self.settings["client_id"]),
                    "client_secret": str(self.settings["client_secret"]),
                    "grant_type": "client_credentials",
                },
            ) as response:
                body = await response.json(content_type=None)
                if not 200 <= response.status < 300:
                    message = body.get("message") or body.get("error") or response.status
                    raise RuntimeError(f"Twitch app-token request failed: {message}")
            token = str(body.get("access_token") or "")
            if not token:
                raise RuntimeError("Twitch app-token response did not contain an access token")
            try:
                expires_in = max(0, int(body.get("expires_in", 0)))
            except (TypeError, ValueError):
                expires_in = 0
            lifetime = max(1, expires_in - TOKEN_EXPIRY_SKEW_SECONDS)
            self._token = token
            self._expires_at = time.monotonic() + lifetime
            if self.logger:
                self.logger.info("Renewed Twitch Helix app access token")
            return token
