"""Placeholder for Facebook publishing and livestream chat."""

from adapters.platform_placeholder import PlatformAdapterPlaceholder
from core.command_model import CommandPlatform


FACEBOOK_ADAPTER = PlatformAdapterPlaceholder(
    platform=CommandPlatform.FACEBOOK,
    capabilities=("posting", "livestream_chat"),
)
