"""Per-guild X posting adapter."""

from adapters.platform_api_adapter import PlatformApiAdapter, json_request
from core.command_model import CommandPlatform


class TwitterAdapter(PlatformApiAdapter):
    def __init__(self):
        super().__init__(CommandPlatform.TWITTER, ("posting",))

    async def create_post(self, settings, text, session):
        token = settings.get("access_token")
        if not token:
            raise ValueError("X access_token is not configured")
        if not 1 <= len(text) <= 280:
            raise ValueError("X post text must contain 1-280 characters")
        return await json_request(
            session,
            "POST",
            "https://api.x.com/2/tweets",
            expected=(201,),
            headers={"Authorization": f"Bearer {token}"},
            json={"text": text},
        )

    async def create_image_post(self, settings, text, media, session):
        token = settings.get("access_token")
        if not token:
            raise ValueError("X access_token is not configured")
        if len(media) > 4:
            raise ValueError("X supports at most four images per post")
        media_ids = []
        for item in media:
            import aiohttp

            form = aiohttp.FormData()
            form.add_field("media_category", "tweet_image")
            with open(item["path"], "rb") as image:
                form.add_field(
                    "media",
                    image,
                    filename=item["path"].rsplit("/", 1)[-1],
                    content_type=item["content_type"],
                )
                uploaded = await json_request(
                    session,
                    "POST",
                    "https://api.x.com/2/media/upload",
                    expected=(200, 201, 202),
                    headers={"Authorization": f"Bearer {token}"},
                    data=form,
                )
            data = uploaded.get("data", uploaded)
            media_id = data.get("id") or data.get("media_id_string")
            if not media_id:
                raise RuntimeError("X media upload did not return a media ID")
            media_ids.append(str(media_id))
        return await json_request(
            session,
            "POST",
            "https://api.x.com/2/tweets",
            expected=(201,),
            headers={"Authorization": f"Bearer {token}"},
            json={"text": text[:280], "media": {"media_ids": media_ids}},
        )


TWITTER_ADAPTER = TwitterAdapter()
