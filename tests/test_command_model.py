import asyncio
import unittest
from datetime import datetime, timezone

from core import (
    CommandActor,
    CommandLocation,
    CommandParseError,
    CommandPlatform,
    CommandRequest,
    CommandResponse,
    CommandRouter,
    CommandStatus,
    CommandSurface,
    ResponseAttachment,
    ResponseCard,
    ResponseField,
    ResponseMessage,
    ResponseVisibility,
)


class CommandRequestTests(unittest.TestCase):
    def setUp(self):
        self.actor = CommandActor(
            id="42",
            username="eyeofthenyte",
            display_name="Eye",
            roles=("DM",),
        )
        self.location = CommandLocation(
            channel_id="100",
            channel_name="table-chat",
            community_id="200",
            community_name="Grand Draconaeum",
        )

    def parse(self, content):
        return CommandRequest.from_text(
            platform=CommandPlatform.DISCORD,
            surface=CommandSurface.CHANNEL,
            actor=self.actor,
            location=self.location,
            content=content,
            prefix="!",
        )

    def test_parses_and_normalizes_command(self):
        request = self.parse('  !RoLl "Test Attack" -dm  ')

        self.assertEqual(request.command, "roll")
        self.assertEqual(request.arguments, ("Test Attack", "-dm"))
        self.assertEqual(request.argument_text, "Test Attack -dm")
        self.assertEqual(request.platform, CommandPlatform.DISCORD)
        self.assertEqual(request.location.community_id, "200")
        self.assertIsNotNone(request.request_id)
        self.assertIsNotNone(request.received_at.tzinfo)

    def test_supports_every_chat_surface_without_sdk_objects(self):
        for platform, surface in (
            (CommandPlatform.TWITCH, CommandSurface.LIVESTREAM_CHAT),
            (CommandPlatform.YOUTUBE, CommandSurface.LIVESTREAM_CHAT),
            (CommandPlatform.FACEBOOK, CommandSurface.LIVESTREAM_CHAT),
            (CommandPlatform.KICK, CommandSurface.LIVESTREAM_CHAT),
            (CommandPlatform.DISCORD, CommandSurface.DIRECT_MESSAGE),
        ):
            with self.subTest(platform=platform):
                request = CommandRequest.from_text(
                    platform=platform,
                    surface=surface,
                    actor=self.actor,
                    content="!oracle Will this work?",
                )
                self.assertEqual(request.command, "oracle")

    def test_rejects_non_commands_and_invalid_quotes(self):
        with self.assertRaisesRegex(CommandParseError, "prefix"):
            self.parse("roll 1d20")
        with self.assertRaisesRegex(CommandParseError, "cannot be empty"):
            self.parse("!")
        with self.assertRaisesRegex(CommandParseError, "quoting"):
            self.parse('!roll "unterminated')

    def test_requires_timezone_aware_timestamp(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            CommandRequest(
                platform=CommandPlatform.GENERIC,
                surface=CommandSurface.SYSTEM,
                actor=self.actor,
                command="test",
                received_at=datetime(2026, 1, 1),
            )

    def test_request_round_trip_serialization(self):
        request = self.parse("!roll 2d6+4")

        restored = CommandRequest.from_dict(request.to_dict())

        self.assertEqual(restored, request)


class CommandResponseTests(unittest.TestCase):
    def test_text_and_error_factories(self):
        success = CommandResponse.text("Done")
        error = CommandResponse.error(
            "Unknown command",
            error_code="command_not_found",
        )

        self.assertEqual(success.status, CommandStatus.SUCCESS)
        self.assertEqual(success.visibility, ResponseVisibility.PUBLIC)
        self.assertEqual(error.status, CommandStatus.ERROR)
        self.assertEqual(error.visibility, ResponseVisibility.REQUESTER)

    def test_structured_response_round_trip(self):
        response = CommandResponse(
            messages=(
                ResponseMessage(
                    content="Result",
                    card=ResponseCard(
                        title="Roll",
                        description="A neutral card",
                        fields=(
                            ResponseField("Total", "17"),
                            ResponseField("Private", "Yes", inline=True),
                        ),
                        footer="eyebot",
                        accent_color=0x019CD0,
                    ),
                    attachments=(
                        ResponseAttachment(
                            name="dice.png",
                            url="https://example.com/dice.png",
                            media_type="image/png",
                        ),
                    ),
                ),
            ),
            visibility=ResponseVisibility.REQUESTER,
            metadata={"pages": 1},
        )

        restored = CommandResponse.from_dict(response.to_dict())

        self.assertEqual(restored, response)

    def test_rejects_empty_messages_and_responses(self):
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            ResponseMessage()
        with self.assertRaisesRegex(ValueError, "at least one"):
            CommandResponse(messages=())
        with self.assertRaisesRegex(ValueError, "path or URL"):
            ResponseAttachment(name="missing")


class CommandRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = CommandRouter()
        self.request = CommandRequest.from_text(
            platform=CommandPlatform.TWITCH,
            surface=CommandSurface.LIVESTREAM_CHAT,
            actor=CommandActor(id="1", username="viewer"),
            content="!hi world",
        )

    def test_routes_async_handler_and_alias(self):
        @self.router.command("hello", aliases=("hi",))
        async def hello(request):
            return CommandResponse.text(f"Hello {request.argument_text}")

        response = asyncio.run(self.router.dispatch(self.request))

        self.assertEqual(response.messages[0].content, "Hello world")
        self.assertEqual(self.router.canonical_name("HI"), "hello")
        self.assertEqual(self.router.registered_commands, ("hello",))

    def test_routes_synchronous_handler(self):
        self.router.register(
            "hi",
            lambda request: CommandResponse.text(request.actor.username),
        )

        response = asyncio.run(self.router.dispatch(self.request))

        self.assertEqual(response.messages[0].content, "viewer")

    def test_returns_neutral_unknown_command_error(self):
        response = asyncio.run(self.router.dispatch(self.request))

        self.assertEqual(response.status, CommandStatus.ERROR)
        self.assertEqual(response.error_code, "command_not_found")

    def test_rejects_duplicate_and_invalid_names(self):
        self.router.register("hello", lambda _: CommandResponse.text("hello"))
        with self.assertRaisesRegex(ValueError, "already registered"):
            self.router.register("other", lambda _: CommandResponse.text("x"), aliases=("hello",))
        with self.assertRaisesRegex(ValueError, "only letters"):
            self.router.register("bad name", lambda _: CommandResponse.text("x"))

    def test_rejects_non_response_handler_results(self):
        self.router.register("hi", lambda _: "not a response")

        with self.assertRaisesRegex(TypeError, "CommandResponse"):
            asyncio.run(self.router.dispatch(self.request))


if __name__ == "__main__":
    unittest.main()
