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

from services.facebookPageService import (
    FacebookPageMonitorService,
    facebook_page_reference,
    resolve_facebook_page,
)


class Response:
    def __init__(self, body, status=200):
        self.body = body
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def json(self, content_type=None):
        return self.body


class Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def get(self, url, **kwargs):
        self.requests.append((url, kwargs))
        return self.responses.pop(0)


class Logger:
    def info(self, message):
        pass

    def error(self, message):
        pass


class Platforms:
    def __init__(self, root, rows):
        self.guild_config_dir = Path(root)
        self.rows = rows

    def discord_guilds(self):
        return {"42": {}}

    def effective_guild_platform(self, guild_id, platform):
        return self.rows


class FacebookPageServiceTests(unittest.IsolatedAsyncioTestCase):
    def test_reference_accepts_page_urls_and_rejects_content_urls(self):
        self.assertEqual(
            facebook_page_reference("https://www.facebook.com/EoNCreations/"),
            "EoNCreations",
        )
        self.assertEqual(
            facebook_page_reference("https://facebook.com/profile.php?id=12345"),
            "12345",
        )
        with self.assertRaises(ValueError):
            facebook_page_reference("https://facebook.com/EoNCreations/posts/1")

    async def test_resolver_returns_accessible_page(self):
        session = Session(
            [
                Response(
                    {
                        "data": [
                            {
                                "id": "12345",
                                "name": "Example",
                                "link": "https://facebook.com/example",
                            }
                        ]
                    }
                ),
                Response({"data": [{"id": "post-1"}]}),
            ]
        )
        result = await resolve_facebook_page(
            "https://facebook.com/example", "token", session
        )
        self.assertEqual(result["page_id"], "12345")
        self.assertNotIn("token", str(result))

    async def test_resolver_rejects_page_not_in_managed_accounts(self):
        session = Session(
            [
                Response({"data": []}),
                Response(
                    {
                        "id": "12345",
                        "name": "Public but unmanaged",
                        "link": "https://facebook.com/example",
                    }
                ),
            ]
        )
        with self.assertRaisesRegex(ValueError, "not managed"):
            await resolve_facebook_page(
                "https://facebook.com/example", "token", session
            )

    async def test_monitor_baselines_then_posts_new_content(self):
        with tempfile.TemporaryDirectory() as root:
            settings = {
                "available": True,
                "enabled": True,
                "access_token": "token",
                "monitored_pages": [
                    {
                        "page_id": "12345",
                        "name": "Example",
                        "url": "https://facebook.com/example",
                        "destination_channel": "987654321098765432",
                    }
                ],
            }
            service = Platforms(root, settings)
            monitor = FacebookPageMonitorService({}, service, Logger())
            monitor.tokens.refresh_guild = types.MethodType(
                lambda self, *args: _false(), monitor.tokens
            )
            delivered = []

            async def send(session, destination, content, **kwargs):
                delivered.append((destination, content))

            monitor.discord.send = send
            first = Session([Response({"data": [{"id": "post-1"}]})])
            await monitor.poll_once(first)
            self.assertEqual(delivered, [])

            second = Session(
                [
                    Response(
                        {
                            "data": [
                                {
                                    "id": "post-2",
                                    "message": "New post",
                                    "permalink_url": "https://facebook.com/post-2",
                                },
                                {"id": "post-1"},
                            ]
                        }
                    )
                ]
            )
            await monitor.poll_once(second)
            self.assertEqual(delivered[0][0], "987654321098765432")
            self.assertIn("New post", delivered[0][1])


async def _false():
    return False


if __name__ == "__main__":
    unittest.main()
