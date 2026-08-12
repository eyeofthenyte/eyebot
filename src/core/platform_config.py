from __future__ import annotations

from collections.abc import Mapping

from core.command_model import CommandPlatform


def is_platform_enabled(
    config: Mapping,
    platform: str | CommandPlatform,
    *,
    default: bool = False,
) -> bool:
    """Return a platform's explicit boolean enable state."""
    platform_name = (
        platform.value if isinstance(platform, CommandPlatform) else platform
    )
    platform_config = config.get(platform_name, {})
    if not isinstance(platform_config, Mapping):
        return default
    enabled = platform_config.get("enabled", default)
    return enabled if isinstance(enabled, bool) else default


def is_platform_available(
    config: Mapping,
    platform: str | CommandPlatform,
    *,
    default: bool = False,
) -> bool:
    """Return the host-level availability gate with legacy compatibility."""
    platform_name = platform.value if isinstance(platform, CommandPlatform) else platform
    settings = config.get(platform_name, {})
    if not isinstance(settings, Mapping):
        return default
    available = settings.get("available")
    if isinstance(available, bool):
        return available
    return is_platform_enabled(config, platform_name, default=default)
