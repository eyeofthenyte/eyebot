import unittest

from core.twitch_config import resolve_twitch_channels


class PlatformService:
    def __init__(self, guilds):
        self.guilds = guilds

    def discord_guilds(self):
        return self.guilds

    def effective_guild_platform(self, guild_id, platform_name):
        return self.guilds[guild_id].get("platforms", {}).get(platform_name, {})


class TwitchChannelResolutionTests(unittest.TestCase):
    def test_private_install_uses_only_global_channels(self):
        service = PlatformService(
            {"42": {"platforms": {"twitch": {"enabled": True, "channel": "guest"}}}}
        )
        config = {
            "private_install": True,
            "twitch": {"channels": ["Owner"]},
        }
        self.assertEqual(resolve_twitch_channels(config, service), ("owner",))

    def test_shared_install_adds_enabled_guild_channels(self):
        service = PlatformService(
            {
                "42": {"platforms": {"twitch": {"enabled": True, "channel": "Guest"}}},
                "84": {"platforms": {"twitch": {"enabled": False, "channel": "ignored"}}},
                "99": {"platforms": {"twitch": {"enabled": True, "channel": "#OWNER"}}},
            }
        )
        config = {
            "private_install": False,
            "twitch": {"channels": ["Owner"]},
        }
        self.assertEqual(resolve_twitch_channels(config, service), ("owner", "guest"))

    def test_shared_install_adds_multiple_guild_channels_without_duplicates(self):
        service = PlatformService(
            {
                "42": {
                    "platforms": {
                        "twitch": {
                            "enabled": True,
                            "channels": [
                                {"channel": "First", "destination_channel": "123"},
                                {"channel": "#SECOND"},
                                "first",
                            ],
                        }
                    }
                }
            }
        )
        config = {"private_install": False, "twitch": {"channels": ["Owner"]}}
        self.assertEqual(
            resolve_twitch_channels(config, service),
            ("owner", "first", "second"),
        )

    def test_missing_mode_fails_closed_as_private(self):
        service = PlatformService(
            {"42": {"platforms": {"twitch": {"enabled": True, "channel": "guest"}}}}
        )
        self.assertEqual(resolve_twitch_channels({"twitch": {}}, service), ())


if __name__ == "__main__":
    unittest.main()
