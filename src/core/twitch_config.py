"""Resolve Twitch connector settings without coupling them to TwitchIO."""

from __future__ import annotations

from collections.abc import Iterable, Mapping


def _channel_names(value) -> tuple[str, ...]:
    if isinstance(value, str):
        values: Iterable = (value,)
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        return ()

    normalized = []
    for item in values:
        if not isinstance(item, str):
            continue
        channel = item.strip().casefold().removeprefix("#")
        if channel and channel not in normalized:
            normalized.append(channel)
    return tuple(normalized)


def resolve_twitch_channels(config: Mapping, platform_service) -> tuple[str, ...]:
    """Return Twitch channels for a private or shared EyeBot installation.

    Private installations use only connector-wide ``twitch.channels``. Shared
    installations additionally join every ``twitch.channels`` entry selected
    by enabled Discord guilds. The legacy singular ``twitch.channel`` remains
    supported during migration.
    """
    twitch = config.get("twitch", {})
    twitch = twitch if isinstance(twitch, Mapping) else {}
    channels = list(_channel_names(twitch.get("channels", ())))

    # Missing or malformed mode values fail closed as a private installation.
    if config.get("private_install", True) is not False:
        return tuple(channels)

    for guild_id in sorted(platform_service.discord_guilds()):
        effective = platform_service.effective_guild_platform(guild_id, "twitch")
        if effective.get("enabled") is not True:
            continue
        selected = (
            *_channel_names(effective.get("channels")),
            *_channel_names(effective.get("channel")),
        )
        for channel in selected:
            if channel not in channels:
                channels.append(channel)
    return tuple(channels)
