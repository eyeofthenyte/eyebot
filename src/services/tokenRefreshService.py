"""Refresh expiring per-guild OAuth credentials without blocking siblings."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aiohttp import BasicAuth

from core.oauth_provider import get_oauth_provider
from services.platformConnectionService import PlatformConnectionService


class TokenRefreshService:
    def __init__(self, platform_service, logger=None):
        self.platforms = platform_service
        self.connections = PlatformConnectionService(platform_service)
        self.logger = logger

    @staticmethod
    def needs_refresh(settings, *, within_seconds=300) -> bool:
        expires_at = settings.get("expires_at")
        if not expires_at:
            return False
        try:
            expiration = datetime.fromisoformat(str(expires_at))
            if expiration.tzinfo is None:
                return False
        except ValueError:
            return False
        return expiration <= datetime.now(timezone.utc) + timedelta(seconds=within_seconds)

    async def refresh_guild(self, guild_id, platform, session) -> bool:
        settings = self.platforms.effective_guild_platform(guild_id, platform)
        if not self.needs_refresh(settings):
            return False
        provider = get_oauth_provider(platform)
        refresh_token = settings.get("refresh_token")
        client_id = settings.get(provider.client_id_parameter)
        client_secret = settings.get(provider.client_secret_parameter)
        if not client_id or not client_secret:
            raise ValueError(f"{platform} connection cannot refresh missing credentials")
        if platform in {"facebook", "instagram"}:
            current_token = settings.get("access_token")
            if not current_token:
                raise ValueError(f"{platform} access token is missing")
            async with session.get(
                "https://graph.facebook.com/v26.0/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "fb_exchange_token": current_token,
                },
            ) as response:
                body = await response.json(content_type=None)
                if not 200 <= response.status < 300:
                    raise ValueError(
                        f"{platform} refresh failed: {body.get('error') or response.status}"
                    )
            self.connections.save_token_response(guild_id, platform, body)
            return True
        if not refresh_token:
            raise ValueError(f"{platform} refresh token is missing")
		payload = {
			"grant_type": "refresh_token",
			"refresh_token": refresh_token,
		}
		request_options = {}

		if provider.uses_basic_token_auth:
			request_options["auth"] = BasicAuth(
				client_id,
				client_secret,
			)
		else:
			payload[provider.token_client_field] = client_id
			payload["client_secret"] = client_secret

		async with session.post(
			provider.token_url,
			data=payload,
			**request_options,
		) as response:
            body = await response.json(content_type=None)
            if not 200 <= response.status < 300:
                raise ValueError(
                    f"{platform} refresh failed: "
                    f"{body.get('error_description') or body.get('error') or response.status}"
                )
        body.setdefault("refresh_token", refresh_token)
        self.connections.save_token_response(guild_id, platform, body)
        if self.logger:
            self.logger.info(f"Refreshed {platform} authorization for guild {guild_id}")
        return True
