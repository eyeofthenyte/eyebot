"""Resolve and poll public Bluesky accounts through the public AppView."""

from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from services.discordPostingService import DiscordPostingService


APPVIEW = "https://public.api.bsky.app/xrpc"
HANDLE = re.compile(
    r"^(?=.{3,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)


def bluesky_handle(value):
    supplied = str(value or "").strip()
    if supplied.startswith("https://"):
        parsed = urlparse(supplied)
        if parsed.hostname not in {"bsky.app", "www.bsky.app"}:
            raise ValueError("URL must use bsky.app")
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) != 2 or parts[0].casefold() != "profile":
            raise ValueError("URL must identify a Bluesky profile, not a post")
        supplied = parts[1]
    supplied = supplied.removeprefix("@").casefold()
    if supplied.startswith("did:") or not HANDLE.fullmatch(supplied):
        raise ValueError("must be a DNS-style Bluesky handle or profile URL")
    return supplied


async def _get(session, method, params):
    async with session.get(f"{APPVIEW}/{method}", params=params) as response:
        body = await response.json(content_type=None)
        if not 200 <= response.status < 300:
            detail = body.get("message") if isinstance(body, dict) else None
            raise ValueError(detail or f"Bluesky AppView returned HTTP {response.status}")
        return body


async def resolve_bluesky_account(handle, session):
    selected = bluesky_handle(handle)
    profile = await _get(session, "app.bsky.actor.getProfile", {"actor": selected})
    did = str(profile.get("did") or "")
    if not did:
        raise ValueError("Bluesky did not return that public account")
    await _get(
        session,
        "app.bsky.feed.getAuthorFeed",
        {"actor": did, "filter": "posts_no_replies", "limit": 1},
    )
    return {
        "did": did,
        "handle": str(profile.get("handle") or selected).casefold(),
        "display_name": str(profile.get("displayName") or profile.get("handle") or selected),
    }


class BlueskyAccountMonitorService:
    def __init__(self, config, platform_service, logger, *, poll_seconds=120):
        self.config = config
        self.platforms = platform_service
        self.logger = logger
        self.discord = DiscordPostingService(config)
        self.poll_seconds = min(3600, max(30, int(poll_seconds)))
        self.state_path = Path(platform_service.guild_config_dir) / ".bluesky_posts" / "state.json"
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
            settings = self.platforms.effective_guild_platform(guild_id, "bluesky")
            if settings.get("available", True) is not True or settings.get("enabled") is not True:
                continue
            accounts = settings.get("monitored_accounts", ())
            if not isinstance(accounts, (list, tuple)):
                continue
            for configured in accounts:
                if not isinstance(configured, dict):
                    continue
                did = str(configured.get("did") or "")
                handle = str(configured.get("handle") or "").casefold()
                destination = str(
                    configured.get("destination_channel")
                    or settings.get("destination_channel")
                    or ""
                )
                if not did or not handle or not destination.isdigit():
                    continue
                key = f"{guild_id}:{did}"
                active.add(key)
                try:
                    body = await _get(
                        session,
                        "app.bsky.feed.getAuthorFeed",
                        {"actor": did, "filter": "posts_no_replies", "limit": 10},
                    )
                except ValueError as error:
                    self.logger.error(f"Bluesky @{handle} poll failed: {error}")
                    continue
                rows = []
                for item in body.get("feed", ()):
                    if not isinstance(item, dict) or item.get("reason"):
                        continue
                    post = item.get("post") or {}
                    record = post.get("record") or {}
                    if post.get("uri") and not record.get("reply"):
                        rows.append((post, record))
                if key not in self.state:
                    self.state[key] = str(rows[0][0]["uri"]) if rows else ""
                    changed = True
                    continue
                previous = self.state[key]
                pending = []
                for post, record in rows:
                    if str(post["uri"]) == previous:
                        break
                    pending.append((post, record))
                for post, record in reversed(pending):
                    rkey = str(post["uri"]).rsplit("/", 1)[-1]
                    url = f"https://bsky.app/profile/{handle}/post/{rkey}"
                    text = str(record.get("text") or "New post on Bluesky")
                    await self.discord.send(
                        session,
                        destination,
                        f"{text}\n{url}"[:2000],
                        title=f"New post from @{handle} on Bluesky",
                        url=url,
                    )
                if rows and self.state.get(key) != str(rows[0][0]["uri"]):
                    self.state[key] = str(rows[0][0]["uri"])
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
                    self.logger.error(f"Bluesky account monitoring failed: {error}")
                await asyncio.sleep(self.poll_seconds)
