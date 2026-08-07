"""Placeholder for Bluesky publishing."""

from adapters.platform_placeholder import PlatformAdapterPlaceholder
from core.command_model import CommandPlatform


BLUESKY_ADAPTER = PlatformAdapterPlaceholder(
    platform=CommandPlatform.BLUESKY,
    capabilities=("posting",),
)
