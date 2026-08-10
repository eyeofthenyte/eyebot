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
        image_urls = (
            [str(value) for value in image_url]
            if isinstance(image_url, (list, tuple))
            else [str(image_url)]
        )
        if not 1 <= len(image_urls) <= 10:
            raise ValueError("Instagram requires 1-10 image URLs")
        if any(not value.startswith("https://") for value in image_urls):
            raise ValueError("Instagram image URLs must use HTTPS")
        if len(image_urls) > 1:
            child_ids = []
            for value in image_urls:
                child = await json_request(
                    session,
                    "POST",
                    f"https://graph.facebook.com/v26.0/{account_id}/media",
                    data={
                        "image_url": value,
                        "is_carousel_item": "true",
                        "access_token": token,
                    },
                )
                child_ids.append(str(child["id"]))
            container = await json_request(
                session,
                "POST",
                f"https://graph.facebook.com/v26.0/{account_id}/media",
                data={
                    "media_type": "CAROUSEL",
                    "children": ",".join(child_ids),
                    "caption": caption,
                    "access_token": token,
                },
            )
        else:
            container = await json_request(
                session,
                "POST",
                f"https://graph.facebook.com/v26.0/{account_id}/media",
                data={
                    "image_url": image_urls[0],
                    "caption": caption,
                    "access_token": token,
                },
            )
        return await json_request(
            session,
            "POST",
            f"https://graph.facebook.com/v26.0/{account_id}/media_publish",
            data={"creation_id": container["id"], "access_token": token},
        )


INSTAGRAM_ADAPTER = InstagramAdapter()
