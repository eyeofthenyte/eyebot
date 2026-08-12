"""Resolve and poll professional Instagram accounts via Business Discovery."""

from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from services.discordPostingService import DiscordPostingService


GRAPH_ROOT = "https://graph.facebook.com/v26.0"
USERNAME = re.compile(r"^[A-Za-z0-9._]{1,30}$")


def instagram_username(value):
    supplied = str(value or "").strip()
    if supplied.startswith("https://"):
        parsed = urlparse(supplied)
        if parsed.hostname not in {"instagram.com", "www.instagram.com"}:
            raise ValueError("URL must use instagram.com")
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) != 1:
            raise ValueError("URL must identify an account, not Instagram content")
        supplied = parts[0]
    supplied = supplied.removeprefix("@").casefold()
    if not USERNAME.fullmatch(supplied):
        raise ValueError("must be a valid Instagram username or profile URL")
    return supplied


async def _get(session, owner_id, token, username, *, media_limit=10):
    fields = (
        f"business_discovery.username({username})"
        "{id,username,profile_picture_url,"
        f"media.limit({media_limit})"
        "{id,caption,media_type,media_url,permalink,thumbnail_url,timestamp}}"
    )
    async with session.get(
        f"{GRAPH_ROOT}/{owner_id}",
        params={"fields": fields, "access_token": token},
    ) as response:
        body = await response.json(content_type=None)
        if not 200 <= response.status < 300:
            detail = body.get("error", {}).get("message") if isinstance(body, dict) else None
            raise ValueError(detail or f"Meta Graph API returned HTTP {response.status}")
        account = body.get("business_discovery") if isinstance(body, dict) else None
        if not isinstance(account, dict) or not account.get("id"):
            raise ValueError("account is not accessible through Instagram Business Discovery")
        return account


async def resolve_instagram_account(username, owner_id, token, session):
    selected = instagram_username(username)
    account = await _get(session, owner_id, token, selected, media_limit=1)
    return {
        "account_id": str(account["id"]),
        "username": str(account.get("username") or selected).casefold(),
    }


class InstagramAccountMonitorService:
    def __init__(self, config, platform_service, logger, *, poll_seconds=60):
        from services.tokenRefreshService import TokenRefreshService

        self.config = config
        self.platforms = platform_service
        self.logger = logger
        self.discord = DiscordPostingService(config)
        self.tokens = TokenRefreshService(platform_service, logger)
        self.poll_seconds = min(3600, max(30, int(poll_seconds)))
        self.state_path = (
            Path(platform_service.guild_config_dir) / ".instagram_posts" / "state.json"
        )
        try:
            loaded = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.state = loaded if isinstance(loaded, dict) else {}
        except (OSError, UnicodeError, json.JSONDecodeError):
            self.state = {}

    def _save(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(dir=self.state_path.parent, suffix=".tmp")
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(self.state, output, sort_keys=True)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.state_path)
        finally:
            if temporary.exists():
                temporary.unlink()

    async def poll_once(self, session):
        changed = False
        active = set()
        for guild_id in sorted(self.platforms.discord_guilds()):
            settings = self.platforms.effective_guild_platform(guild_id, "instagram")
            if settings.get("available", True) is not True or settings.get("enabled") is not True:
                continue
            try:
                await self.tokens.refresh_guild(guild_id, "instagram", session)
            except (OSError, RuntimeError, ValueError) as error:
                self.logger.error(f"Skipping Instagram accounts for guild {guild_id}: {error}")
                continue
            settings = self.platforms.effective_guild_platform(guild_id, "instagram")
            owner_id = str(settings.get("account_id") or "")
            token = str(settings.get("access_token") or "")
            accounts = settings.get("monitored_accounts", ())
            if not owner_id or not token or not isinstance(accounts, (list, tuple)):
                continue
            for configured in accounts:
                if not isinstance(configured, dict):
                    continue
                username = str(configured.get("username") or "").casefold()
                destination = str(
                    configured.get("destination_channel")
                    or settings.get("destination_channel")
                    or ""
                )
                if not username or not destination.isdigit():
                    continue
                key = f"{guild_id}:{configured.get('account_id') or username}"
                active.add(key)
                try:
                    account = await _get(session, owner_id, token, username)
                except ValueError as error:
                    self.logger.error(f"Instagram @{username} poll failed: {error}")
                    continue
                rows = [
                    row for row in (account.get("media") or {}).get("data", ())
                    if isinstance(row, dict) and row.get("id")
                ]
                if key not in self.state:
                    self.state[key] = str(rows[0]["id"]) if rows else ""
                    changed = True
                    continue
                previous = self.state[key]
                pending = []
                for row in rows:
                    if str(row["id"]) == previous:
                        break
                    pending.append(row)
                for row in reversed(pending):
                    caption = str(row.get("caption") or "New Instagram post")
                    permalink = str(row.get("permalink") or f"https://instagram.com/{username}/")
                    await self.discord.send(
                        session,
                        destination,
                        f"{caption}\n{permalink}"[:2000],
                        title=f"New post from @{username}",
                        url=permalink,
                    )
                if rows and self.state.get(key) != str(rows[0]["id"]):
                    self.state[key] = str(rows[0]["id"])
                    changed = True
        for stale in set(self.state) - active:
            self.state.pop(stale, None)
            changed = True
        if changed:
            self._save()

    async def run_forever(self):
        import aiohttp

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            while True:
                try:
                    await self.poll_once(session)
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    self.logger.error(f"Instagram account monitoring failed: {error}")
                await asyncio.sleep(self.poll_seconds)
