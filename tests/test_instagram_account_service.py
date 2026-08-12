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

from services.instagramAccountService import (
    InstagramAccountMonitorService,
    instagram_username,
    resolve_instagram_account,
)


class Response:
    def __init__(self, body, status=200):
        self.body = body
        self.status = status

    async def __aenter__(self): return self
    async def __aexit__(self, *args): return False
    async def json(self, content_type=None): return self.body


class Session:
    def __init__(self, responses): self.responses = list(responses)
    def get(self, url, **kwargs): return self.responses.pop(0)


class Logger:
    def info(self, message): pass
    def error(self, message): pass


class Platforms:
    def __init__(self, root, settings):
        self.guild_config_dir = Path(root)
        self.settings = settings
    def discord_guilds(self): return {"42": {}}
    def effective_guild_platform(self, guild_id, platform): return self.settings


async def _false(): return False


class InstagramAccountServiceTests(unittest.IsolatedAsyncioTestCase):
    def test_username_accepts_profile_url_and_rejects_content(self):
        self.assertEqual(
            instagram_username("https://instagram.com/Example.Pro/"), "example.pro"
        )
        with self.assertRaises(ValueError):
            instagram_username("https://instagram.com/p/ABC123/")

    async def test_resolver_uses_business_discovery(self):
        session = Session(
            [Response({"business_discovery": {"id": "ig-2", "username": "example.pro"}})]
        )
        result = await resolve_instagram_account("example.pro", "owner-1", "token", session)
        self.assertEqual(result, {"account_id": "ig-2", "username": "example.pro"})

    async def test_monitor_baselines_then_posts_new_media(self):
        with tempfile.TemporaryDirectory() as root:
            settings = {
                "available": True,
                "enabled": True,
                "account_id": "owner-1",
                "access_token": "token",
                "monitored_accounts": [
                    {
                        "account_id": "ig-2",
                        "username": "example.pro",
                        "destination_channel": "987654321098765432",
                    }
                ],
            }
            monitor = InstagramAccountMonitorService({}, Platforms(root, settings), Logger())
            monitor.tokens.refresh_guild = types.MethodType(
                lambda self, *args: _false(), monitor.tokens
            )
            delivered = []
            async def send(session, destination, content, **kwargs):
                delivered.append((destination, content))
            monitor.discord.send = send
            await monitor.poll_once(
                Session([Response({"business_discovery": {"id": "ig-2", "media": {"data": [{"id": "m1"}]}}})])
            )
            self.assertEqual(delivered, [])
            await monitor.poll_once(
                Session([Response({"business_discovery": {"id": "ig-2", "media": {"data": [
                    {"id": "m2", "caption": "New media", "permalink": "https://instagram.com/p/x"},
                    {"id": "m1"},
                ]}}})])
            )
            self.assertEqual(delivered[0][0], "987654321098765432")
            self.assertIn("New media", delivered[0][1])


if __name__ == "__main__": unittest.main()
