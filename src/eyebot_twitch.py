from __future__ import annotations

import asyncio
import os

from twitchio.ext import commands

from adapters.twitch_adapter import TwitchTransportAdapter
from core.command_model import CommandPlatform
from core.platform_config import is_platform_enabled
from core.portable_runtime import build_portable_runtime
from core.twitch_config import resolve_twitch_channels
from services.logService import LogService
from services.liveNotificationService import LiveEvent, LiveNotificationService
from services.platformConfigService import load_split_config


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
config, _global_config_service, platform_config_service = load_split_config(
    os.getenv("EYEBOT_CONFIG_PATH", os.path.join(project_root, "config.yaml")),
    os.getenv(
        "EYEBOT_PLATFORM_CONFIG_PATH",
        os.path.join(project_root, "platforms.yaml"),
    ),
    guild_config_dir=os.getenv(
        "EYEBOT_GUILD_CONFIG_DIR",
        os.path.join(project_root, "data", "guilds"),
    ),
)
config.setdefault("prefix", "!")
config.setdefault("logging", {})
config.setdefault("twitch", {})
config["twitch"].setdefault("enabled", False)

BOT_PREFIX = config["prefix"] or "!"
TWITCH_ENABLED = is_platform_enabled(config, CommandPlatform.TWITCH)
TMI_TOKEN = config["twitch"].get("tmi_token", "")
CLIENT_ID = config["twitch"].get("client_id", "")
BOT_NICK = config["twitch"].get("nick", "")
CHANNELS = resolve_twitch_channels(config, platform_config_service)

logger = LogService("twitch", config["logging"])


async def detect_twitch_live(settings, session):
    """Detect one configured Twitch channel through the official Helix API."""
    channel = str(settings.get("channel") or "").strip().casefold()
    token = str(settings.get("tmi_token") or "").removeprefix("oauth:")
    client_id = str(settings.get("client_id") or "")
    if not channel or not token or not client_id:
        return None
    async with session.get(
        "https://api.twitch.tv/helix/streams",
        params={"user_login": channel},
        headers={"Authorization": f"Bearer {token}", "Client-Id": client_id},
    ) as response:
        response.raise_for_status()
        rows = (await response.json()).get("data", [])
    if not rows:
        return None
    stream = rows[0]
    thumbnail = str(stream.get("thumbnail_url") or "").replace("{width}", "1280").replace("{height}", "720")
    return LiveEvent(
        event_id=str(stream["id"]),
        title=str(stream.get("title") or f"{channel} is live"),
        url=f"https://www.twitch.tv/{channel}",
        broadcaster=str(stream.get("user_name") or channel),
        description=str(stream.get("game_name") or ""),
        thumbnail_url=thumbnail,
    )


def validate_twitch_config():
    missing = []
    if not TMI_TOKEN:
        missing.append("twitch.tmi_token")
    if not CHANNELS:
        missing.append("twitch.channels")
    return tuple(missing)


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=TMI_TOKEN,
            client_id=CLIENT_ID,
            nick=BOT_NICK,
            prefix=BOT_PREFIX,
            initial_channels=CHANNELS,
        )
        self.logger = logger
        self.config = config
        self.command_host, self.command_router = build_portable_runtime(
            config=config,
            logger=logger,
        )
        self.command_transport = TwitchTransportAdapter(
            self.command_router,
            prefix=BOT_PREFIX,
        )
        self.live_notifier = LiveNotificationService(
            "twitch", config, platform_config_service, detect_twitch_live, logger
        )
        self.live_notification_task = None

    async def event_ready(self):
        logger.info(f"Logged in as | {self.nick}")
        logger.info(f"User id is | {self.user_id}")
        logger.info(f"{BOT_NICK} is alive")
        logger.info(
            "Registered platform-neutral commands: "
            + ", ".join(self.command_router.registered_commands)
        )
        if self.live_notification_task is None or self.live_notification_task.done():
            self.live_notification_task = asyncio.create_task(
                self.live_notifier.run_forever()
            )

    async def event_message(self, message):
        if getattr(message, "echo", False):
            return
        if await self.command_transport.dispatch(message):
            return
        await self.handle_commands(message)

    @commands.command()
    async def hello(self, ctx: commands.Context):
        """Twitch-only connectivity check."""
        await ctx.send(f"Hello {ctx.author.name}!")


def main():
    if not TWITCH_ENABLED:
        logger.info(
            "Twitch integration is disabled. Set twitch.enabled to true "
            "to start it."
        )
        return 0
    missing = validate_twitch_config()
    if missing:
        logger.error(
            "Twitch integration cannot start. Missing configuration: "
            + ", ".join(missing)
        )
        return 2
    bot = Bot()
    bot.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
