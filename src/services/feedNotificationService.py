"""Per-guild Substack RSS state and Discord delivery."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from adapters.substack_adapter import SUBSTACK_ADAPTER
from services.discordPostingService import DiscordPostingService


class FeedNotificationService:
    def __init__(self, config, platform_service, logger):
        self.config = config
        self.platforms = platform_service
        self.logger = logger
        self.discord = DiscordPostingService(config)
        self.state_path = platform_service.guild_config_dir / ".feed_state" / "substack.json"
        try:
            self.state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.state = {}

    def save(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.state, sort_keys=True), encoding="utf-8")
        temporary.replace(self.state_path)

    async def poll_once(self, session):
        changed = False
        for guild_id in sorted(self.platforms.discord_guilds()):
            settings = self.platforms.effective_guild_platform(guild_id, "substack")
            destination = settings.get("destination_channel")
            if settings.get("enabled") is not True or not str(destination or "").isdigit():
                continue
            entries = await SUBSTACK_ADAPTER.fetch_feed(settings)
            recent = list(entries[:20])
            last_seen = self.state.get(guild_id)
            new_entries = []
            for entry in recent:
                event_id = str(entry.get("id") or entry.get("link") or "")
                if not event_id:
                    continue
                if event_id == last_seen:
                    break
                new_entries.append(entry)
            # On a fresh connection announce at most the newest item.
            if last_seen is None:
                new_entries = new_entries[:1]
            for entry in reversed(new_entries):
                event_id = str(entry.get("id") or entry.get("link") or "")
                enclosures = entry.get("enclosures") or []
                is_podcast = any(
                    str(item.get("type") or "").startswith("audio/")
                    for item in enclosures
                )
                enabled = settings.get(
                    "podcasts_enabled" if is_podcast else "newsletters_enabled"
                ) is True
                if enabled:
                    title = str(entry.get("title") or "New Substack post")
                    link = str(entry.get("link") or "")
                    await self.discord.send(
                        session,
                        destination,
                        f"📰 **{title}**\n{link}"[:2000],
                        title="New Substack podcast" if is_podcast else "New Substack newsletter",
                        url=link,
                    )
                self.state[guild_id] = event_id
                changed = True
            if changed:
                self.save()

    async def run_forever(self):
        import aiohttp

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            while True:
                try:
                    await self.poll_once(session)
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    self.logger.error(f"Substack feed polling failed: {error}")
                await asyncio.sleep(300)
