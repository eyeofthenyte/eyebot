import sys
import tempfile
import types
import unittest
from pathlib import Path

if "aiohttp" not in sys.modules:
    try:
        import aiohttp  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["aiohttp"] = types.SimpleNamespace(
            BasicAuth=lambda *args, **kwargs: (args, kwargs)
        )

from services.twitterAccountService import (
    TwitterAccountMonitorService,
    resolve_twitter_account,
    twitter_username,
)


class Response:
    def __init__(self, body, status=200):
        self.body = body
        self.status = status
    async def __aenter__(self): return self
    async def __aexit__(self, *args): return False
    async def json(self, content_type=None): return self.body


class Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class Logger:
    def info(self, message, **kwargs): pass
    def error(self, message, **kwargs): pass


class Platforms:
    def __init__(self, root, settings):
        self.guild_config_dir = Path(root)
        self.settings = settings
    def discord_guilds(self): return {"42": {}}
    def effective_guild_platform(self, guild_id, platform): return self.settings


async def _false(): return False


class TwitterAccountServiceTests(unittest.IsolatedAsyncioTestCase):
    def test_username_accepts_profile_urls_and_rejects_post_urls(self):
        self.assertEqual(twitter_username("https://x.com/XDevelopers"), "xdevelopers")
        self.assertEqual(twitter_username("@EyeBot"), "eyebot")
        with self.assertRaises(ValueError):
            twitter_username("https://x.com/XDevelopers/status/123")

    async def test_resolver_verifies_public_readable_account(self):
        session = Session(
            [
                Response({"data": {"id": "1", "name": "Example", "username": "Example"}}),
                Response({"data": []}),
            ]
        )
        result = await resolve_twitter_account("example", "token", session)
        self.assertEqual(result["user_id"], "1")
        self.assertEqual(len(session.calls), 2)

    async def test_resolver_rejects_protected_account(self):
        session = Session(
            [Response({"data": {"id": "1", "username": "private", "protected": True}})]
        )
        with self.assertRaisesRegex(ValueError, "protected"):
            await resolve_twitter_account("private", "token", session)

    async def test_monitor_baselines_then_delivers_new_posts(self):
        with tempfile.TemporaryDirectory() as root:
            settings = {
                "available": True,
                "enabled": True,
                "bearer_token": "token",
                "monitored_accounts": [
                    {
                        "user_id": "1",
                        "username": "example",
                        "destination_channel": "987654321098765432",
                    }
                ],
            }
            monitor = TwitterAccountMonitorService({}, Platforms(root, settings), Logger())
            monitor.tokens.refresh_guild = types.MethodType(
                lambda self, *args: _false(), monitor.tokens
            )
            delivered = []
            async def send(session, destination, content, **kwargs):
                delivered.append((destination, content, kwargs))
            monitor.discord.send = send

            await monitor.poll_once(Session([Response({"data": [{"id": "p1"}]})]))
            self.assertEqual(delivered, [])
            await monitor.poll_once(
                Session([Response({"data": [{"id": "p2", "text": "New post"}]})])
            )
            self.assertEqual(delivered[0][0], "987654321098765432")
            self.assertIn("https://x.com/example/status/p2", delivered[0][1])
            self.assertEqual(delivered[0][2]["url"], "https://x.com/example/status/p2")


if __name__ == "__main__": unittest.main()
