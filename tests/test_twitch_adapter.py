import unittest
from types import SimpleNamespace

from adapters.twitch_adapter import (
    TwitchTransportAdapter,
    request_from_twitch_message,
    send_twitch_response,
    split_twitch_text,
)
from core.command_model import (
    CommandPlatform,
    CommandResponse,
    CommandSurface,
    ResponseAttachment,
    ResponseCard,
    ResponseField,
    ResponseMessage,
    ResponseVisibility,
)
from core.command_router import CommandRouter


class Destination:
    def __init__(self, name="channel"):
        self.name = name
        self.sent = []

    async def send(self, content):
        self.sent.append(content)


class Author(Destination):
    id = "7"
    display_name = "Test User"


def twitch_message(content="!roll 1d20"):
    author = Author("tester")
    channel = Destination("eyebot")
    return SimpleNamespace(
        content=content,
        author=author,
        channel=channel,
        tags={
            "id": "message-1",
            "room-id": "room-2",
            "mod": "1",
            "badges": "broadcaster/1,subscriber/12",
        },
        echo=False,
    )


class TwitchRequestTests(unittest.TestCase):
    def test_maps_twitch_chat_to_neutral_request(self):
        request = request_from_twitch_message(twitch_message(), prefix="!")
        self.assertEqual(request.platform, CommandPlatform.TWITCH)
        self.assertEqual(request.surface, CommandSurface.LIVESTREAM_CHAT)
        self.assertEqual(request.actor.id, "7")
        self.assertEqual(request.actor.username, "tester")
        self.assertIn("moderator", request.actor.roles)
        self.assertIn("broadcaster", request.actor.roles)
        self.assertEqual(request.location.channel_name, "eyebot")

    def test_splits_output_below_twitch_limit(self):
        chunks = split_twitch_text("word " * 300)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 450 for chunk in chunks))


class TwitchResponseTests(unittest.IsolatedAsyncioTestCase):
    async def test_flattens_cards_for_public_chat(self):
        message = twitch_message()
        response = CommandResponse(
            messages=(
                ResponseMessage(
                    card=ResponseCard(
                        title="Roll result",
                        fields=(ResponseField("Total", "17"),),
                    )
                ),
            ),
        )
        await send_twitch_response(message, response)
        self.assertEqual(message.channel.sent, ["Roll result | Total: 17"])

    async def test_removes_attachment_suffix_and_everything_after_it(self):
        message = twitch_message()
        response = CommandResponse(
            messages=(
                ResponseMessage(
                    content=(
                        "Roll result: 17 | Attachments: dice.png "
                        "| internal attachment detail"
                    ),
                    attachments=(
                        ResponseAttachment(name="dice.png", path="dice.png"),
                    ),
                ),
            ),
        )

        await send_twitch_response(message, response)

        self.assertEqual(message.channel.sent, ["Roll result: 17"])

    async def test_does_not_add_attachment_names_to_non_discord_output(self):
        message = twitch_message()
        response = CommandResponse(
            messages=(
                ResponseMessage(
                    content="Roll result: 17",
                    attachments=(
                        ResponseAttachment(name="dice.png", path="dice.png"),
                    ),
                ),
            ),
        )

        await send_twitch_response(message, response)

        self.assertEqual(message.channel.sent, ["Roll result: 17"])

    async def test_requester_response_uses_private_destination(self):
        message = twitch_message()
        response = CommandResponse.text(
            "secret",
            visibility=ResponseVisibility.REQUESTER,
        )
        await send_twitch_response(message, response)
        self.assertEqual(message.author.sent, ["secret"])
        self.assertEqual(message.channel.sent, [])

    async def test_blind_response_never_leaks_to_public_chat(self):
        message = twitch_message()
        response = CommandResponse.text(
            "hidden total",
            visibility=ResponseVisibility.BLIND,
        )
        await send_twitch_response(message, response)
        self.assertNotIn("hidden total", " ".join(message.channel.sent))

    async def test_transport_dispatches_through_shared_router(self):
        router = CommandRouter()

        @router.command("ping")
        async def ping(_request):
            return CommandResponse.text("pong")

        adapter = TwitchTransportAdapter(router)
        message = twitch_message("!ping")
        self.assertTrue(await adapter.dispatch(message))
        self.assertEqual(message.channel.sent, ["pong"])
