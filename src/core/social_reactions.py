"""Platform-neutral selection of Discord social approval reactions."""

from __future__ import annotations


ATTACHMENT_PLATFORMS = frozenset({"twitter", "facebook", "bluesky"})
URL_MEDIA_PLATFORMS = frozenset({"instagram", "tiktok"})
HOSTED_IMAGE_TYPES = {
    "instagram": frozenset({"image/jpeg"}),
    "tiktok": frozenset({"image/jpeg", "image/webp"}),
}


def enabled_reaction_emojis(
    platform_service,
    guild_id,
    reaction_platforms,
    *,
    has_attachments=False,
    has_media_url=False,
    attachments_can_be_hosted=False,
    attachment_content_types=(),
):
    """Return actionable reactions for accounts ready to publish this message."""
    emojis = []
    for emoji, platform in reaction_platforms.items():
        if platform == "all":
            continue
        settings = platform_service.effective_guild_platform(guild_id, platform)
        if not (
            settings.get("enabled") is True
            and settings.get("connected") is True
            and settings.get("posting_enabled") is True
        ):
            continue
        if platform in ATTACHMENT_PLATFORMS and has_attachments:
            emojis.append(emoji)
        elif platform in URL_MEDIA_PLATFORMS:
            content_types = {str(value).casefold() for value in attachment_content_types}
            compatible_attachments = (
                has_attachments
                and attachments_can_be_hosted
                and content_types
                and content_types <= HOSTED_IMAGE_TYPES[platform]
            )
            if has_media_url or compatible_attachments:
                emojis.append(emoji)

    compatible_attachment_emojis = {
        emoji
        for emoji, platform in reaction_platforms.items()
        if platform in ATTACHMENT_PLATFORMS
        or (
            attachments_can_be_hosted
            and platform in URL_MEDIA_PLATFORMS
            and {str(value).casefold() for value in attachment_content_types}
            <= HOSTED_IMAGE_TYPES[platform]
        )
    }
    if has_attachments and len(compatible_attachment_emojis.intersection(emojis)) > 1:
        all_emoji = next(
            emoji
            for emoji, platform in reaction_platforms.items()
            if platform == "all"
        )
        emojis.append(all_emoji)
    return tuple(emojis)
