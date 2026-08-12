"""Platform-neutral validation and queuing for outbound social posts."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from services.mediaStagingService import MediaStagingService
from services.platformJobService import DuplicateJobError, PlatformJobService
from services.publicMediaService import PublicMediaService


TEXT_PLATFORMS = ("twitter", "facebook", "bluesky")
IMAGE_ATTACHMENT_PLATFORMS = ("twitter", "facebook", "bluesky")
URL_MEDIA_PLATFORMS = ("instagram", "tiktok")
ALL_POSTING_PLATFORMS = TEXT_PLATFORMS + URL_MEDIA_PLATFORMS
HOSTABLE_IMAGE_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/gif", "image/webp"}
)
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
    def __init__(self, platform_service, global_config=None):
        self.platforms = platform_service
        self.jobs = PlatformJobService(platform_service.guild_config_dir / ".platform_jobs")
        self.media = MediaStagingService(platform_service.guild_config_dir / ".platform_media")
        self.public_media = PublicMediaService(
            global_config or {},
            platform_service.guild_config_dir,
        )

    async def queue(self, request: SocialPostRequest) -> SocialPostResult:
        selected = self._select_platforms(request)
        queued = []
        hosted_media = None
        for platform in selected:
            settings = self.platforms.effective_guild_platform(request.guild_id, platform)
            if settings.get("enabled") is not True:
                if request.platform != "all":
                    raise ValueError(f"{platform} is disabled for this server")
                continue
            if settings.get("connected") is not True:
                if request.platform != "all":
                    raise ValueError(
                        f"{platform} is enabled but not connected for this server"
                    )
                continue
            if settings.get("posting_enabled") is not True:
                if request.platform != "all":
                    raise ValueError(
                        f"{platform} is enabled but posting is disabled for this server"
                    )
                continue
            self._validate_text(
                platform,
                request.text,
                allow_empty=bool(request.attachments or request.media_url),
            )
            key = f"{request.guild_id}:{request.source_message_id}:{platform}"
            if request.attachments:
                if platform in URL_MEDIA_PLATFORMS:
                    if hosted_media is None:
                        hosted_media = await self.public_media.host_images(
                            request.guild_id,
                            request.attachments,
                            alt_text=request.text,
                            # Instagram accepts JPEG URLs, while TikTok accepts
                            # JPEG and WebP. JPEG is the safe common output.
                            output_content_type="image/jpeg",
                        )
                    self.jobs.enqueue(
                        request.guild_id,
                        platform,
                        "hosted_media_post",
                        {
                            "text": request.text,
                            "media": hosted_media,
                            "requested_by": request.requested_by,
                        },
                        idempotency_key=key,
                        source_message_id=request.source_message_id,
                    )
                    queued.append(platform)
                    continue
                staged = await self.media.stage_images(
                    platform,
                    request.attachments,
                    alt_text=request.text,
                )
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
            media = job.get("payload", {}).get("media")
            self.media.remove(media)
            self.public_media.remove(media)
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
            content_types = {
                str(getattr(item, "content_type", "") or "").casefold()
                for item in request.attachments
            }
            if selected == "all":
                selected_platforms = list(IMAGE_ATTACHMENT_PLATFORMS)
                if self.public_media.enabled:
                    selected_platforms.extend(
                        platform
                        for platform in URL_MEDIA_PLATFORMS
                        if content_types <= HOSTABLE_IMAGE_TYPES
                    )
                return tuple(selected_platforms)
            if selected not in ALL_POSTING_PLATFORMS:
                raise ValueError(f"{selected} cannot publish Discord image attachments")
            if (
                selected in URL_MEDIA_PLATFORMS
                and content_types - HOSTABLE_IMAGE_TYPES
            ):
                allowed = ", ".join(sorted(HOSTABLE_IMAGE_TYPES))
                raise ValueError(
                    f"{selected} hosted images accept these upload types: {allowed}"
                )
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
