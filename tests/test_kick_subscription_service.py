import sys
import types
import unittest

if "aiohttp" not in sys.modules:
    try:
        import aiohttp  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["aiohttp"] = types.SimpleNamespace(
            BasicAuth=lambda *args, **kwargs: (args, kwargs)
        )

from services.kickSubscriptionService import KickSubscriptionService


class _Response:
    def __init__(self, status, body):
        self.status = status
        self.body = body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def json(self, content_type=None):
        return self.body

    async def text(self):
        return str(self.body)


class _Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def get(self, url, **kwargs):
        self.requests.append(("GET", url, kwargs))
        return _Response(*self.responses.pop(0))

    def post(self, url, **kwargs):
        self.requests.append(("POST", url, kwargs))
        return _Response(*self.responses.pop(0))


class _Platforms:
    def __init__(self, subscription_id=None):
        self.saved = []
        self.subscription_id = subscription_id

    def effective_guild_platform(self, guild_id, platform):
        return {
            "access_token": "token",
            "chat_subscription_id": self.subscription_id,
        }

    def set_guild_platform_override(self, guild_id, platform, name, value):
        self.saved.append((str(guild_id), platform, name, value))


class KickSubscriptionTests(unittest.IsolatedAsyncioTestCase):
    async def test_reuses_existing_chat_subscription(self):
        platforms = _Platforms()
        service = KickSubscriptionService(platforms)
        session = _Session(
            [(200, {"data": [{"id": "sub-1", "event": "chat.message.sent"}]})]
        )

        result = await service.ensure_chat("42", session)

        self.assertEqual(result, "sub-1")
        self.assertEqual(len(session.requests), 1)
        self.assertIn(("42", "kick", "chat_subscription_id", "sub-1"), platforms.saved)

    async def test_creates_missing_chat_subscription(self):
        platforms = _Platforms()
        service = KickSubscriptionService(platforms)
        session = _Session(
            [
                (200, {"data": []}),
                (
                    200,
                    {
                        "data": [
                            {
                                "name": "chat.message.sent",
                                "version": 1,
                                "subscription_id": "sub-2",
                            }
                        ]
                    },
                ),
            ]
        )

        result = await service.ensure_chat("42", session)

        self.assertEqual(result, "sub-2")
        request = session.requests[1][2]["json"]
        self.assertEqual(request["method"], "webhook")
        self.assertEqual(request["events"][0]["name"], "chat.message.sent")

    async def test_unchanged_subscription_is_not_saved_or_logged_again(self):
        class Logger:
            def __init__(self):
                self.messages = []

            def info(self, message, **_kwargs):
                self.messages.append(message)

        platforms = _Platforms(subscription_id="sub-1")
        logger = Logger()
        service = KickSubscriptionService(platforms, logger)
        session = _Session(
            [(200, {"data": [{"id": "sub-1", "event": "chat.message.sent"}]})]
        )

        result = await service.ensure_chat("42", session)

        self.assertEqual(result, "sub-1")
        self.assertEqual(platforms.saved, [])
        self.assertEqual(logger.messages, [])


if __name__ == "__main__":
    unittest.main()
