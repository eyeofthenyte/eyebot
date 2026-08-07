from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable

from core.command_model import CommandRequest, CommandResponse


CommandHandler = Callable[
    [CommandRequest],
    CommandResponse | Awaitable[CommandResponse],
]


class CommandRouter:
    """Platform-independent mapping from normalized command names to handlers."""

    COMMAND_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

    def __init__(self):
        self._handlers: dict[str, CommandHandler] = {}
        self._canonical_names: dict[str, str] = {}

    @classmethod
    def normalize_name(cls, name: str) -> str:
        normalized = name.strip().casefold()
        if not cls.COMMAND_NAME.fullmatch(normalized):
            raise ValueError(
                "Command names must start with a letter or number and contain "
                "only letters, numbers, underscores, or hyphens."
            )
        return normalized

    def register(
        self,
        name: str,
        handler: CommandHandler,
        *,
        aliases: tuple[str, ...] = (),
    ) -> None:
        canonical = self.normalize_name(name)
        names = (canonical,) + tuple(
            self.normalize_name(alias) for alias in aliases
        )
        duplicate = next((item for item in names if item in self._handlers), None)
        if duplicate:
            raise ValueError(f"Command or alias '{duplicate}' is already registered.")
        for item in names:
            self._handlers[item] = handler
            self._canonical_names[item] = canonical

    def command(self, name: str, *, aliases: tuple[str, ...] = ()):
        def decorator(handler: CommandHandler):
            self.register(name, handler, aliases=aliases)
            return handler

        return decorator

    async def dispatch(self, request: CommandRequest) -> CommandResponse:
        handler = self._handlers.get(request.command)
        if handler is None:
            return CommandResponse.error(
                f"Unknown command: {request.command}",
                error_code="command_not_found",
            )
        response = handler(request)
        if inspect.isawaitable(response):
            response = await response
        if not isinstance(response, CommandResponse):
            raise TypeError("Command handlers must return CommandResponse.")
        return response

    def canonical_name(self, name: str) -> str | None:
        return self._canonical_names.get(name.strip().casefold())

    @property
    def registered_commands(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                name
                for name, canonical in self._canonical_names.items()
                if name == canonical
            )
        )
