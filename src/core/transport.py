from __future__ import annotations

from abc import ABC, abstractmethod

from core.command_model import CommandParseError, CommandRequest, CommandResponse
from core.command_router import CommandRouter


NON_DISCORD_ATTACHMENT_MARKER = "| Attachments:"


def strip_non_discord_attachment_suffix(content: str) -> str:
    """Remove Discord-only attachment details from portable chat output."""
    visible_content, marker, _attachment_details = content.partition(
        NON_DISCORD_ATTACHMENT_MARKER
    )
    return visible_content.rstrip() if marker else content


class CommandTransportAdapter(ABC):
    """Convert native chat events to and from the shared command models."""

    def __init__(self, router: CommandRouter, *, prefix: str = "!"):
        self.router = router
        self.prefix = prefix

    async def dispatch(self, native_message) -> bool:
        """Dispatch a portable command, returning whether it was handled."""
        try:
            request = self.to_request(native_message)
        except CommandParseError:
            return False

        if self.router.canonical_name(request.command) is None:
            return False

        response = await self.router.dispatch(request)
        await self.send_response(native_message, response)
        return True

    @abstractmethod
    def to_request(self, native_message) -> CommandRequest:
        """Convert a platform message into a neutral request."""

    @abstractmethod
    async def send_response(
        self,
        native_message,
        response: CommandResponse,
    ) -> None:
        """Render and deliver a neutral response on the source platform."""
