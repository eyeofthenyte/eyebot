import unittest
from types import SimpleNamespace

from core.cog_bridge import LegacyCogHandler, PortableCommandSpec
from core.command_model import (
    CommandActor,
    CommandLocation,
    CommandPlatform,
    CommandRequest,
    CommandSurface,
    ResponseVisibility,
)
from core.cog_registry import PORTABLE_COMMANDS, build_portable_router


class FakeLogger:
    def error(self, _message):
        pass


class FakeCommand:
    def __init__(self, callback):
        self.callback = callback


class FakeCog:
    def __init__(self):
        self.bot = SimpleNamespace(logger=FakeLogger())
        self.roll = FakeCommand(type(self)._roll)
        self.lookup = FakeCommand(type(self)._lookup)

    async def _roll(self, ctx, *, args=None):
        await ctx.send(f"rolled {args}")

    async def _lookup(self, ctx, *, select):
        await ctx.send(f"selected {select}")


def request(command, *arguments):
    return CommandRequest(
        platform=CommandPlatform.GENERIC,
        surface=CommandSurface.CHANNEL,
        actor=CommandActor(id="7", username="tester"),
        command=command,
        arguments=arguments,
        location=CommandLocation(
            channel_id="2",
            community_id="1",
            community_name="table",
        ),
    )


class CogBridgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_joined_arguments_are_passed_to_legacy_callback(self):
        spec = PortableCommandSpec(
            "Fake", "lookup", "lookup", (), "joined", "select"
        )
        response = await LegacyCogHandler(FakeCog(), spec)(
            request("lookup", "red", "dragon")
        )
        self.assertEqual(response.messages[0].content, "selected red dragon")

    async def test_roll_delivery_flag_is_not_part_of_expression(self):
        spec = PortableCommandSpec(
            "Fake", "roll", "roll", (), "optional_joined", "args", True
        )
        response = await LegacyCogHandler(FakeCog(), spec)(
            request("roll", "@Test", "Attack", "-dm")
        )
        self.assertEqual(response.messages[0].content, "rolled @Test Attack")
        self.assertEqual(response.visibility, ResponseVisibility.REQUESTER)

    async def test_blind_flag_produces_blind_visibility(self):
        spec = PortableCommandSpec(
            "Fake", "roll", "roll", (), "optional_joined", "args", True
        )
        response = await LegacyCogHandler(FakeCog(), spec)(
            request("roll", "1d20", "-blind")
        )
        self.assertEqual(response.visibility, ResponseVisibility.BLIND)

    async def test_missing_required_argument_returns_neutral_error(self):
        spec = PortableCommandSpec(
            "Fake", "lookup", "lookup", (), "joined", "select"
        )
        response = await LegacyCogHandler(FakeCog(), spec)(request("lookup"))
        self.assertEqual(response.error_code, "missing_argument")


class CogRegistryTests(unittest.TestCase):
    def test_registry_contains_only_portable_commands(self):
        commands = {spec.command for spec in PORTABLE_COMMANDS}
        self.assertIn("roll", commands)
        self.assertIn("loot", commands)
        self.assertNotIn("clear", commands)
        self.assertNotIn("set_dm", commands)
        self.assertNotIn("reload", commands)
        self.assertNotIn("privateroll", commands)

    def test_registry_can_skip_cogs_not_loaded_on_a_platform(self):
        router = build_portable_router({}, strict=False)
        self.assertEqual(router.registered_commands, ())

    def test_registry_reports_missing_portable_cogs_in_strict_mode(self):
        with self.assertRaisesRegex(RuntimeError, "Carousing"):
            build_portable_router({}, strict=True)
