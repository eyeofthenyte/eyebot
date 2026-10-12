import unittest
from unittest.mock import patch

from services.twitchHelixTokenService import TwitchHelixTokenService


class Response:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def json(self, **kwargs):
        return self.payload


class Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class TwitchHelixTokenTests(unittest.IsolatedAsyncioTestCase):
    async def test_app_token_is_cached_until_near_expiration(self):
        service = TwitchHelixTokenService(
            {"client_id": "client", "client_secret": "secret"}
        )
        session = Session([Response({"access_token": "app-token", "expires_in": 3600})])
        with patch(
            "services.twitchHelixTokenService.time.monotonic",
            side_effect=[100, 100, 100, 101],
        ):
            first = await service.access_token(session)
            second = await service.access_token(session)
        self.assertEqual(first, "app-token")
        self.assertEqual(second, "app-token")
        self.assertEqual(len(session.calls), 1)
        self.assertEqual(session.calls[0][1]["data"]["grant_type"], "client_credentials")

    async def test_forced_refresh_replaces_cached_app_token(self):
        service = TwitchHelixTokenService(
            {"client_id": "client", "client_secret": "secret"}
        )
        session = Session([
            Response({"access_token": "first", "expires_in": 3600}),
            Response({"access_token": "second", "expires_in": 3600}),
        ])
        first = await service.access_token(session)
        second = await service.access_token(session, force=True)
        self.assertEqual((first, second), ("first", "second"))
        self.assertEqual(len(session.calls), 2)

    async def test_legacy_chat_token_remains_a_compatible_fallback(self):
        service = TwitchHelixTokenService({"tmi_token": "oauth:user-token"})
        self.assertEqual(await service.access_token(object()), "user-token")

    async def test_app_token_error_is_actionable(self):
        service = TwitchHelixTokenService(
            {"client_id": "client", "client_secret": "secret"}
        )
        session = Session([Response({"message": "invalid client secret"}, 400)])
        with self.assertRaisesRegex(RuntimeError, "invalid client secret"):
            await service.access_token(session)


if __name__ == "__main__":
    unittest.main()
