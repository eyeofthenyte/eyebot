import ast
import os
import tempfile
import types
import unittest
from pathlib import Path

import yaml

from services.platformConfigService import PlatformConfigService


PLATFORM_PATH = Path(__file__).resolve().parents[1] / "src/cogs/platform.py"
TREE = ast.parse(PLATFORM_PATH.read_text(encoding="utf-8"))
support_nodes = []
platform_class = None
for node in TREE.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        if isinstance(node, ast.Import) and any(alias.name == "discord" for alias in node.names):
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "discord.ext":
            continue
        support_nodes.append(node)
    elif isinstance(node, ast.ClassDef) and node.name == "Platform":
        methods = []
        for method in node.body:
            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and method.name in {
                "__init__",
                "platform_command",
                "_service",
                "_delete_invocation",
                "_can_manage",
                "_resolve_target",
                "_require_mod_channel",
                "_send_setup_instructions",
                "_ensure_socialmedia_source_channel",
            }:
                method.decorator_list = []
                methods.append(method)
        platform_class = ast.ClassDef(
            name="Platform",
            bases=[],
            keywords=[],
            body=methods,
            decorator_list=[],
        )
    elif isinstance(node, ast.ClassDef):
        support_nodes.append(node)
    elif not isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef)):
        support_nodes.append(node)

MODULE = ast.Module(body=[*support_nodes, platform_class], type_ignores=[])
ast.fix_missing_locations(MODULE)
class DiscordError(Exception):
    pass


namespace = {
    "discord": types.SimpleNamespace(
        Forbidden=DiscordError,
        NotFound=DiscordError,
        HTTPException=DiscordError,
    )
}
exec(compile(MODULE, str(PLATFORM_PATH), "exec"), namespace)

Platform = namespace["Platform"]
PlatformValueError = namespace["PlatformValueError"]
PLATFORM_RULES = namespace["PLATFORM_RULES"]
validate_parameter_value = namespace["validate_parameter_value"]


class Guild:
    def __init__(self, guild_id=42, name="Campaign", manager_id=7):
        self.id = guild_id
        self.name = name
        self.manager_id = manager_id

    def get_member(self, user_id):
        if user_id != self.manager_id:
            return None
        return types.SimpleNamespace(
            guild_permissions=types.SimpleNamespace(manage_guild=True)
        )

    def get_channel(self, channel_id):
        return getattr(self, "channels", {}).get(channel_id)


class Recorder:
    def __init__(self, guild=None, *, channel_id=999):
        self.guild = guild
        self.author = RecorderDestination(id=7)
        self.channel = types.SimpleNamespace(id=channel_id)
        self.messages = []
        self.deleted = 0
        self.message = types.SimpleNamespace(delete=self.delete)

    async def delete(self):
        self.deleted += 1

    async def send(self, message):
        self.messages.append(message)


class RecorderDestination:
    def __init__(self, *, id=None):
        self.id = id
        self.messages = []

    async def send(self, message):
        self.messages.append(message)


class PlatformValueValidationTests(unittest.TestCase):
    def test_boolean_values_are_normalized(self):
        rule = PLATFORM_RULES["youtube"]["videos_enabled"]
        self.assertTrue(validate_parameter_value(rule, "ON"))
        self.assertFalse(validate_parameter_value(rule, "no"))

    def test_youtube_channel_id_requires_uc_format(self):
        rule = PLATFORM_RULES["youtube"]["channel_id"]
        valid = "UC" + "a" * 22
        self.assertEqual(validate_parameter_value(rule, valid), valid)
        with self.assertRaises(PlatformValueError):
            validate_parameter_value(rule, "not-a-channel")

    def test_twitch_channel_is_normalized_and_validated(self):
        rule = PLATFORM_RULES["twitch"]["channel"]
        self.assertEqual(validate_parameter_value(rule, "EyeBot_Channel"), "eyebot_channel")
        with self.assertRaises(PlatformValueError):
            validate_parameter_value(rule, "invalid channel name")

    def test_twitch_destination_requires_discord_channel(self):
        rule = PLATFORM_RULES["twitch"]["destination_channel"]
        self.assertEqual(
            validate_parameter_value(rule, "<#123456789012345678>"),
            "123456789012345678",
        )
        with self.assertRaises(PlatformValueError):
            validate_parameter_value(rule, "#stream-alerts")

    def test_discord_channel_mentions_are_normalized_to_ids(self):
        rule = PLATFORM_RULES["youtube"]["destination_channel"]
        self.assertEqual(
            validate_parameter_value(rule, "<#123456789012345678>"),
            "123456789012345678",
        )
        with self.assertRaises(PlatformValueError):
            validate_parameter_value(rule, "#announcements")

    def test_kofi_url_rejects_other_hosts_and_credentials(self):
        rule = PLATFORM_RULES["kofi"]["page_url"]
        self.assertEqual(
            validate_parameter_value(rule, "https://ko-fi.com/eyebot"),
            "https://ko-fi.com/eyebot",
        )
        with self.assertRaises(PlatformValueError):
            validate_parameter_value(rule, "https://example.com/eyebot")
        with self.assertRaises(PlatformValueError):
            validate_parameter_value(rule, "https://user:pass@ko-fi.com/eyebot")


class PlatformCommandTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.platform_path = root / "platforms.yaml"
        self.platform_path.write_text(
            yaml.safe_dump(
                {
                    "youtube": {
                        "videos_enabled": False,
                        "api_key": "platform-secret",
                    },
                    "kofi": {"page_url": "https://ko-fi.com/default"},
                }
            ),
            encoding="utf-8",
        )
        self.service = PlatformConfigService(str(self.platform_path))
        self.guild = Guild()
        guild_config = self.service.ensure_discord_guild("42", "Campaign")
        guild_config["mod_channel"] = 999
        self.service.save_discord_guild("42")
        self.bot = types.SimpleNamespace(
            platform_config_service=self.service,
            guilds=(self.guild,),
            config={},
        )
        self.cog = Platform(self.bot)
        self.context = Recorder(self.guild)

    def tearDown(self):
        self.temp.cleanup()

    async def test_set_writes_only_the_selected_guild_override(self):
        await self.cog.platform_command(
            self.context,
            "youtube",
            "set",
            "videos_enabled",
            value="true",
        )

        effective = self.service.effective_guild_platform(42, "youtube")
        self.assertTrue(effective["videos_enabled"])
        self.assertEqual(effective["api_key"], "platform-secret")
        saved = yaml.safe_load(
            (Path(self.temp.name) / "data/guilds/42.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(saved["platforms"]["youtube"]["videos_enabled"])
        self.assertNotIn("api_key", saved["platforms"]["youtube"])
        self.assertEqual(self.context.deleted, 1)

    async def test_twitch_go_live_destination_is_saved_per_guild(self):
        await self.cog.platform_command(
            self.context,
            "twitch",
            "set",
            "destination_channel",
            value="<#123456789012345678>",
        )

        effective = self.service.effective_guild_platform(42, "twitch")
        self.assertEqual(effective["destination_channel"], "123456789012345678")
        saved = yaml.safe_load(
            (Path(self.temp.name) / "data/guilds/42.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            saved["platforms"]["twitch"]["destination_channel"],
            "123456789012345678",
        )

    async def test_enable_and_disable_change_only_service_state(self):
        self.service.set_guild_platform_override(
            42,
            "youtube",
            "videos_enabled",
            True,
        )

        await self.cog.platform_command(self.context, "youtube", "disable")
        overrides = self.service.discord_guilds()["42"]["platforms"]["youtube"]
        self.assertFalse(overrides["enabled"])
        self.assertTrue(overrides["videos_enabled"])

        await self.cog.platform_command(self.context, "youtube", "enable")
        overrides = self.service.discord_guilds()["42"]["platforms"]["youtube"]
        self.assertTrue(overrides["enabled"])
        self.assertTrue(overrides["videos_enabled"])
        self.assertEqual(self.context.deleted, 2)

    async def test_enabling_social_platform_prompts_for_source_channel(self):
        async def wait_for(event, timeout, check):
            message = types.SimpleNamespace(
                author=self.context.author,
                channel=self.context.channel,
                content="3",
                delete=self.context.delete,
            )
            self.assertTrue(check(message))
            return message

        self.bot.wait_for = wait_for
        await self.cog.platform_command(self.context, "twitter", "enable")

        output = "\n".join(self.context.messages)
        self.assertIn("social-media source channel", output)
        self.assertIn("Image posting remains unavailable", output)

    async def test_connect_sends_signed_link_only_to_manager_dm(self):
        self.bot.config = {
            "gateway": {
                "enabled": True,
                "public_base_url": "https://bot.example.com",
            }
        }
        previous = os.environ.get("EYEBOT_OAUTH_STATE_KEY")
        os.environ["EYEBOT_OAUTH_STATE_KEY"] = "x" * 32
        try:
            await self.cog.platform_command(self.context, "youtube", "connect")
        finally:
            if previous is None:
                os.environ.pop("EYEBOT_OAUTH_STATE_KEY", None)
            else:
                os.environ["EYEBOT_OAUTH_STATE_KEY"] = previous

        self.assertIn("/oauth/youtube/start?request=", self.context.author.messages[0])
        self.assertNotIn("/oauth/youtube/start?request=", "\n".join(self.context.messages))
        self.assertIn("sent to your DM", self.context.messages[-1])

    async def test_enable_rejects_extra_parameters_without_changing_state(self):
        await self.cog.platform_command(
            self.context,
            "youtube",
            "enable",
            "videos_enabled",
        )

        self.assertIn("does not accept", self.context.messages[-1])
        self.assertNotIn("platforms", self.service.discord_guilds()["42"])

    async def test_default_removes_override_and_restores_inheritance(self):
        self.service.set_guild_platform_override(
            42,
            "youtube",
            "videos_enabled",
            True,
        )

        await self.cog.platform_command(
            self.context,
            "youtube",
            "default",
            "videos_enabled",
        )

        effective = self.service.effective_guild_platform(42, "youtube")
        self.assertFalse(effective["videos_enabled"])
        self.assertNotIn(
            "platforms",
            self.service.discord_guilds()["42"],
        )

    async def test_credentials_are_rejected(self):
        await self.cog.platform_command(
            self.context,
            "youtube",
            "set",
            "api_key",
            value="do-not-store",
        )

        self.assertIn("cannot be entered through Discord", self.context.messages[-1])
        self.assertNotIn("do-not-store", str(self.service.discord_guilds()))

    async def test_invalid_value_is_not_persisted(self):
        await self.cog.platform_command(
            self.context,
            "kofi",
            "set",
            "page_url",
            value="http://example.com/not-kofi",
        )

        self.assertIn("Invalid", self.context.messages[-1])
        guild = self.service.discord_guilds()["42"]
        self.assertNotIn("platforms", guild)

    async def test_server_command_is_rejected_outside_mod_channel(self):
        context = Recorder(self.guild, channel_id=123)

        await self.cog.platform_command(context, "youtube", "enable")

        self.assertIn("can only be changed", context.messages[-1])
        self.assertEqual(context.deleted, 1)
        self.assertNotIn("platforms", self.service.discord_guilds()["42"])

    async def test_missing_mod_channel_prompts_for_setup_or_dm(self):
        self.service.discord_guilds()["42"]["mod_channel"] = "UNSET"
        context = Recorder(self.guild)

        await self.cog.platform_command(context, "youtube", "enable")

        self.assertIn("setmodchannel", context.messages[-1])
        self.assertIn("direct message", context.messages[-1])

    async def test_dm_uses_only_managed_shared_guild(self):
        context = Recorder(None)

        await self.cog.platform_command(context, "youtube", "disable")

        overrides = self.service.discord_guilds()["42"]["platforms"]["youtube"]
        self.assertFalse(overrides["enabled"])
        self.assertEqual(context.deleted, 0)

    async def test_dm_requires_guild_id_when_multiple_are_managed(self):
        second = Guild(84, "Second Campaign")
        self.bot.guilds = (self.guild, second)
        context = Recorder(None)

        await self.cog.platform_command(context, "youtube", "enable")

        self.assertIn("Select a server by ID", context.messages[-1])
        self.assertNotIn("platforms", self.service.discord_guilds()["42"])

    async def test_dm_guild_id_targets_selected_server(self):
        second = Guild(84, "Second Campaign")
        self.bot.guilds = (self.guild, second)
        context = Recorder(None)

        await self.cog.platform_command(
            context,
            "84",
            "youtube",
            "enable",
        )

        overrides = self.service.discord_guilds()["84"]["platforms"]["youtube"]
        self.assertTrue(overrides["enabled"])
        self.assertNotIn("platforms", self.service.discord_guilds()["42"])

    async def test_instructions_are_sent_to_configured_mod_channel(self):
        mod_channel = RecorderDestination(id=999)
        self.guild.channels = {999: mod_channel}

        await self.cog.platform_command(
            self.context,
            "twitch",
            "instructions",
        )

        output = "\n".join(mod_channel.messages)
        self.assertIn("# Twitch setup", output)
        self.assertIn("https://dev.twitch.tv/console/apps", output)
        self.assertIn("--guild 42", output)
        self.assertEqual(self.context.deleted, 1)
        self.assertEqual(self.context.author.messages, [])

    async def test_instructions_fall_back_to_dm_without_mod_channel(self):
        self.service.discord_guilds()["42"]["mod_channel"] = "UNSET"

        await self.cog.platform_command(
            self.context,
            "youtube",
            "instructions",
        )

        output = "\n".join(self.context.author.messages)
        self.assertIn("# YouTube setup", output)
        self.assertIn("https://console.cloud.google.com/", output)
        self.assertIn("sent the platform setup instructions by DM", self.context.messages[-1])

    async def test_all_instructions_cover_every_platform(self):
        self.service.discord_guilds()["42"]["mod_channel"] = "UNSET"

        await self.cog.platform_command(
            self.context,
            "all",
            "instructions",
        )

        output = "\n".join(self.context.author.messages)
        expected_headings = (
            "# Discord setup",
            "# Twitch setup",
            "# YouTube setup",
            "# Facebook setup",
            "# Kick setup",
            "# Twitter/X setup",
            "# Bluesky setup",
            "# TikTok setup",
            "# Instagram setup",
            "# Substack setup",
            "# Ko-fi setup",
        )
        for heading in expected_headings:
            self.assertIn(heading, output)
        self.assertTrue(all(len(message) <= 1900 for message in self.context.author.messages))


if __name__ == "__main__":
    unittest.main()
