import ast
import asyncio
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
    if isinstance(node, ast.AsyncFunctionDef)
    and node.name in {"servers", "restart_platform", "set_prefix"}
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


namespace = {
    "asyncio": asyncio,
    "discord": types.SimpleNamespace(Forbidden=Forbidden),
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

    def info(self, message):
        self.messages.append(message)

    def error(self, message):
        self.messages.append(message)


class AdminServerCommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_servers_uses_injected_bot_and_sends_one_dm(self):
        admin = Admin()
        admin.bot = types.SimpleNamespace(
            guilds=(
                types.SimpleNamespace(id=1, name="First"),
                types.SimpleNamespace(id=2, name="Second"),
            )
        )
        admin.logger = Logger()
        author = Recorder()
        channel = Recorder()
        context = types.SimpleNamespace(author=author, send=channel.send)

        await admin.servers(context)

        self.assertEqual(len(author.messages), 1)
        self.assertIn("First (id: 1)", author.messages[0])
        self.assertIn("Second (id: 2)", author.messages[0])
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
