"""Resolve and poll public X accounts through the official X API v2."""

from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from services.discordPostingService import DiscordPostingService


API_ROOT = "https://api.x.com/2"
USERNAME = re.compile(r"^[A-Za-z0-9_]{1,15}$")


def twitter_username(value):
    supplied = str(value or "").strip()
    if supplied.startswith("https://"):
        parsed = urlparse(supplied)
        if parsed.hostname not in {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}:
            raise ValueError("URL must use x.com or twitter.com")
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) != 1:
            raise ValueError("URL must identify an account, not X content")
        supplied = parts[0]
    supplied = supplied.removeprefix("@").casefold()
    if not USERNAME.fullmatch(supplied):
        raise ValueError("must be a valid X username or profile URL")
    return supplied


async def _get(session, path, token, params=None):
    async with session.get(
        f"{API_ROOT}/{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params or {},
    ) as response:
        body = await response.json(content_type=None)
        if not 200 <= response.status < 300:
            detail = None
            if isinstance(body, dict):
                errors = body.get("errors") or ()
                detail = body.get("detail") or body.get("title")
                if not detail and errors and isinstance(errors[0], dict):
                    detail = errors[0].get("detail") or errors[0].get("message")
            raise ValueError(detail or f"X API returned HTTP {response.status}")
        return body


async def resolve_twitter_account(username, token, session):
    selected = twitter_username(username)
    body = await _get(
        session,
        f"users/by/username/{selected}",
        token,
        {"user.fields": "id,name,username,protected"},
    )
    user = body.get("data") if isinstance(body, dict) else None
    if not isinstance(user, dict) or not user.get("id"):
        raise ValueError("X did not return that account")
    if user.get("protected") is True:
        raise ValueError("protected X accounts cannot be monitored")
    # Verify that the app's current access can read the account timeline.
    await _get(
        session,
        f"users/{user['id']}/tweets",
        token,
        {"max_results": 5, "exclude": "replies,retweets"},
    )
    return {
        "user_id": str(user["id"]),
        "username": str(user.get("username") or selected).casefold(),
        "name": str(user.get("name") or user.get("username") or selected),
    }


class TwitterAccountMonitorService:
    def __init__(self, config, platform_service, logger, *, poll_seconds=300):
        from services.tokenRefreshService import TokenRefreshService

        self.config = config
        self.platforms = platform_service
        self.logger = logger
        self.discord = DiscordPostingService(config)
        self.tokens = TokenRefreshService(platform_service, logger)
        self.poll_seconds = min(3600, max(60, int(poll_seconds)))
        self.state_path = Path(platform_service.guild_config_dir) / ".twitter_posts" / "state.json"
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
            settings = self.platforms.effective_guild_platform(guild_id, "twitter")
            if settings.get("available", True) is not True or settings.get("enabled") is not True:
                continue
            try:
                await self.tokens.refresh_guild(guild_id, "twitter", session)
            except (OSError, RuntimeError, ValueError) as error:
                self.logger.error(
                    f"Skipping X accounts for guild {guild_id}: {error}",
                    guild_id=guild_id,
                )
                continue
            settings = self.platforms.effective_guild_platform(guild_id, "twitter")
            token = str(settings.get("bearer_token") or settings.get("access_token") or "")
            accounts = settings.get("monitored_accounts", ())
            if not token or not isinstance(accounts, (list, tuple)):
                continue
            for configured in accounts:
                if not isinstance(configured, dict):
                    continue
                user_id = str(configured.get("user_id") or "")
                username = str(configured.get("username") or "").casefold()
                destination = str(
                    configured.get("destination_channel")
                    or settings.get("destination_channel")
                    or ""
                )
                if not user_id or not username or not destination.isdigit():
                    continue
                key = f"{guild_id}:{user_id}"
                active.add(key)
                params = {
                    "max_results": 10,
                    "exclude": "replies,retweets",
                    "tweet.fields": "id,text,created_at",
                }
                if self.state.get(key):
                    params["since_id"] = self.state[key]
                try:
                    body = await _get(session, f"users/{user_id}/tweets", token, params)
                except ValueError as error:
                    self.logger.error(
                        f"X account @{username} poll failed: {error}",
                        guild_id=guild_id,
                    )
                    continue
                rows = [
                    row for row in body.get("data", ())
                    if isinstance(row, dict) and row.get("id")
                ]
                if key not in self.state:
                    self.state[key] = str(rows[0]["id"]) if rows else ""
                    changed = True
                    continue
                for row in reversed(rows):
                    post_id = str(row["id"])
                    url = f"https://x.com/{username}/status/{post_id}"
                    await self.discord.send(
                        session,
                        destination,
                        f"{str(row.get('text') or 'New post on X')}\n{url}"[:2000],
                        title=f"New post from @{username} on X",
                        url=url,
                    )
                if rows:
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
                    self.logger.error(f"X account monitoring failed: {error}")
                await asyncio.sleep(self.poll_seconds)
