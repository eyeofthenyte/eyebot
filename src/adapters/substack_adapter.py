"""Placeholder for Substack newsletter and podcast retrieval."""

from adapters.platform_placeholder import PlatformAdapterPlaceholder
from core.command_model import CommandPlatform


SUBSTACK_ADAPTER = PlatformAdapterPlaceholder(
    platform=CommandPlatform.SUBSTACK,
    capabilities=("newsletters", "podcasts"),
)
