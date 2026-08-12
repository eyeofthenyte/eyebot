"""Platform-neutral selection of Discord social approval reactions."""

from __future__ import annotations


ATTACHMENT_PLATFORMS = frozenset({"twitter", "facebook", "bluesky"})
URL_MEDIA_PLATFORMS = frozenset({"instagram", "tiktok"})


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
    """Return placeholders for enabled platforms supported by this message."""
    emojis = []
    for emoji, platform in reaction_platforms.items():
        if platform == "all":
            continue
        settings = platform_service.effective_guild_platform(guild_id, platform)
        if settings.get("enabled") is not True:
            continue
        if platform in ATTACHMENT_PLATFORMS and has_attachments:
            emojis.append(emoji)
        elif platform in URL_MEDIA_PLATFORMS and (has_attachments or has_media_url):
            emojis.append(emoji)

    if has_attachments and len(emojis) > 1:
        all_emoji = next(
            emoji
            for emoji, platform in reaction_platforms.items()
            if platform == "all"
        )
        emojis.append(all_emoji)
    return tuple(emojis)
