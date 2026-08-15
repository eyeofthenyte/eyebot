import sys
import tempfile
import types
import unittest
from pathlib import Path

if "aiohttp" not in sys.modules:
    try: import aiohttp  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["aiohttp"] = types.SimpleNamespace(BasicAuth=lambda *a, **k: None)

from services.tiktokVideoMonitorService import TikTokVideoMonitorService

class Response:
    def __init__(self, body, status=200): self.body, self.status = body, status
    async def __aenter__(self): return self
    async def __aexit__(self, *args): return False
    async def json(self, content_type=None): return self.body

class Session:
    def __init__(self, bodies): self.bodies = list(bodies)
    def post(self, *args, **kwargs): return Response(self.bodies.pop(0))

class Platforms:
    def __init__(self, root, settings): self.guild_config_dir, self.settings = Path(root), settings
    def discord_guilds(self): return {"42": {}}
    def effective_guild_platform(self, *args): return self.settings

class Logger:
    def info(self, message, **kwargs): pass
    def error(self, message, **kwargs): pass

async def _false(): return False

class TikTokVideoMonitorTests(unittest.IsolatedAsyncioTestCase):
    async def test_baselines_then_delivers_connected_account_video(self):
        with tempfile.TemporaryDirectory() as root:
            settings = {
                "enabled": True, "videos_enabled": True, "access_token": "token",
                "destination_channel": "987654321098765432",
            }
            monitor = TikTokVideoMonitorService({}, Platforms(root, settings), Logger())
            monitor.tokens.refresh_guild = types.MethodType(lambda self, *a: _false(), monitor.tokens)
            sent = []
            async def send(session, destination, content, **kwargs): sent.append((destination, content))
            monitor.discord.send = send
            await monitor.poll_once(Session([{"data": {"videos": [{"id": "v1"}]}}]))
            self.assertEqual(sent, [])
            await monitor.poll_once(Session([{"data": {"videos": [{"id": "v2", "title": "New", "share_url": "https://tiktok.com/v2"}]}}]))
            self.assertEqual(sent[0][0], "987654321098765432")

if __name__ == "__main__": unittest.main()
