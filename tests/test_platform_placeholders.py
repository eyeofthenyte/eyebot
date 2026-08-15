import unittest
from pathlib import Path

import yaml

from adapters.bluesky_adapter import BLUESKY_ADAPTER
from adapters.facebook_adapter import FACEBOOK_ADAPTER
from adapters.instagram_adapter import INSTAGRAM_ADAPTER
from adapters.kick_adapter import KICK_ADAPTER
from adapters.kofi_adapter import KOFI_ADAPTER
from adapters.substack_adapter import SUBSTACK_ADAPTER
from adapters.tiktok_adapter import TIKTOK_ADAPTER
from adapters.twitter_adapter import TWITTER_ADAPTER
from adapters.youtube_adapter import YOUTUBE_ADAPTER
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PlatformConnectorTests(unittest.TestCase):
    def test_every_requested_platform_has_an_implemented_adapter_contract(self):
        adapters = (
            YOUTUBE_ADAPTER,
            FACEBOOK_ADAPTER,
            KICK_ADAPTER,
            TWITTER_ADAPTER,
            BLUESKY_ADAPTER,
            TIKTOK_ADAPTER,
            INSTAGRAM_ADAPTER,
            SUBSTACK_ADAPTER,
            KOFI_ADAPTER,
        )
        self.assertEqual(len(adapters), 9)
        self.assertTrue(all(item.implemented for item in adapters))
        self.assertTrue(all(item.capabilities for item in adapters))

    def test_kick_chat_is_exposed_through_verified_webhooks(self):
        self.assertIn("livestream_chat", KICK_ADAPTER.capabilities)

    def test_distribution_config_contains_disabled_blank_sections(self):
        with (PROJECT_ROOT / "platforms.yaml.dist").open(encoding="utf-8") as file:
            config = yaml.safe_load(file)

        for platform in (
            "youtube",
            "facebook",
            "kick",
            "twitter",
            "bluesky",
            "tiktok",
            "instagram",
            "substack",
            "kofi",
        ):
            with self.subTest(platform=platform):
                self.assertIn(platform, config)
                self.assertFalse(config[platform]["enabled"])

        self.assertIsNone(config["youtube"]["api_key"])
        self.assertIsNone(config["facebook"]["access_token"])
        self.assertIsNone(config["kick"]["access_token"])
        self.assertIsNone(config["twitter"]["bearer_token"])
        self.assertIsNone(config["bluesky"]["app_password"])
        self.assertIsNone(config["tiktok"]["access_token"])
        self.assertIsNone(config["instagram"]["access_token"])
        self.assertIsNone(config["substack"]["credential"])
        self.assertIsNone(config["kofi"]["verification_token"])
        self.assertFalse(config["twitch"]["enabled"])

        for platform in (
            "twitch",
            "youtube",
            "facebook",
            "kick",
            "twitter",
            "tiktok",
            "instagram",
        ):
            with self.subTest(live_destination=platform):
                self.assertIn("destination_channel", config[platform])
