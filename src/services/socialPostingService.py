"""Platform-neutral validation and queuing for outbound social posts."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from services.mediaStagingService import MediaStagingService
from services.platformJobService import DuplicateJobError, PlatformJobService


TEXT_PLATFORMS = ("twitter", "facebook", "bluesky")
IMAGE_ATTACHMENT_PLATFORMS = ("twitter", "facebook", "bluesky")
URL_MEDIA_PLATFORMS = ("instagram", "tiktok")
ALL_POSTING_PLATFORMS = TEXT_PLATFORMS + URL_MEDIA_PLATFORMS
TEXT_LIMITS = {"twitter": 280, "facebook": 2000, "bluesky": 300, "instagram": 2000, "tiktok": 2000}


@dataclass(frozen=True)
class SocialPostRequest:
    guild_id: str
    platform: str
    text: str
    source_message_id: str
    requested_by: str
    attachments: tuple = ()
    media_url: str | None = None


@dataclass(frozen=True)
class SocialPostResult:
    queued: tuple[str, ...]


class SocialPostingService:
    def __init__(self, platform_service):
        self.platforms = platform_service
        self.jobs = PlatformJobService(platform_service.guild_config_dir / ".platform_jobs")
        self.media = MediaStagingService(platform_service.guild_config_dir / ".platform_media")

    async def queue(self, request: SocialPostRequest) -> SocialPostResult:
        selected = self._select_platforms(request)
        queued = []
        for platform in selected:
            settings = self.platforms.effective_guild_platform(request.guild_id, platform)
            if settings.get("enabled") is not True or settings.get("posting_enabled") is not True:
                if request.platform != "all":
                    raise ValueError(f"{platform} posting is disabled for this server")
                continue
            self._validate_text(
                platform,
                request.text,
                allow_empty=bool(request.attachments or request.media_url),
            )
            key = f"{request.guild_id}:{request.source_message_id}:{platform}"
            if request.attachments:
                staged = await self.media.stage_images(platform, request.attachments, alt_text=request.text)
                try:
                    self.jobs.enqueue(
                        request.guild_id,
                        platform,
                        "image_post",
                        {"text": request.text, "media": staged, "requested_by": request.requested_by},
                        idempotency_key=key,
                        source_message_id=request.source_message_id,
                    )
                except Exception:
                    self.media.remove(staged)
                    raise
            elif platform in URL_MEDIA_PLATFORMS:
                self.jobs.enqueue(
                    request.guild_id,
                    platform,
                    "post",
                    {"text": request.text, "media_url": request.media_url, "requested_by": request.requested_by},
                    idempotency_key=key,
                    source_message_id=request.source_message_id,
                )
            else:
                self.jobs.enqueue(
                    request.guild_id,
                    platform,
                    "post",
                    {"text": request.text, "requested_by": request.requested_by},
                    idempotency_key=key,
                    source_message_id=request.source_message_id,
                )
            queued.append(platform)
        if not queued:
            raise ValueError("None of the compatible platforms has posting enabled")
        return SocialPostResult(tuple(queued))

    def cancel(self, guild_id: str, source_message_id: str) -> int:
        removed = self.jobs.cancel_pending(guild_id, source_message_id)
        for job in removed:
            self.media.remove(job.get("payload", {}).get("media"))
        return len(removed)

    @staticmethod
    def _validate_url(value: str | None) -> None:
        parsed = urlparse(str(value or ""))
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Instagram and TikTok require a public HTTPS media URL")

    def _select_platforms(self, request: SocialPostRequest) -> tuple[str, ...]:
        selected = request.platform.casefold()
        if selected != "all" and selected not in ALL_POSTING_PLATFORMS:
            raise ValueError("Unsupported social posting platform")
        if request.attachments:
            if selected == "all":
                return IMAGE_ATTACHMENT_PLATFORMS
            if selected not in IMAGE_ATTACHMENT_PLATFORMS:
                raise ValueError(f"{selected} cannot publish Discord image attachments")
            return (selected,)
        if request.media_url:
            self._validate_url(request.media_url)
            if selected == "all":
                raise ValueError("Select Instagram or TikTok for URL-based media")
            if selected not in URL_MEDIA_PLATFORMS:
                raise ValueError(f"{selected} does not use URL-based media posting")
            return (selected,)
        if selected == "all":
            return TEXT_PLATFORMS
        if selected not in TEXT_PLATFORMS:
            raise ValueError(f"{selected} requires a public HTTPS media URL")
        return (selected,)

    @staticmethod
    def _validate_text(platform: str, text: str, *, allow_empty: bool = False) -> None:
        length = len(text)
        minimum = 0 if allow_empty else 1
        if not minimum <= length <= TEXT_LIMITS[platform]:
            raise ValueError(
                f"{platform} post text must contain {minimum}-{TEXT_LIMITS[platform]} characters"
            )


__all__ = [
    "DuplicateJobError",
    "SocialPostRequest",
    "SocialPostResult",
    "SocialPostingService",
]
