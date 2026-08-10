import ast
import unittest
from pathlib import Path

from core.social_reactions import enabled_reaction_emojis


class _PlatformService:
    def __init__(self, settings):
        self.settings = settings

    def effective_guild_platform(self, guild_id, platform):
        return self.settings.get(platform, {})


class SocialReactionConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path("src/cogs/social.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        assignments = {
            node.targets[0].id: ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in {"REACTION_PLATFORMS", "CANCEL_REACTION"}
        }
        cls.platforms = assignments["REACTION_PLATFORMS"]
        cls.cancel = assignments["CANCEL_REACTION"]
        cls.source = source

    def test_reaction_destinations_include_supported_platforms(self):
        self.assertEqual(
            set(self.platforms.values()),
            {"twitter", "facebook", "bluesky", "instagram", "tiktok", "all"},
        )

    def test_kofi_is_not_a_reaction_destination(self):
        self.assertNotIn("kofi", self.platforms.values())

    def test_cancel_reaction_is_separate_from_destinations(self):
        self.assertEqual(self.cancel, "❌")
        self.assertNotIn(self.cancel, self.platforms)

    def test_social_help_explains_every_reaction(self):
        for label in (
            "🐦 **Twitter/X**",
            "🦋 **Bluesky**",
            "📘 **Facebook**",
            "📸 **Instagram**",
            "🎵 **TikTok**",
            "📣 **All compatible**",
            "❌ **Cancel**",
            "✅ **Success**",
            "⚠️ **Failed**",
        ):
            self.assertIn(label, self.source)

    def test_each_social_command_includes_reaction_help(self):
        tree = ast.parse(self.source)
        commands_with_help = set()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                if any(
                    isinstance(keyword.value, ast.List)
                    and "SOCIAL_REACTION_HELP" in ast.unparse(keyword.value)
                    for keyword in decorator.keywords
                    if keyword.arg == "extras"
                ):
                    commands_with_help.add(node.name)
        self.assertEqual(
            commands_with_help,
            {"social_post", "social_media", "social_url"},
        )

    def test_social_help_lists_public_media_provider_placeholders(self):
        for provider in (
            "local_caddy",
            "cloudflare_r2",
            "amazon_s3",
            "azure_blob",
            "google_cloud_storage",
        ):
            self.assertIn(provider, self.source)

    def test_each_social_command_includes_provider_help(self):
        tree = ast.parse(self.source)
        commands_with_provider_help = set()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if any(
                "PUBLIC_MEDIA_PROVIDER_HELP" in ast.unparse(decorator)
                for decorator in node.decorator_list
            ):
                commands_with_provider_help.add(node.name)
        self.assertEqual(
            commands_with_provider_help,
            {"social_post", "social_media", "social_url"},
        )


class SocialReactionPlaceholderTests(unittest.TestCase):
    reactions = {
        "🐦": "twitter",
        "🦋": "bluesky",
        "📘": "facebook",
        "📸": "instagram",
        "🎵": "tiktok",
        "📣": "all",
    }

    def test_attachment_reactions_only_include_ready_compatible_accounts(self):
        service = _PlatformService(
            {
                "twitter": {"enabled": True, "connected": True, "posting_enabled": True},
                "facebook": {"enabled": True, "connected": True, "posting_enabled": True},
                "bluesky": {"enabled": True, "connected": False, "posting_enabled": True},
                "instagram": {"enabled": True, "connected": True, "posting_enabled": True},
            }
        )

        self.assertEqual(
            enabled_reaction_emojis(
                service, "42", self.reactions, has_attachments=True
            ),
            ("🐦", "📘", "📣"),
        )

    def test_url_reactions_include_connected_instagram_and_tiktok(self):
        service = _PlatformService(
            {
                "instagram": {"enabled": True, "connected": True, "posting_enabled": True},
                "tiktok": {"enabled": True, "connected": True, "posting_enabled": True},
                "twitter": {"enabled": True, "connected": True, "posting_enabled": True},
            }
        )

        self.assertEqual(
            enabled_reaction_emojis(
                service, "42", self.reactions, has_media_url=True
            ),
            ("📸", "🎵"),
        )

    def test_hosting_adds_instagram_and_tiktok_attachment_placeholders(self):
        service = _PlatformService(
            {
                "instagram": {"enabled": True, "connected": True, "posting_enabled": True},
                "tiktok": {"enabled": True, "connected": True, "posting_enabled": True},
            }
        )

        self.assertEqual(
            enabled_reaction_emojis(
                service,
                "42",
                self.reactions,
                has_attachments=True,
                attachments_can_be_hosted=True,
                attachment_content_types=("image/jpeg",),
            ),
            ("📸", "🎵", "📣"),
        )

    def test_disabled_or_non_posting_accounts_have_no_placeholder(self):
        service = _PlatformService(
            {
                "twitter": {"enabled": False, "connected": True, "posting_enabled": True},
                "facebook": {"enabled": True, "connected": True, "posting_enabled": False},
            }
        )

        self.assertEqual(
            enabled_reaction_emojis(
                service, "42", self.reactions, has_attachments=True
            ),
            (),
        )


if __name__ == "__main__":
    unittest.main()
