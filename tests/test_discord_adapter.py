import unittest
from types import SimpleNamespace

from adapters.discord_adapter import (
    DiscordTransportAdapter,
    request_from_discord_message,
    resolve_discord_roll_destinations,
    send_discord_response,
)
from core.command_model import CommandPlatform, CommandSurface, ResponseVisibility
from core.command_model import CommandResponse
from core.command_router import CommandRouter


class FakeAuthor:
    id = 7
    display_name = "Test"
    roles = [SimpleNamespace(name="Player")]
    guild_permissions = SimpleNamespace(manage_guild=True, administrator=False)

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
        self.assertTrue(request.actor.metadata["manage_guild"])


class DiscordTransportTests(unittest.IsolatedAsyncioTestCase):

    async def test_dm_roll_routes_to_private_and_gm_channels(self):
        private = SimpleNamespace(id=21)
        gm = SimpleNamespace(id=22)
        channels = {21: private, 22: gm}
        bot = SimpleNamespace(get_channel=channels.get)
        source = SimpleNamespace(
            author=SimpleNamespace(id=7), channel=SimpleNamespace(id=8)
        )
        response = CommandResponse.text(
            "roll", visibility=ResponseVisibility.REQUESTER
        )

        destinations = resolve_discord_roll_destinations(
            bot,
            source,
            response,
            {"dm_channel": "22", "user_channels": {"7": "21"}},
        )

        self.assertEqual(destinations, (private, gm))

    async def test_blind_roll_routes_only_to_gm_channel(self):
        gm = SimpleNamespace(id=22)
        bot = SimpleNamespace(get_channel=lambda channel_id: gm if channel_id == 22 else None)
        source = SimpleNamespace(
            author=SimpleNamespace(id=7), channel=SimpleNamespace(id=8)
        )
        response = CommandResponse.text(
            "roll", visibility=ResponseVisibility.BLIND
        )

        destinations = resolve_discord_roll_destinations(
            bot,
            source,
            response,
            {"dm_channel": "22", "user_channels": {"7": "21"}},
        )

        self.assertEqual(destinations, (gm,))

    async def test_missing_gm_channel_posts_public_setup_notice(self):
        channel = SimpleNamespace(sent=[])
        author = SimpleNamespace(id=7, sent=[])

        async def channel_send(content=None, **_kwargs):
            channel.sent.append(content)

        async def author_send(content=None, **_kwargs):
            author.sent.append(content)

        channel.send = channel_send
        author.send = author_send
        source = SimpleNamespace(
            author=author,
            channel=channel,
            guild=SimpleNamespace(id=9),
        )
        response = CommandResponse.text(
            "secret roll",
            visibility=ResponseVisibility.BLIND,
            metadata={"command": "roll"},
        )

        await send_discord_response(
            source, response, destination_resolver=lambda *_args: ()
        )

        self.assertIn("No GM roll channel", channel.sent[0])
        self.assertEqual(author.sent, [])
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
