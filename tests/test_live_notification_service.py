import tempfile
import sys
import types
import unittest
from pathlib import Path

if "aiohttp" not in sys.modules:
    try:
        import aiohttp  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["aiohttp"] = types.SimpleNamespace(
            BasicAuth=lambda *args, **kwargs: (args, kwargs)
        )

from services.liveNotificationService import LiveEvent, LiveNotificationService


class Logger:
    def info(self, message):
        pass

    def error(self, message):
        pass


class PlatformService:
    def __init__(self, root, settings, guild=None):
        self.guild_config_dir = Path(root)
        self.settings = settings
        self.guild = guild or {}

    def discord_guilds(self):
        return {"42": self.guild}

    def effective_guild_platform(self, guild_id, platform):
        return self.settings


class RecordingNotifier(LiveNotificationService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.posts = []

    async def _post_discord(self, session, channel_id, event):
        self.posts.append((channel_id, event.event_id))


class LiveNotificationTests(unittest.IsolatedAsyncioTestCase):
    async def test_posts_only_on_new_live_transition_and_resets_offline(self):
        with tempfile.TemporaryDirectory() as root:
            settings = {
                "enabled": True,
                "channel": "creator",
                "destination_channel": "123456789012345678",
            }
            service = PlatformService(root, settings)
            current = LiveEvent("stream-1", "Live", "https://example.com/live", "Creator")

            async def detector(config, session):
                return current

            notifier = RecordingNotifier(
                "twitch", {"twitch": {}}, service, detector, Logger()
            )
            await notifier.poll_once(object())
            await notifier.poll_once(object())
            self.assertEqual(notifier.posts, [("123456789012345678", "stream-1")])

            async def offline(config, session):
                return None

            notifier.detector = offline
            await notifier.poll_once(object())
            notifier.detector = detector
            await notifier.poll_once(object())
            self.assertEqual(len(notifier.posts), 2)

    async def test_disabled_or_missing_destination_is_not_polled(self):
        with tempfile.TemporaryDirectory() as root:
            calls = []

            async def detector(config, session):
                calls.append(config)
                return None

            service = PlatformService(root, {"enabled": False, "channel": "creator"})
            notifier = RecordingNotifier(
                "twitch", {"twitch": {}}, service, detector, Logger()
            )
            await notifier.poll_once(object())
            self.assertEqual(calls, [])

    async def test_twitch_polls_each_guild_channel(self):
        with tempfile.TemporaryDirectory() as root:
            seen = []

            async def detector(config, session):
                seen.append(config["channel"])
                return None

            settings = {
                "enabled": True,
                "destination_channel": "123456789012345678",
            }
            guild = {
                "platforms": {
                    "twitch": {
                        "channels": [
                            {
                                "channel": "First",
                                "destination_channel": "987654321098765432",
                            },
                            {"channel": "#second"},
                            "first",
                        ]
                    }
                }
            }
            service = PlatformService(root, settings, guild)
            notifier = RecordingNotifier(
                "twitch", {"twitch": {}}, service, detector, Logger()
            )

            await notifier.poll_once(object())

            self.assertEqual(seen, ["first", "second"])

    async def test_twitch_channel_destination_overrides_guild_default(self):
        with tempfile.TemporaryDirectory() as root:
            settings = {
                "enabled": True,
                "destination_channel": "123456789012345678",
            }
            guild = {
                "platforms": {
                    "twitch": {
                        "channels": [
                            {
                                "channel": "creator",
                                "destination_channel": "987654321098765432",
                            }
                        ]
                    }
                }
            }
            service = PlatformService(root, settings, guild)
            notifier = RecordingNotifier(
                "twitch", {"twitch": {}}, service, lambda *_: None, Logger()
            )

            targets = list(notifier._targets())

            self.assertEqual(targets[0][0], "42")
            self.assertEqual(targets[0][1], "987654321098765432")
            self.assertEqual(targets[0][2]["channel"], "creator")

    async def test_kick_channels_use_individual_or_default_destinations(self):
        with tempfile.TemporaryDirectory() as root:
            settings = {
                "enabled": True,
                "destination_channel": "123456789012345678",
            }
            guild = {
                "platforms": {
                    "kick": {
                        "channels": [
                            {
                                "channel": "first_creator",
                                "destination_channel": "987654321098765432",
                            },
                            {"channel": "second_creator"},
                        ]
                    }
                }
            }
            service = PlatformService(root, settings, guild)
            notifier = RecordingNotifier(
                "kick", {"kick": {}}, service, lambda *_: None, Logger()
            )

            targets = list(notifier._targets())

            self.assertEqual(
                [(destination, config["channel"]) for _, destination, config in targets],
                [
                    ("987654321098765432", "first_creator"),
                    ("123456789012345678", "second_creator"),
                ],
            )


if __name__ == "__main__":
    unittest.main()
