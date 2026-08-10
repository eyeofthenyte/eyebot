"""Per-guild TikTok approved Content Posting adapter."""

from adapters.platform_api_adapter import PlatformApiAdapter, json_request
from core.command_model import CommandPlatform


class TikTokAdapter(PlatformApiAdapter):
    def __init__(self):
        super().__init__(CommandPlatform.TIKTOK, ("video_posting",))

    async def initialize_video_post(self, settings, title, video_url, session):
        token = settings.get("access_token")
        if not token:
            raise ValueError("TikTok access_token is required")
        if not str(video_url).startswith("https://"):
            raise ValueError("TikTok video URL must use HTTPS")
        return await json_request(
            session,
            "POST",
            "https://open.tiktokapis.com/v2/post/publish/video/init/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"},
            json={
                "post_info": {"title": title, "privacy_level": "SELF_ONLY", "disable_duet": False, "disable_comment": False, "disable_stitch": False},
                "source_info": {"source": "PULL_FROM_URL", "video_url": video_url},
            },
        )

    async def initialize_photo_post(self, settings, title, image_urls, session):
        token = settings.get("access_token")
        if not token:
            raise ValueError("TikTok access_token is required")
        selected = [str(value) for value in image_urls]
        if not 1 <= len(selected) <= 35:
            raise ValueError("TikTok requires 1-35 photo URLs")
        if any(not value.startswith("https://") for value in selected):
            raise ValueError("TikTok photo URLs must use HTTPS")
        return await json_request(
            session,
            "POST",
            "https://open.tiktokapis.com/v2/post/publish/content/init/",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            json={
                "post_info": {
                    "title": title,
                    "description": title,
                    "privacy_level": "SELF_ONLY",
                    "disable_comment": False,
                    "auto_add_music": True,
                },
                "source_info": {
                    "source": "PULL_FROM_URL",
                    "photo_cover_index": 0,
                    "photo_images": selected,
                },
                "post_mode": "DIRECT_POST",
                "media_type": "PHOTO",
            },
        )


TIKTOK_ADAPTER = TikTokAdapter()
