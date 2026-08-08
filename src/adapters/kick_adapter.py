"""Kick live-event adapter; chat awaits an approved transport contract."""

from adapters.platform_api_adapter import PlatformApiAdapter, PlatformCapabilityError
from core.command_model import CommandPlatform


class KickAdapter(PlatformApiAdapter):
    def __init__(self):
        super().__init__(CommandPlatform.KICK, ("live_events",))

    async def connect_chat(self, settings, handler):
        raise PlatformCapabilityError(
            "Kick chat requires the app's approved event/chat API contract; "
            "live-event polling is implemented, but chat is not enabled."
        )


KICK_ADAPTER = KickAdapter()
