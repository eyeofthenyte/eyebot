"""Persist non-secret connection metadata and encrypted OAuth tokens."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


class PlatformConnectionService:
    def __init__(self, platform_config_service):
        self.platforms = platform_config_service

    def save_token_response(self, guild_id, platform, token_response: dict) -> None:
        access_token = token_response.get("access_token")
        if not access_token:
            raise ValueError("OAuth response did not contain an access token")
        secrets = self.platforms.secret_service
        secrets.set_secret(platform, "access_token", str(access_token), guild_id=guild_id)
        user_access_token = token_response.get("user_access_token")
        if user_access_token and platform == "facebook":
            secrets.set_secret(
                platform,
                "user_access_token",
                str(user_access_token),
                guild_id=guild_id,
            )
        refresh_token = token_response.get("refresh_token")
        if refresh_token:
            secrets.set_secret(platform, "refresh_token", str(refresh_token), guild_id=guild_id)

        expires_at = None
        try:
            expires_in = int(token_response.get("expires_in", 0))
            if expires_in > 0:
                expires_at = (
                    datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                ).isoformat()
        except (TypeError, ValueError):
            pass
        metadata = {
            "connected": True,
            "token_type": str(token_response.get("token_type") or "Bearer"),
            "scope": token_response.get("scope") or token_response.get("scopes") or [],
            "expires_at": expires_at,
            "connected_at": datetime.now(timezone.utc).isoformat(),
        }
        for key, value in metadata.items():
            self.platforms.set_guild_platform_override(guild_id, platform, key, value)

    def disconnect(self, guild_id, platform) -> None:
        for parameter in ("access_token", "user_access_token", "refresh_token"):
            try:
                self.platforms.secret_service.delete_secret(
                    platform, parameter, guild_id=guild_id
                )
            except ValueError:
                pass
        for parameter in (
            "connected",
            "token_type",
            "scope",
            "expires_at",
            "connected_at",
            "account_id",
            "account_name",
            "broadcaster_user_id",
            "chat_subscription_id",
        ):
            self.platforms.clear_guild_platform_override(guild_id, platform, parameter)
