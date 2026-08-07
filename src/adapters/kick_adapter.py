"""Placeholder for Kick livestream chat."""

from adapters.platform_placeholder import PlatformAdapterPlaceholder
from core.command_model import CommandPlatform


KICK_ADAPTER = PlatformAdapterPlaceholder(
    platform=CommandPlatform.KICK,
    capabilities=("livestream_chat",),
)
