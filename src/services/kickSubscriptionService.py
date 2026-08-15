"""Manage Kick event subscriptions for one authorized guild broadcaster."""

from __future__ import annotations

import asyncio

from services.tokenRefreshService import TokenRefreshService


SUBSCRIPTIONS_URL = "https://api.kick.com/public/v1/events/subscriptions"
CHAT_EVENT = "chat.message.sent"


class KickSubscriptionService:
    def __init__(self, platform_service, logger=None):
        self.platforms = platform_service
        self.logger = logger
        self.tokens = TokenRefreshService(platform_service, logger)

    async def list(self, guild_id, session) -> tuple[dict, ...]:
        settings = self.platforms.effective_guild_platform(guild_id, "kick")
        token = str(settings.get("access_token") or "")
        if not token:
            raise ValueError("Kick access token is unavailable")
        async with session.get(
            SUBSCRIPTIONS_URL,
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            body = await response.json(content_type=None)
            if not 200 <= response.status < 300:
                raise ValueError(
                    f"Kick subscription list failed: "
                    f"{body.get('message') if isinstance(body, dict) else response.status}"
                )
        rows = body.get("data", []) if isinstance(body, dict) else []
        return tuple(row for row in rows if isinstance(row, dict))

    async def ensure_chat(self, guild_id, session) -> str:
        existing = next(
            (row for row in await self.list(guild_id, session) if row.get("event") == CHAT_EVENT),
            None,
        )
        if existing:
            subscription_id = str(existing.get("id") or "")
        else:
            settings = self.platforms.effective_guild_platform(guild_id, "kick")
            token = str(settings.get("access_token") or "")
            async with session.post(
                SUBSCRIPTIONS_URL,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "events": [{"name": CHAT_EVENT, "version": 1}],
                    "method": "webhook",
                },
            ) as response:
                body = await response.json(content_type=None)
                if not 200 <= response.status < 300:
                    raise ValueError(
                        f"Kick chat subscription failed: "
                        f"{body.get('message') if isinstance(body, dict) else response.status}"
                    )
            rows = body.get("data", []) if isinstance(body, dict) else []
            selected = next(
                (row for row in rows if isinstance(row, dict) and row.get("name") == CHAT_EVENT),
                None,
            )
            if not selected or selected.get("error") or not selected.get("subscription_id"):
                raise ValueError(
                    f"Kick did not create the chat subscription: "
                    f"{(selected or {}).get('error') or 'missing subscription ID'}"
                )
            subscription_id = str(selected["subscription_id"])
        self.platforms.set_guild_platform_override(
            guild_id, "kick", "chat_subscription_id", subscription_id
        )
        if self.logger:
            self.logger.info(
                f"Kick chat subscription ready for guild {guild_id}",
                guild_id=guild_id,
            )
        return subscription_id

    async def delete_chat(self, guild_id, session) -> bool:
        rows = await self.list(guild_id, session)
        ids = [str(row.get("id")) for row in rows if row.get("event") == CHAT_EVENT and row.get("id")]
        if not ids:
            return False
        settings = self.platforms.effective_guild_platform(guild_id, "kick")
        async with session.delete(
            SUBSCRIPTIONS_URL,
            headers={"Authorization": f"Bearer {settings.get('access_token')}"},
            params=[("id", value) for value in ids],
        ) as response:
            if response.status != 204:
                body = await response.text()
                raise ValueError(f"Kick subscription deletion failed: {body or response.status}")
        self.platforms.clear_guild_platform_override(
            guild_id, "kick", "chat_subscription_id"
        )
        return True

    async def reconcile_all(self, session) -> None:
        global_settings = self.platforms.platform("kick")
        if global_settings.get("available") is not True:
            return
        if global_settings.get("livestream_chat_commands_enabled") is not True:
            return
        for guild_id in sorted(self.platforms.discord_guilds()):
            settings = self.platforms.effective_guild_platform(guild_id, "kick")
            if not all(
                settings.get(name) is True
                for name in ("enabled", "connected", "livestream_chat_commands_enabled")
            ):
                continue
            try:
                await self.tokens.refresh_guild(guild_id, "kick", session)
                await self.ensure_chat(guild_id, session)
            except Exception as error:
                if self.logger:
                    self.logger.error(
                        f"Unable to reconcile Kick chat subscription for guild "
                        f"{guild_id}: {error}",
                        guild_id=guild_id,
                    )

    async def run_forever(self, session, *, poll_seconds=300) -> None:
        while True:
            await self.reconcile_all(session)
            await asyncio.sleep(poll_seconds)
