"""Shared polling and Discord delivery primitives for platform-owned detectors."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

DISCORD_API = "https://discord.com/api/v10"
DEFAULT_POLL_SECONDS = 60


@dataclass(frozen=True)
class LiveEvent:
    event_id: str
    title: str
    url: str
    broadcaster: str
    description: str = ""
    thumbnail_url: str = ""


def load_platform_runtime(platform_name: str):
    """Load the split config used by one independently supervised child."""
    from services.platformConfigService import load_split_config

    project_root = Path(__file__).resolve().parents[2]
    config, _global, platform_service = load_split_config(
        os.getenv("EYEBOT_CONFIG_PATH", str(project_root / "config.yaml")),
        os.getenv("EYEBOT_PLATFORM_CONFIG_PATH", str(project_root / "platforms.yaml")),
        guild_config_dir=os.getenv(
            "EYEBOT_GUILD_CONFIG_DIR",
            str(project_root / "data" / "guilds"),
        ),
    )
    config.setdefault("logging", {"level": "INFO", "output": "syslog"})
    config.setdefault(platform_name, {})
    return config, platform_service


class LiveNotificationService:
    """Poll one platform detector and publish newly-live events to Discord."""

    def __init__(
        self,
        platform_name: str,
        config: Mapping,
        platform_service,
        detector: Callable[[Mapping, object], Awaitable[LiveEvent | None]],
        logger,
        *,
        poll_seconds: int | None = None,
    ) -> None:
        self.platform_name = platform_name
        self.config = config
        self.platform_service = platform_service
        self.detector = detector
        self.logger = logger
        configured_interval = config.get(platform_name, {}).get(
            "live_poll_seconds", DEFAULT_POLL_SECONDS
        )
        self.poll_seconds = poll_seconds or self._bounded_interval(configured_interval)
        state_root = Path(
            os.getenv(
                "EYEBOT_LIVE_STATE_DIR",
                str(Path(platform_service.guild_config_dir) / ".live_state"),
            )
        )
        self.state_path = state_root / f"{platform_name}.json"
        self.state = self._load_state()
        from services.tokenRefreshService import TokenRefreshService

        self.token_refresher = TokenRefreshService(platform_service, logger)

    @staticmethod
    def _bounded_interval(value) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return DEFAULT_POLL_SECONDS
        return min(3600, max(30, parsed))

    def _load_state(self) -> dict[str, str]:
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, UnicodeError, json.JSONDecodeError):
            return {}

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.state_path.parent,
            prefix=f".{self.platform_name}-",
            suffix=".tmp",
            text=True,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(self.state, output, sort_keys=True)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.state_path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _targets(self):
        for guild_id in sorted(self.platform_service.discord_guilds()):
            effective = self.platform_service.effective_guild_platform(
                guild_id, self.platform_name
            )
            if effective.get("available", True) is not True:
                continue
            if effective.get("enabled") is not True:
                continue
            destination = effective.get("destination_channel")
            if not str(destination or "").isdigit():
                continue
            yield str(guild_id), str(destination), effective

    async def _post_discord(
        self,
        session,
        channel_id: str,
        event: LiveEvent,
    ) -> None:
        discord = self.config.get("discord", {})
        token = discord.get("bot_token", "") if isinstance(discord, Mapping) else ""
        if not token:
            raise RuntimeError("discord.bot_token is unavailable to live notifier")
        embed = {
            "title": event.title[:256] or f"{event.broadcaster} is live",
            "url": event.url,
            "description": event.description[:4096],
            "color": 0xED4245,
            "author": {"name": f"{event.broadcaster} is live on {self.platform_name.title()}"},
        }
        if event.thumbnail_url.startswith("https://"):
            embed["image"] = {"url": event.thumbnail_url}
        payload = {
            "content": f"🔴 **{event.broadcaster} is live on {self.platform_name.title()}!**\n{event.url}"[:2000],
            "embeds": [embed],
            "allowed_mentions": {"parse": []},
        }
        async with session.post(
            f"{DISCORD_API}/channels/{channel_id}/messages",
            headers={"Authorization": f"Bot {token}"},
            json=payload,
        ) as response:
            if response.status not in {200, 201}:
                detail = (await response.text())[:500]
                raise RuntimeError(
                    f"Discord post failed for channel {channel_id}: "
                    f"HTTP {response.status} {detail}"
                )

    async def poll_once(self, session) -> None:
        cache: dict[str, LiveEvent | None] = {}
        failed_sources = set()
        active_keys = set()
        changed = False
        for guild_id, destination, effective in self._targets():
            if self.platform_name in {
                "youtube",
                "facebook",
                "instagram",
                "kick",
                "twitter",
                "tiktok",
            }:
                try:
                    await self.token_refresher.refresh_guild(
                        guild_id, self.platform_name, session
                    )
                except Exception as error:
                    self.logger.error(
                        f"Skipping {self.platform_name} live check for guild "
                        f"{guild_id}: token refresh failed: {error}"
                    )
                    continue
                effective = self.platform_service.effective_guild_platform(
                    guild_id, self.platform_name
                )
            source_key = json.dumps(
                {
                    key: effective.get(key)
                    for key in (
                        "channel",
                        "channel_id",
                        "page_id",
                        "account_id",
                        "open_id",
                        "user_id",
                    )
                },
                sort_keys=True,
            )
            if source_key in failed_sources:
                continue
            if source_key not in cache:
                try:
                    cache[source_key] = await self.detector(effective, session)
                except Exception as error:
                    self.logger.error(
                        f"{self.platform_name} detector failed for guild "
                        f"{guild_id}: {error}"
                    )
                    failed_sources.add(source_key)
                    continue
            event = cache[source_key]
            state_key = f"{guild_id}:{destination}:{source_key}"
            active_keys.add(state_key)
            if event is None:
                if state_key in self.state:
                    self.state.pop(state_key, None)
                    changed = True
                continue
            if self.state.get(state_key) == event.event_id:
                continue
            try:
                await self._post_discord(session, destination, event)
            except Exception as error:
                self.logger.error(
                    f"Discord live delivery failed for guild {guild_id}: {error}"
                )
                continue
            self.state[state_key] = event.event_id
            changed = True
            self.logger.info(
                f"Posted {self.platform_name} live event {event.event_id} "
                f"for guild {guild_id} to Discord channel {destination}"
            )
        stale = set(self.state) - active_keys
        if stale:
            for key in stale:
                self.state.pop(key, None)
            changed = True
        if changed:
            self._save_state()

    async def run_forever(self) -> None:
        import aiohttp

        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while True:
                try:
                    await self.poll_once(session)
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    self.logger.error(
                        f"{self.platform_name} live detection failed: {error}"
                    )
                await asyncio.sleep(self.poll_seconds)
