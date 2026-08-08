"""Per-guild Instagram professional-account publishing adapter."""

from adapters.platform_api_adapter import PlatformApiAdapter, json_request
from core.command_model import CommandPlatform


class InstagramAdapter(PlatformApiAdapter):
    def __init__(self):
        super().__init__(CommandPlatform.INSTAGRAM, ("image_posting", "live_events"))

    async def create_image_post(self, settings, caption, image_url, session):
        account_id = settings.get("account_id")
        token = settings.get("access_token")
        if not account_id or not token:
            raise ValueError("Instagram account_id and access_token are required")
        if not str(image_url).startswith("https://"):
            raise ValueError("Instagram image URL must use HTTPS")
        container = await json_request(
            session,
            "POST",
            f"https://graph.facebook.com/v26.0/{account_id}/media",
            data={"image_url": image_url, "caption": caption, "access_token": token},
        )
        return await json_request(
            session,
            "POST",
            f"https://graph.facebook.com/v26.0/{account_id}/media_publish",
            data={"creation_id": container["id"], "access_token": token},
        )


INSTAGRAM_ADAPTER = InstagramAdapter()
