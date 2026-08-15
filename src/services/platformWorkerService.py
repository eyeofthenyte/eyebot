"""Execute queued outbound social jobs in the owning platform child."""

from __future__ import annotations

import asyncio

from adapters.bluesky_adapter import BLUESKY_ADAPTER
from adapters.facebook_adapter import FACEBOOK_ADAPTER
from adapters.instagram_adapter import INSTAGRAM_ADAPTER
from adapters.tiktok_adapter import TIKTOK_ADAPTER
from adapters.twitter_adapter import TWITTER_ADAPTER
from services.platformJobService import PlatformJobService
from services.mediaStagingService import MediaStagingService
from services.tokenRefreshService import TokenRefreshService


ADAPTERS = {
    "bluesky": BLUESKY_ADAPTER,
    "facebook": FACEBOOK_ADAPTER,
    "instagram": INSTAGRAM_ADAPTER,
    "tiktok": TIKTOK_ADAPTER,
    "twitter": TWITTER_ADAPTER,
}


class PlatformWorkerService:
    def __init__(self, platform, platform_service, logger):
        self.platform = platform
        self.platforms = platform_service
        self.logger = logger
        self.jobs = PlatformJobService(
            platform_service.guild_config_dir / ".platform_jobs"
        )
        self.tokens = TokenRefreshService(platform_service, logger)
        self.media = MediaStagingService(
            platform_service.guild_config_dir / ".platform_media"
        )

    async def execute(self, job, session):
        if self.platform != "bluesky":
            await self.tokens.refresh_guild(
                job["guild_id"], self.platform, session
            )
        settings = self.platforms.effective_guild_platform(
            job["guild_id"], self.platform
        )
        if settings.get("available", True) is not True:
            raise RuntimeError(f"{self.platform} is unavailable on this EyeBot host")
        if settings.get("enabled") is not True or settings.get("posting_enabled") is not True:
            raise RuntimeError(f"{self.platform} posting is disabled for this guild")
        payload = job.get("payload", {})
        adapter = ADAPTERS[self.platform]
        if job.get("operation") == "hosted_media_post":
            media_urls = [
                str(item.get("url") or "")
                for item in payload.get("media", ())
                if item.get("url")
            ]
            if not media_urls:
                raise RuntimeError("Hosted-media job does not contain public URLs")
            if self.platform == "instagram":
                return await adapter.create_image_post(
                    settings,
                    str(payload.get("text") or ""),
                    media_urls,
                    session,
                )
            if self.platform == "tiktok":
                return await adapter.initialize_photo_post(
                    settings,
                    str(payload.get("text") or ""),
                    media_urls,
                    session,
                )
            raise RuntimeError(
                f"{self.platform} does not accept hosted-media jobs"
            )
        if job.get("operation") == "image_post":
            if self.platform not in {"twitter", "facebook", "bluesky"}:
                raise RuntimeError(
                    f"{self.platform} does not accept staged Discord images"
                )
            return await adapter.create_image_post(
                settings,
                str(payload.get("text") or ""),
                list(payload.get("media") or ()),
                session,
            )
        if self.platform in {"twitter", "bluesky"}:
            return await adapter.create_post(settings, str(payload.get("text") or ""), session)
        if self.platform == "facebook":
            return await adapter.create_post(
                settings,
                str(payload.get("text") or ""),
                session,
                link=payload.get("url"),
            )
        if self.platform == "instagram":
            return await adapter.create_image_post(
                settings,
                str(payload.get("text") or ""),
                str(payload.get("media_url") or ""),
                session,
            )
        if self.platform == "tiktok":
            return await adapter.initialize_video_post(
                settings,
                str(payload.get("text") or ""),
                str(payload.get("media_url") or ""),
                session,
            )
        raise RuntimeError(f"Unsupported worker platform: {self.platform}")

    async def run_forever(self):
        import aiohttp

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        ) as session:
            while True:
                selected = self.jobs.claim_next(self.platform)
                if selected is None:
                    await asyncio.sleep(2)
                    continue
                claimed, job = selected
                try:
                    await self.execute(job, session)
                    self.jobs.complete(claimed)
                    self.media.remove(job.get("payload", {}).get("media"))
                    self.logger.info(
                        f"Completed {self.platform} job {job.get('id')}",
                        guild_id=job.get("guild_id"),
                    )
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    dead = self.jobs.fail(claimed, job, error)
                    if dead:
                        self.media.remove(job.get("payload", {}).get("media"))
                    self.logger.error(
                        f"Failed {self.platform} job {job.get('id')}: {error}",
                        guild_id=job.get("guild_id"),
                    )
