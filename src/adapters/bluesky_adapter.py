"""Per-guild Bluesky posting adapter using an app password."""

import asyncio

from adapters.platform_api_adapter import PlatformApiAdapter
from core.command_model import CommandPlatform


class BlueskyAdapter(PlatformApiAdapter):
    def __init__(self):
        super().__init__(CommandPlatform.BLUESKY, ("posting",))

    async def create_post(self, settings, text, session=None):
        handle = settings.get("handle")
        password = settings.get("app_password")
        if not handle or not password:
            raise ValueError("Bluesky handle and app_password are required")
        if not 1 <= len(text) <= 300:
            raise ValueError("Bluesky post text must contain 1-300 characters")

        def publish():
            from atproto import Client

            client = Client()
            client.login(handle, password)
            return client.send_post(text=text)

        return await asyncio.to_thread(publish)

    async def create_image_post(self, settings, text, media, session=None):
        handle = settings.get("handle")
        password = settings.get("app_password")
        if not handle or not password:
            raise ValueError("Bluesky handle and app_password are required")
        if len(media) > 4:
            raise ValueError("Bluesky supports at most four images per post")

        def publish():
            from atproto import Client, models

            client = Client()
            client.login(handle, password)
            images = []
            for item in media:
                with open(item["path"], "rb") as source:
                    payload = source.read()
                if len(payload) > 2_000_000:
                    raise ValueError(
                        "Each Bluesky image must be no larger than 2,000,000 bytes"
                    )
                blob = client.upload_blob(payload).blob
                images.append(
                    models.AppBskyEmbedImages.Image(
                        alt=item.get("alt_text", "")[:1000],
                        image=blob,
                    )
                )
            embed = models.AppBskyEmbedImages.Main(images=images)
            return client.send_post(text=text[:300], embed=embed)

        return await asyncio.to_thread(publish)


BLUESKY_ADAPTER = BlueskyAdapter()
