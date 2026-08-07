"""Placeholder for Instagram publishing."""

from adapters.platform_placeholder import PlatformAdapterPlaceholder
from core.command_model import CommandPlatform


INSTAGRAM_ADAPTER = PlatformAdapterPlaceholder(
    platform=CommandPlatform.INSTAGRAM,
    capabilities=("posting",),
)
