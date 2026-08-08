import unittest

from eyebot_facebook import detect_facebook_live
from eyebot_instagram import detect_instagram_live
from eyebot_kick import detect_kick_live
from eyebot_twitter import detect_twitter_live
from eyebot_youtube import detect_youtube_live


class Response:
    def __init__(self, payload):
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def raise_for_status(self):
        pass

    async def json(self):
        return self.payload


class Session:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return Response(self.payload)


class LiveDetectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_youtube_live_result(self):
        session = Session({"items": [{"id": {"videoId": "abc"}, "snippet": {"title": "Game", "channelTitle": "Creator", "description": "Desc", "thumbnails": {}}}]})
        event = await detect_youtube_live({"channel_id": "UC" + "a" * 22, "api_key": "key"}, session)
        self.assertEqual(event.event_id, "abc")
        self.assertEqual(event.url, "https://www.youtube.com/watch?v=abc")

    async def test_facebook_ignores_non_live_rows(self):
        session = Session({"data": [{"id": "1", "status": "VOD"}]})
        event = await detect_facebook_live({"page_id": "12345", "access_token": "token"}, session)
        self.assertIsNone(event)

    async def test_kick_live_result(self):
        session = Session({"data": [{"name": "Creator", "stream": {"id": 7, "is_live": True, "title": "Now live"}}]})
        event = await detect_kick_live({"channel": "creator", "access_token": "token"}, session)
        self.assertEqual(event.event_id, "7")
        self.assertEqual(event.url, "https://kick.com/creator")

    async def test_x_spaces_requires_live_state(self):
        session = Session({"data": [{"id": "space", "state": "live", "title": "Talk"}]})
        event = await detect_twitter_live({"user_id": "12345", "bearer_token": "token"}, session)
        self.assertEqual(event.url, "https://x.com/i/spaces/space")

    async def test_instagram_live_media_result(self):
        session = Session({"data": [{"id": "ig1", "username": "creator", "caption": "Live", "permalink": "https://instagram.com/p/ig1"}]})
        event = await detect_instagram_live({"account_id": "12345", "access_token": "token"}, session)
        self.assertEqual(event.event_id, "ig1")


if __name__ == "__main__":
    unittest.main()
