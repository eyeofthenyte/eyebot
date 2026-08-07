import unittest

from core.command_model import (
    CommandActor,
    CommandPlatform,
    CommandRequest,
    CommandSurface,
)
from core.command_router import CommandRouter
from core.transport import CommandTransportAdapter


class FakeTransport(CommandTransportAdapter):
    def __init__(self, router):
        super().__init__(router)
        self.responses = []

    def to_request(self, native_message):
        return CommandRequest.from_text(
            platform=CommandPlatform.GENERIC,
            surface=CommandSurface.CHANNEL,
            actor=CommandActor(id="1", username="tester"),
            content=native_message,
        )

    async def send_response(self, native_message, response):
        self.responses.append((native_message, response))


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_dispatches_registered_command(self):
        router = CommandRouter()

        @router.command("ping")
        async def ping(_request):
            from core.command_model import CommandResponse

            return CommandResponse.text("pong")

        adapter = FakeTransport(router)
        handled = await adapter.dispatch("!ping")
        self.assertTrue(handled)
        self.assertEqual(adapter.responses[0][1].messages[0].content, "pong")

    async def test_leaves_unknown_or_non_command_messages_unhandled(self):
        adapter = FakeTransport(CommandRouter())
        self.assertFalse(await adapter.dispatch("hello"))
        self.assertFalse(await adapter.dispatch("!native-command"))
        self.assertEqual(adapter.responses, [])
