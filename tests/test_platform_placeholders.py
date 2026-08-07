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
import eyebot_bluesky
import eyebot_facebook
import eyebot_instagram
import eyebot_kick
import eyebot_kofi
import eyebot_substack
import eyebot_tiktok
import eyebot_twitter
import eyebot_youtube


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PlatformPlaceholderTests(unittest.TestCase):
    def test_every_requested_platform_has_a_disabled_placeholder(self):
        placeholders = (
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
        self.assertEqual(len(placeholders), 9)
        self.assertTrue(all(not item.implemented for item in placeholders))

    def test_placeholders_fail_explicitly_if_used(self):
        with self.assertRaisesRegex(NotImplementedError, "youtube"):
            YOUTUBE_ADAPTER.require_implementation()

    def test_placeholder_bot_entrypoints_fail_explicitly(self):
        entrypoints = (
            eyebot_youtube,
            eyebot_facebook,
            eyebot_kick,
            eyebot_twitter,
            eyebot_bluesky,
            eyebot_tiktok,
            eyebot_instagram,
            eyebot_substack,
            eyebot_kofi,
        )
        for entrypoint in entrypoints:
            with self.subTest(entrypoint=entrypoint.__name__):
                with self.assertRaises(NotImplementedError):
                    entrypoint.main()

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
