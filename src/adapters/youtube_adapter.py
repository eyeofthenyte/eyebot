"""Placeholder for YouTube uploads, community posts, and livestream chat."""

from adapters.platform_placeholder import PlatformAdapterPlaceholder
from core.command_model import CommandPlatform


YOUTUBE_ADAPTER = PlatformAdapterPlaceholder(
    platform=CommandPlatform.YOUTUBE,
    capabilities=("videos", "community_posts", "livestream_chat"),
)
