"""Poll the connected guild TikTok account's authorized public videos."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path

from services.discordPostingService import DiscordPostingService
from services.tokenRefreshService import TokenRefreshService


class TikTokVideoMonitorService:
    def __init__(self, config, platform_service, logger, *, poll_seconds=300):
        self.config = config
        self.platforms = platform_service
        self.logger = logger
        self.discord = DiscordPostingService(config)
        self.tokens = TokenRefreshService(platform_service, logger)
        self.poll_seconds = min(3600, max(60, int(poll_seconds)))
        self.state_path = Path(platform_service.guild_config_dir) / ".tiktok_videos" / "state.json"
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
                output.flush(); os.fsync(output.fileno())
            os.replace(temporary, self.state_path)
        finally:
            if temporary.exists(): temporary.unlink()

    async def poll_once(self, session):
        changed = False
        for guild_id in sorted(self.platforms.discord_guilds()):
            settings = self.platforms.effective_guild_platform(guild_id, "tiktok")
            destination = str(settings.get("destination_channel") or "")
            if (
                settings.get("available", True) is not True
                or settings.get("enabled") is not True
                or settings.get("videos_enabled") is not True
                or not destination.isdigit()
            ):
                continue
            try:
                await self.tokens.refresh_guild(guild_id, "tiktok", session)
            except (OSError, RuntimeError, ValueError) as error:
                self.logger.error(f"Skipping TikTok videos for guild {guild_id}: {error}")
                continue
            settings = self.platforms.effective_guild_platform(guild_id, "tiktok")
            token = str(settings.get("access_token") or "")
            if not token:
                continue
            async with session.post(
                "https://open.tiktokapis.com/v2/video/list/",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                params={"fields": "id,title,video_description,share_url,create_time"},
                json={"max_count": 20},
            ) as response:
                body = await response.json(content_type=None)
                if not 200 <= response.status < 300:
                    self.logger.error(f"TikTok video list failed for guild {guild_id}: HTTP {response.status}")
                    continue
            rows = [row for row in body.get("data", {}).get("videos", ()) if row.get("id")]
            previous = self.state.get(str(guild_id))
            if previous is None:
                self.state[str(guild_id)] = str(rows[0]["id"]) if rows else ""
                changed = True
                continue
            pending = []
            for row in rows:
                if str(row["id"]) == previous: break
                pending.append(row)
            for row in reversed(pending):
                url = str(row.get("share_url") or "https://www.tiktok.com/")
                text = str(row.get("title") or row.get("video_description") or "New TikTok video")
                await self.discord.send(session, destination, f"{text}\n{url}"[:2000], title="New TikTok video", url=url)
            if rows:
                self.state[str(guild_id)] = str(rows[0]["id"]); changed = True
        if changed: self._save()

    async def run_forever(self):
        import aiohttp
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            while True:
                try: await self.poll_once(session)
                except asyncio.CancelledError: raise
                except Exception as error: self.logger.error(f"TikTok video monitoring failed: {error}")
                await asyncio.sleep(self.poll_seconds)
