"""Placeholder for TikTok publishing."""

from adapters.platform_placeholder import PlatformAdapterPlaceholder
from core.command_model import CommandPlatform


TIKTOK_ADAPTER = PlatformAdapterPlaceholder(
    platform=CommandPlatform.TIKTOK,
    capabilities=("posting",),
)
