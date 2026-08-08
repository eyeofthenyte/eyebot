"""Ko-fi signed webhook capability descriptor."""

from adapters.platform_api_adapter import PlatformApiAdapter
from core.command_model import CommandPlatform


class KofiAdapter(PlatformApiAdapter):
    def __init__(self):
        super().__init__(CommandPlatform.KOFI, ("donations", "memberships", "shop_orders", "webhooks"))


KOFI_ADAPTER = KofiAdapter()
