"""Per-guild Facebook Page publishing adapter."""

from adapters.platform_api_adapter import PlatformApiAdapter, json_request
from core.command_model import CommandPlatform


class FacebookAdapter(PlatformApiAdapter):
    def __init__(self):
        super().__init__(CommandPlatform.FACEBOOK, ("posting", "live_events"))

    async def create_post(self, settings, text, session, *, link=None):
        page_id = settings.get("page_id")
        token = settings.get("access_token")
        if not page_id or not token:
            raise ValueError("Facebook page_id and access_token are required")
        payload = {"message": text, "access_token": token}
        if link:
            payload["link"] = link
        return await json_request(
            session,
            "POST",
            f"https://graph.facebook.com/v26.0/{page_id}/feed",
            expected=(200,),
            data=payload,
        )

    async def create_image_post(self, settings, text, media, session):
        page_id = settings.get("page_id")
        token = settings.get("access_token")
        if not page_id or not token:
            raise ValueError("Facebook page_id and access_token are required")
        results = []
        for index, item in enumerate(media):
            import aiohttp

            form = aiohttp.FormData()
            form.add_field("access_token", token)
            form.add_field("published", "true")
            if text and index == 0:
                form.add_field("caption", text[:2000])
            with open(item["path"], "rb") as image:
                form.add_field(
                    "source",
                    image,
                    filename=item["path"].rsplit("/", 1)[-1],
                    content_type=item["content_type"],
                )
                results.append(
                    await json_request(
                        session,
                        "POST",
                        f"https://graph.facebook.com/v26.0/{page_id}/photos",
                        data=form,
                    )
                )
        return results


FACEBOOK_ADAPTER = FacebookAdapter()
