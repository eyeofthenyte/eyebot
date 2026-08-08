import tempfile
import unittest
from pathlib import Path

from services.liveNotificationService import LiveEvent, LiveNotificationService


class Logger:
    def info(self, message):
        pass

    def error(self, message):
        pass


class PlatformService:
    def __init__(self, root, settings):
        self.guild_config_dir = Path(root)
        self.settings = settings

    def discord_guilds(self):
        return {"42": {}}

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


if __name__ == "__main__":
    unittest.main()
