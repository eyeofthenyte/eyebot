import unittest
import sys
import types

if "aiohttp" not in sys.modules:
    try:
        import aiohttp  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["aiohttp"] = types.SimpleNamespace(
            BasicAuth=lambda *args, **kwargs: (args, kwargs)
        )

from core.command_model import CommandResponse
from core.command_router import CommandRouter
from services.kickCommandService import KickCommandService
from services.kickWebhookService import KickWebhookEvent
from datetime import datetime, timezone


class _Response:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def json(self, content_type=None):
        return {"data": {"is_sent": True, "message_id": "bot-message-1"}}


class _Session:
    def __init__(self):
        self.posts = []

    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        return _Response()


class _ReplayStore:
    def __init__(self):
        self.ids = []

    def remember_message_id(self, message_id):
        self.ids.append(message_id)


class _PlatformService:
    def __init__(self, *, second=False):
        self.guilds = {
            "42": {"prefix": "!"},
            **({"43": {"prefix": "!"}} if second else {}),
        }
        self.settings = {
            "available": True,
            "enabled": True,
            "connected": True,
            "livestream_chat_commands_enabled": True,
            "broadcaster_user_id": "100",
            "chat_subscription_id": "subscription-1",
            "access_token": "token",
        }

    def platform(self, name):
        return {
            "available": True,
            "livestream_chat_commands_enabled": True,
        }

    def discord_guilds(self):
        return self.guilds

    def effective_guild_platform(self, guild_id, platform):
        return dict(self.settings)


def event(content="!r 1d20"):
    return KickWebhookEvent(
        message_id="message-1",
        subscription_id="subscription-1",
        event_type="chat.message.sent",
        event_version="1",
        timestamp=datetime.now(timezone.utc),
        payload={
            "message_id": "message-1",
            "content": content,
            "broadcaster": {
                "user_id": 100,
                "username": "Channel",
                "channel_slug": "channel",
            },
            "sender": {
                "user_id": 200,
                "username": "roller",
                "channel_slug": "roller",
                "is_anonymous": False,
                "identity": {"badges": []},
            },
        },
    )


class KickCommandServiceTests(unittest.IsolatedAsyncioTestCase):
    def build(self, platform_service=None):
        router = CommandRouter()

        @router.command("roll", aliases=("r",))
        async def roll(request):
            return CommandResponse.text(f"Rolled {request.argument_text}")

        replay = _ReplayStore()
        service = KickCommandService(
            {"prefix": "!"}, platform_service or _PlatformService(), router, replay
        )
        return service, replay

    async def test_routes_alias_dispatches_and_records_bot_message(self):
        service, replay = self.build()
        session = _Session()

        outcome = await service.handle(
            event(), {"Kick-Event-Type": "chat.message.sent"}, session
        )

        self.assertEqual(outcome, "processed")
        self.assertEqual(session.posts[0][1]["json"]["content"], "Rolled 1d20")
        self.assertEqual(session.posts[0][1]["json"]["type"], "bot")
        self.assertEqual(replay.ids, ["bot-message-1"])

    async def test_non_command_is_ignored(self):
        service, _ = self.build()
        self.assertEqual(
            await service.handle(
                event("hello"), {"Kick-Event-Type": "chat.message.sent"}, _Session()
            ),
            "not_command",
        )

    async def test_ambiguous_multi_guild_route_does_not_duplicate_response(self):
        service, _ = self.build(_PlatformService(second=True))
        session = _Session()
        self.assertEqual(
            await service.handle(
                event(), {"Kick-Event-Type": "chat.message.sent"}, session
            ),
            "ambiguous",
        )
        self.assertEqual(session.posts, [])


if __name__ == "__main__":
    unittest.main()
