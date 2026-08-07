import unittest
from types import SimpleNamespace

from adapters.discord_adapter import (
    DiscordTransportAdapter,
    request_from_discord_message,
)
from core.command_model import CommandPlatform, CommandSurface
from core.command_model import CommandResponse
from core.command_router import CommandRouter


class FakeAuthor:
    id = 7
    display_name = "Test"
    roles = [SimpleNamespace(name="Player")]

    def __str__(self):
        return "test-user"


class DiscordRequestAdapterTests(unittest.TestCase):
    def test_guild_message_maps_to_neutral_request(self):
        message = SimpleNamespace(
            id=90,
            content='!roll "Test Attack" -dm',
            author=FakeAuthor(),
            channel=SimpleNamespace(id=8, name="dice"),
            guild=SimpleNamespace(id=9, name="Campaign"),
        )
        request = request_from_discord_message(message, prefix="!")
        self.assertEqual(request.platform, CommandPlatform.DISCORD)
        self.assertEqual(request.surface, CommandSurface.CHANNEL)
        self.assertEqual(request.command, "roll")
        self.assertEqual(request.arguments, ("Test Attack", "-dm"))
        self.assertEqual(request.location.community_id, "9")


class DiscordTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_dispatches_through_shared_router(self):
        router = CommandRouter()

        @router.command("ping")
        async def ping(_request):
            return CommandResponse.text("pong")

        destination = SimpleNamespace(id=8, name="dice", sent=[])

        async def send(content=None, **_kwargs):
            destination.sent.append(content)

        destination.send = send
        author = FakeAuthor()
        author.bot = False
        message = SimpleNamespace(
            id=91,
            content="!ping",
            author=author,
            channel=destination,
            guild=None,
        )
        adapter = DiscordTransportAdapter(router)
        self.assertTrue(await adapter.dispatch(message))
        self.assertEqual(destination.sent, ["pong"])

    async def test_uses_per_guild_prefix_resolver(self):
        router = CommandRouter()

        @router.command("ping")
        async def ping(_request):
            return CommandResponse.text("pong")

        destination = SimpleNamespace(id=8, name="dice", sent=[])

        async def send(content=None, **_kwargs):
            destination.sent.append(content)

        destination.send = send
        author = FakeAuthor()
        author.bot = False
        message = SimpleNamespace(
            id=92,
            content="?ping",
            author=author,
            channel=destination,
            guild=SimpleNamespace(id=9, name="Campaign"),
        )
        adapter = DiscordTransportAdapter(
            router,
            prefix="!",
            prefix_resolver=lambda _message: "?",
        )

        self.assertTrue(await adapter.dispatch(message))
        self.assertEqual(destination.sent, ["pong"])
