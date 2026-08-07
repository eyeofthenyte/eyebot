"""Placeholder for Twitter/X publishing."""

from adapters.platform_placeholder import PlatformAdapterPlaceholder
from core.command_model import CommandPlatform


TWITTER_ADAPTER = PlatformAdapterPlaceholder(
    platform=CommandPlatform.TWITTER,
    capabilities=("posting",),
)
