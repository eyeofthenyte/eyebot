from __future__ import annotations

import inspect
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

from core.command_model import (
    CommandRequest,
    CommandResponse,
    ResponseAttachment,
    ResponseCard,
    ResponseField,
    ResponseMessage,
    ResponseVisibility,
)


ArgumentMode = Literal["none", "joined", "optional_joined", "variadic"]


@dataclass(frozen=True)
class PortableCommandSpec:
    cog_name: str
    method_name: str
    command: str
    aliases: tuple[str, ...] = ()
    argument_mode: ArgumentMode = "none"
    parameter_name: str | None = None
    delivery_flags: bool = False

    def __post_init__(self):
        if self.argument_mode in {"joined", "optional_joined"}:
            if not self.parameter_name:
                raise ValueError("Joined argument modes require parameter_name.")


class _CapturedDestination:
    def __init__(self, context: "NeutralCogContext"):
        self._context = context

    async def send(self, content=None, **kwargs):
        return await self._context.send(content, **kwargs)


class _NeutralMessage:
    def __init__(self, context: "NeutralCogContext"):
        self.author = context.author

    async def delete(self):
        return None


class NeutralCogContext:
    """Small Discord-context compatibility surface backed by neutral models."""

    def __init__(self, request: CommandRequest, bot):
        self.request = request
        self.bot = bot
        self.messages: list[ResponseMessage] = []
        self.author = _CapturedDestination(self)
        self.author.id = request.actor.id
        self.author.name = request.actor.username
        self.author.display_name = (
            request.actor.display_name or request.actor.username
        )
        self.author.roles = [
            SimpleNamespace(name=role) for role in request.actor.roles
        ]
        self.channel = SimpleNamespace(
            id=request.location.channel_id,
            name=request.location.channel_name,
        )
        self.guild = (
            SimpleNamespace(
                id=request.location.community_id,
                name=request.location.community_name,
                roles=[],
            )
            if request.location.community_id
            else None
        )
        self.message = _NeutralMessage(self)

    async def send(
        self,
        content=None,
        *,
        embed=None,
        file=None,
        files=None,
        **_kwargs,
    ):
        attachments = []
        for item in ([file] if file is not None else []) + list(files or []):
            attachment = _attachment_from_platform_file(item)
            if attachment is not None:
                attachments.append(attachment)
            close = getattr(item, "close", None)
            if callable(close):
                close()
        message = ResponseMessage(
            content=str(content) if content is not None else None,
            card=_card_from_platform_embed(embed) if embed is not None else None,
            attachments=tuple(attachments),
        )
        self.messages.append(message)
        return message

    def __str__(self):
        return self.author.display_name


def _color_value(color):
    value = getattr(color, "value", color)
    return value if isinstance(value, int) else None


def _card_from_platform_embed(embed) -> ResponseCard:
    footer = getattr(getattr(embed, "footer", None), "text", None)
    thumbnail = getattr(getattr(embed, "thumbnail", None), "url", None)
    author = getattr(getattr(embed, "author", None), "name", None)
    title = getattr(embed, "title", None) or author
    fields = tuple(
        ResponseField(
            name=str(getattr(field, "name", "")),
            value=str(getattr(field, "value", "")),
            inline=bool(getattr(field, "inline", False)),
        )
        for field in getattr(embed, "fields", ())
    )
    return ResponseCard(
        title=title,
        description=getattr(embed, "description", None),
        fields=fields,
        footer=footer,
        accent_color=_color_value(getattr(embed, "color", None)),
        thumbnail_url=thumbnail,
    )


def _attachment_from_platform_file(item) -> ResponseAttachment | None:
    fp = getattr(item, "fp", None)
    path = getattr(fp, "name", None)
    if not path and isinstance(fp, (str, Path)):
        path = str(fp)
    if not path:
        return None
    name = getattr(item, "filename", None) or Path(path).name
    media_type, _ = mimetypes.guess_type(name)
    return ResponseAttachment(name=name, path=str(path), media_type=media_type)


class LegacyCogHandler:
    """Expose an existing cog callback as a platform-neutral command handler."""

    def __init__(self, cog, spec: PortableCommandSpec):
        self.cog = cog
        self.spec = spec

    async def __call__(self, request: CommandRequest) -> CommandResponse:
        arguments = list(request.arguments)
        visibility = ResponseVisibility.PUBLIC
        if self.spec.delivery_flags and arguments:
            flag = arguments[-1].casefold()
            if flag == "-dm":
                visibility = ResponseVisibility.REQUESTER
                arguments.pop()
            elif flag == "-blind":
                visibility = ResponseVisibility.BLIND
                arguments.pop()

        context = NeutralCogContext(request, self.cog.bot)
        callback = getattr(self.cog, self.spec.method_name)
        callback = getattr(callback, "callback", callback)

        try:
            if self.spec.argument_mode == "none":
                result = callback(self.cog, context)
            elif self.spec.argument_mode == "variadic":
                result = callback(self.cog, context, *arguments)
            else:
                value = " ".join(arguments)
                if self.spec.argument_mode == "joined" and not value:
                    return CommandResponse.error(
                        f"Missing argument for {self.spec.command}.",
                        error_code="missing_argument",
                    )
                result = callback(
                    self.cog,
                    context,
                    **{self.spec.parameter_name: value or None},
                )
            if inspect.isawaitable(result):
                await result
        except Exception as error:
            logger = getattr(self.cog.bot, "logger", None)
            if logger is not None:
                logger.error(
                    f"Portable command '{self.spec.command}' failed: {error}"
                )
            return CommandResponse.error(
                f"Command failed: {error}",
                error_code="command_failed",
            )

        if not context.messages:
            return CommandResponse.error(
                f"Command '{self.spec.command}' produced no response.",
                error_code="empty_response",
            )
        return CommandResponse(
            messages=tuple(context.messages),
            visibility=visibility,
            metadata={"command": self.spec.command},
        )
