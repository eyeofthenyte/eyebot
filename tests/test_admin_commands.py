import ast
import asyncio
import io
import types
import unittest
from pathlib import Path


ADMIN_PATH = Path(__file__).resolve().parents[1] / "src/cogs/admin.py"
TREE = ast.parse(ADMIN_PATH.read_text(encoding="utf-8"))
ADMIN_CLASS = next(
    node
    for node in TREE.body
    if isinstance(node, ast.ClassDef) and node.name == "Admin"
)
METHODS = [
    node
    for node in ADMIN_CLASS.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name in {
        "servers",
        "restart_platform",
        "set_prefix",
        "on_message_edit",
        "_message_edit_previews",
    }
]
for method in METHODS:
    method.decorator_list = []
TEST_CLASS = ast.ClassDef(
    name="TestAdmin",
    bases=[],
    keywords=[],
    body=METHODS,
    decorator_list=[],
)
MODULE = ast.Module(body=[TEST_CLASS], type_ignores=[])
ast.fix_missing_locations(MODULE)


class Forbidden(Exception):
    pass


class Embed:
    def __init__(self, *, title=None, description=None, **kwargs):
        self.title = title
        self.description = description
        self.timestamp = kwargs.get("timestamp")
        self.fields = []
        self.footer = None

    def add_field(self, *, name, value, inline=True):
        self.fields.append(
            types.SimpleNamespace(name=name, value=value, inline=inline)
        )

    def set_footer(self, *, text):
        self.footer = text


class File:
    def __init__(self, fp, *, filename):
        self.fp = fp
        self.filename = filename


namespace = {
    "asyncio": asyncio,
    "io": io,
    "discord": types.SimpleNamespace(
        Forbidden=Forbidden,
        Embed=Embed,
        File=File,
    ),
    "send_restart_command": lambda platform: f"{platform} restarted",
}
exec(compile(MODULE, str(ADMIN_PATH), "exec"), namespace)
Admin = namespace["TestAdmin"]


class Recorder:
    def __init__(self, *, fail=False):
        self.messages = []
        self.fail = fail

    async def send(self, message):
        if self.fail:
            raise Forbidden()
        self.messages.append(message)


class Logger:
    def __init__(self):
        self.messages = []

    def info(self, message, **kwargs):
        self.messages.append(message)

    def error(self, message, **kwargs):
        self.messages.append(message)


class AdminServerCommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_servers_uses_injected_bot_and_sends_one_dm(self):
        class PlatformStatusService:
            def effective_guild_platform(self, guild_id, platform_name):
                return {
                    "enabled": platform_name == "discord"
                    or (platform_name == "twitch" and guild_id == 1)
                }

        admin = Admin()
        admin.bot = types.SimpleNamespace(
            guilds=(
                types.SimpleNamespace(id=1, name="First"),
                types.SimpleNamespace(id=2, name="Second"),
            ),
            platform_config_service=PlatformStatusService(),
        )
        admin.config = {}
        admin.logger = Logger()
        author = Recorder()
        channel = Recorder()
        context = types.SimpleNamespace(author=author, send=channel.send)

        await admin.servers(context)

        self.assertEqual(len(author.messages), 1)
        self.assertIn("First (id: 1)", author.messages[0])
        self.assertIn("Second (id: 2)", author.messages[0])
        self.assertIn("discord: enabled", author.messages[0])
        self.assertIn("twitch: enabled", author.messages[0])
        self.assertIn("youtube: disabled", author.messages[0])
        self.assertEqual(
            channel.messages,
            ["✅ I sent the connected server list by direct message."],
        )

    async def test_servers_reports_blocked_direct_messages(self):
        admin = Admin()
        admin.bot = types.SimpleNamespace(
            guilds=(types.SimpleNamespace(id=1, name="First"),)
        )
        admin.logger = Logger()
        author = Recorder(fail=True)
        channel = Recorder()
        context = types.SimpleNamespace(author=author, send=channel.send)

        await admin.servers(context)

        self.assertIn("enable direct messages", channel.messages[0])

    async def test_servers_handles_no_connected_guilds(self):
        admin = Admin()
        admin.bot = types.SimpleNamespace(guilds=())
        admin.logger = Logger()
        author = Recorder()
        context = types.SimpleNamespace(author=author)

        await admin.servers(context)

        self.assertEqual(
            author.messages,
            ["EyeBot is not currently connected to any servers."],
        )


class PlatformService:
    def __init__(self):
        self.guild = {}
        self.saved = 0

    def ensure_discord_guild(self, guild_id, guild_name, default_prefix):
        self.guild.setdefault("prefix", default_prefix)
        return self.guild

    def save_discord_guild(self, _guild_id):
        self.saved += 1


class AdminPrefixCommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_sets_and_resets_server_prefix(self):
        service = PlatformService()
        admin = Admin()
        admin.config = {"prefix": "!"}
        admin.bot = types.SimpleNamespace(platform_config_service=service)
        channel = Recorder()
        context = types.SimpleNamespace(
            guild=types.SimpleNamespace(id=42, name="Campaign"),
            send=channel.send,
        )

        await admin.set_prefix(context, "?")
        self.assertEqual(service.guild["prefix"], "?")
        await admin.set_prefix(context, "reset")
        self.assertEqual(service.guild["prefix"], "!")
        self.assertEqual(service.saved, 2)

    async def test_rejects_invalid_server_prefix(self):
        service = PlatformService()
        admin = Admin()
        admin.config = {"prefix": "!"}
        admin.bot = types.SimpleNamespace(platform_config_service=service)
        channel = Recorder()
        context = types.SimpleNamespace(
            guild=types.SimpleNamespace(id=42, name="Campaign"),
            send=channel.send,
        )

        await admin.set_prefix(context, "toolong")
        self.assertEqual(service.saved, 0)
        self.assertIn("1–5", channel.messages[0])


class AdminRestartCommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_owner_can_request_non_discord_restart(self):
        admin = Admin()
        admin.logger = Logger()
        channel = Recorder()
        context = types.SimpleNamespace(send=channel.send)

        await admin.restart_platform(context, "TWITCH")

        self.assertEqual(channel.messages, ["✅ twitch restarted."])

    async def test_discord_acknowledges_before_restarting_itself(self):
        admin = Admin()
        admin.logger = Logger()
        channel = Recorder()
        context = types.SimpleNamespace(send=channel.send)

        await admin.restart_platform(context, "discord")

        self.assertEqual(
            channel.messages,
            ["♻️ Restarting the Discord bot..."],
        )

    async def test_restart_failure_is_reported(self):
        admin = Admin()
        admin.logger = Logger()
        channel = Recorder()
        context = types.SimpleNamespace(send=channel.send)
        original = admin.restart_platform.__globals__["send_restart_command"]

        def fail(_platform):
            raise RuntimeError("twitch is not enabled or running")

        admin.restart_platform.__globals__["send_restart_command"] = fail
        try:
            await admin.restart_platform(context, "twitch")
        finally:
            admin.restart_platform.__globals__["send_restart_command"] = original

        self.assertIn("not enabled or running", channel.messages[0])


class MessageEditHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_user_content_edit_is_sent_to_mod_channel(self):
        class ModHandler:
            def __init__(self):
                self.calls = []
                self.destination = object()

            def configured_channel(self, _guild):
                return self.destination

            @staticmethod
            def sanitize_text(_guild, value):
                return value

            @staticmethod
            def username(user):
                return user.name

            async def send(self, guild, **kwargs):
                self.calls.append((guild, kwargs))

        guild = types.SimpleNamespace(id=42)
        author = types.SimpleNamespace(name="alice", bot=False)
        channel = types.SimpleNamespace(name="general")
        before = types.SimpleNamespace(content="Original", guild=guild)
        after = types.SimpleNamespace(
            id=100,
            content="Revised",
            guild=guild,
            author=author,
            channel=channel,
            jump_url="https://discord.com/channels/42/99/100",
            edited_at=None,
        )
        admin = Admin()
        admin.mod_channel_handler = ModHandler()
        admin.logger = Logger()

        await admin.on_message_edit(before, after)

        self.assertEqual(len(admin.mod_channel_handler.calls), 1)
        _, kwargs = admin.mod_channel_handler.calls[0]
        self.assertIs(kwargs["channel"], admin.mod_channel_handler.destination)
        self.assertEqual(kwargs["embeds"][0].description, "Original")
        self.assertEqual(kwargs["embeds"][1].description, "Revised")
        self.assertEqual(kwargs["embeds"][0].fields[0].value, "alice")
        self.assertEqual(kwargs["files"], [])

    async def test_long_edit_attaches_complete_versions_and_uses_previews(self):
        class ModHandler:
            def __init__(self):
                self.calls = []
                self.destination = object()

            def configured_channel(self, _guild):
                return self.destination

            @staticmethod
            def sanitize_text(_guild, value):
                return value

            @staticmethod
            def username(user):
                return user.name

            async def send(self, guild, **kwargs):
                self.calls.append((guild, kwargs))

        prefix = "a" * 4500
        original_text = prefix + " OLD " + ("z" * 700)
        revised_text = prefix + " NEW " + ("z" * 700)
        guild = types.SimpleNamespace(id=42)
        before = types.SimpleNamespace(content=original_text, guild=guild)
        after = types.SimpleNamespace(
            id=101,
            content=revised_text,
            guild=guild,
            author=types.SimpleNamespace(name="alice", bot=False),
            channel=types.SimpleNamespace(name="general"),
            jump_url=None,
            edited_at=None,
        )
        admin = Admin()
        admin.mod_channel_handler = ModHandler()
        admin.logger = Logger()

        await admin.on_message_edit(before, after)

        _, kwargs = admin.mod_channel_handler.calls[0]
        self.assertLessEqual(len(kwargs["embeds"][0].description), 4096)
        self.assertTrue(kwargs["embeds"][0].description.startswith("…"))
        self.assertTrue(kwargs["embeds"][0].description.endswith("…"))
        self.assertEqual(
            [selected.filename for selected in kwargs["files"]],
            [
                "message-101-original.txt",
                "message-101-revised.txt",
            ],
        )
        self.assertEqual(
            kwargs["files"][0].fp.getvalue().decode("utf-8"),
            original_text,
        )
        self.assertEqual(
            kwargs["files"][1].fp.getvalue().decode("utf-8"),
            revised_text,
        )

    async def test_bot_and_no_content_change_are_ignored(self):
        handler = types.SimpleNamespace(
            configured_channel=lambda _guild: object()
        )
        admin = Admin()
        admin.mod_channel_handler = handler
        admin.logger = Logger()
        guild = types.SimpleNamespace(id=42)
        channel = types.SimpleNamespace(name="general")

        for author, before_content, after_content in (
            (types.SimpleNamespace(name="bot", bot=True), "a", "b"),
            (types.SimpleNamespace(name="alice", bot=False), "same", "same"),
        ):
            before = types.SimpleNamespace(content=before_content, guild=guild)
            after = types.SimpleNamespace(
                content=after_content,
                guild=guild,
                author=author,
                channel=channel,
            )
            await admin.on_message_edit(before, after)
