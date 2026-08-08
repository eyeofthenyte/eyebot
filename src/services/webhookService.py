"""Verify supported social webhooks and route events to one guild."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

from services.discordPostingService import DiscordPostingService


class WebhookService:
    def __init__(self, config, platform_service, logger=None):
        self.config = config
        self.platforms = platform_service
        self.logger = logger
        self.discord = DiscordPostingService(config)
        self._seen: dict[str, float] = {}

    def _reject_replay(self, key: str, *, ttl=86400) -> None:
        now = time.monotonic()
        self._seen = {
            existing: seen
            for existing, seen in self._seen.items()
            if now - seen < ttl
        }
        if key in self._seen:
            raise ValueError("Duplicate webhook event")
        self._seen[key] = now

    @staticmethod
    def verify_meta_signature(raw_body: bytes, signature: str, app_secret: str) -> bool:
        if not signature.startswith("sha256=") or not app_secret:
            return False
        expected = hmac.new(
            app_secret.encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature[7:], expected)

    async def meta_challenge(self, guild_id, platform, query):
        settings = self.platforms.effective_guild_platform(guild_id, platform)
        expected = settings.get("webhook_verify_token")
        if query.get("hub.mode") != "subscribe" or not expected:
            raise ValueError("Meta webhook verification is not configured")
        if not hmac.compare_digest(str(query.get("hub.verify_token", "")), str(expected)):
            raise ValueError("Meta webhook verification token is invalid")
        return str(query.get("hub.challenge", ""))

    async def handle_meta(self, guild_id, platform, raw_body, signature, session):
        settings = self.platforms.effective_guild_platform(guild_id, platform)
        if not self.verify_meta_signature(raw_body, signature, str(settings.get("app_secret") or "")):
            raise ValueError("Meta webhook signature is invalid")
        self._reject_replay(
            f"meta:{guild_id}:{hashlib.sha256(raw_body).hexdigest()}"
        )
        payload = json.loads(raw_body)
        destination = settings.get("destination_channel")
        if destination and settings.get("enabled") is True:
            await self.discord.send(
                session,
                destination,
                f"New {platform.title()} event received for the connected account.",
                title=f"{platform.title()} update",
            )
        return payload

    async def handle_kofi(self, guild_id, form, session):
        settings = self.platforms.effective_guild_platform(guild_id, "kofi")
        raw = form.get("data")
        if not raw:
            raise ValueError("Ko-fi webhook is missing data")
        payload = json.loads(raw)
        expected = str(settings.get("verification_token") or "")
        supplied = str(payload.get("verification_token") or "")
        if not expected or not hmac.compare_digest(supplied, expected):
            raise ValueError("Ko-fi verification token is invalid")
        event_id = str(payload.get("kofi_transaction_id") or "")
        if not event_id:
            event_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        self._reject_replay(f"kofi:{guild_id}:{event_id}")
        event_type = str(payload.get("type") or "event")
        toggles = {
            "Donation": "donations_enabled",
            "Subscription": "memberships_enabled",
            "Shop Order": "shop_orders_enabled",
        }
        toggle = toggles.get(event_type)
        destination = settings.get("destination_channel")
        if settings.get("enabled") is True and destination and (
            toggle is None or settings.get(toggle) is True
        ):
            sender = str(payload.get("from_name") or "A supporter")
            amount = str(payload.get("amount") or "")
            currency = str(payload.get("currency") or "")
            await self.discord.send(
                session,
                destination,
                f"☕ **{sender}** sent a Ko-fi {event_type.lower()} {amount} {currency}".strip(),
                title="New Ko-fi event",
            )
        return payload
