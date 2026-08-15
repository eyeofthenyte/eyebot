import tempfile
import unittest
from pathlib import Path

from services.blueskyAccountService import (
    BlueskyAccountMonitorService,
    bluesky_handle,
    resolve_bluesky_account,
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


class BlueskyAccountServiceTests(unittest.IsolatedAsyncioTestCase):
    def test_handle_accepts_profile_url_and_rejects_post_url(self):
        self.assertEqual(
            bluesky_handle("https://bsky.app/profile/ATProto.com"), "atproto.com"
        )
        with self.assertRaises(ValueError):
            bluesky_handle("https://bsky.app/profile/atproto.com/post/abc")

    async def test_resolver_verifies_public_profile_and_feed(self):
        session = Session(
            [
                Response({"did": "did:plc:example", "handle": "atproto.com", "displayName": "AT"}),
                Response({"feed": []}),
            ]
        )
        result = await resolve_bluesky_account("atproto.com", session)
        self.assertEqual(result["did"], "did:plc:example")
        self.assertEqual(len(session.calls), 2)

    async def test_monitor_baselines_then_delivers_new_post(self):
        with tempfile.TemporaryDirectory() as root:
            settings = {
                "available": True,
                "enabled": True,
                "monitored_accounts": [
                    {
                        "did": "did:plc:example",
                        "handle": "atproto.com",
                        "destination_channel": "987654321098765432",
                    }
                ],
            }
            monitor = BlueskyAccountMonitorService({}, Platforms(root, settings), Logger())
            delivered = []
            async def send(session, destination, content, **kwargs):
                delivered.append((destination, content, kwargs))
            monitor.discord.send = send
            old = "at://did:plc:example/app.bsky.feed.post/old"
            new = "at://did:plc:example/app.bsky.feed.post/new"
            await monitor.poll_once(
                Session([Response({"feed": [{"post": {"uri": old, "record": {"text": "Old"}}}]})])
            )
            self.assertEqual(delivered, [])
            await monitor.poll_once(
                Session([Response({"feed": [
                    {"post": {"uri": new, "record": {"text": "New post"}}},
                    {"post": {"uri": old, "record": {"text": "Old"}}},
                ]})])
            )
            self.assertEqual(delivered[0][0], "987654321098765432")
            self.assertIn("https://bsky.app/profile/atproto.com/post/new", delivered[0][1])


if __name__ == "__main__": unittest.main()
