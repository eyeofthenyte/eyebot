"""Placeholder for Ko-fi donation, membership, and shop webhooks."""

from adapters.platform_placeholder import PlatformAdapterPlaceholder
from core.command_model import CommandPlatform


KOFI_ADAPTER = PlatformAdapterPlaceholder(
    platform=CommandPlatform.KOFI,
    capabilities=("donations", "memberships", "shop_orders", "webhooks"),
)
