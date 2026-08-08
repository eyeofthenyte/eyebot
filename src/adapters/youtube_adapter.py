"""Per-guild YouTube livestream-chat adapter."""

from adapters.platform_api_adapter import PlatformApiAdapter, json_request
from core.command_model import CommandPlatform


class YouTubeAdapter(PlatformApiAdapter):
    def __init__(self):
        super().__init__(CommandPlatform.YOUTUBE, ("live_events", "livestream_chat"))

    async def list_chat_messages(self, settings, live_chat_id, session, page_token=None):
        token = settings.get("access_token")
        if not token:
            raise ValueError("YouTube OAuth access_token is required")
        params = {"liveChatId": live_chat_id, "part": "id,snippet,authorDetails", "maxResults": 200}
        if page_token:
            params["pageToken"] = page_token
        return await json_request(
            session,
            "GET",
            "https://www.googleapis.com/youtube/v3/liveChat/messages",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )

    async def send_chat_message(self, settings, live_chat_id, text, session):
        token = settings.get("access_token")
        if not token:
            raise ValueError("YouTube OAuth access_token is required")
        return await json_request(
            session,
            "POST",
            "https://www.googleapis.com/youtube/v3/liveChat/messages",
            expected=(200,),
            headers={"Authorization": f"Bearer {token}"},
            params={"part": "snippet"},
            json={"snippet": {"liveChatId": live_chat_id, "type": "textMessageEvent", "textMessageDetails": {"messageText": text[:200]}}},
        )


YOUTUBE_ADAPTER = YouTubeAdapter()
