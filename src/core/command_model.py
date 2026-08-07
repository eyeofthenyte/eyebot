from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class CommandParseError(ValueError):
    """Raised when incoming platform text is not a valid bot command."""


class CommandPlatform(str, Enum):
    GENERIC = "generic"
    DISCORD = "discord"
    TWITCH = "twitch"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    KICK = "kick"
    TWITTER = "twitter"
    BLUESKY = "bluesky"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    SUBSTACK = "substack"
    KOFI = "kofi"


class CommandSurface(str, Enum):
    CHANNEL = "channel"
    DIRECT_MESSAGE = "direct_message"
    LIVESTREAM_CHAT = "livestream_chat"
    WHISPER = "whisper"
    SYSTEM = "system"


class ResponseVisibility(str, Enum):
    PUBLIC = "public"
    REQUESTER = "requester"
    MODERATORS = "moderators"
    BLIND = "blind"


class CommandStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


@dataclass(frozen=True)
class CommandActor:
    id: str
    username: str
    display_name: str | None = None
    roles: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "roles": list(self.roles),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> CommandActor:
        return cls(
            id=str(value["id"]),
            username=str(value["username"]),
            display_name=value.get("display_name"),
            roles=tuple(str(role) for role in value.get("roles", ())),
            metadata=dict(value.get("metadata", {})),
        )


@dataclass(frozen=True)
class CommandLocation:
    channel_id: str | None = None
    channel_name: str | None = None
    community_id: str | None = None
    community_name: str | None = None
    stream_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "community_id": self.community_id,
            "community_name": self.community_name,
            "stream_id": self.stream_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> CommandLocation:
        return cls(
            channel_id=value.get("channel_id"),
            channel_name=value.get("channel_name"),
            community_id=value.get("community_id"),
            community_name=value.get("community_name"),
            stream_id=value.get("stream_id"),
            metadata=dict(value.get("metadata", {})),
        )


@dataclass(frozen=True)
class CommandRequest:
    platform: CommandPlatform
    surface: CommandSurface
    actor: CommandActor
    command: str
    arguments: tuple[str, ...] = ()
    raw_content: str = ""
    prefix: str = "!"
    location: CommandLocation = field(default_factory=CommandLocation)
    request_id: str = field(default_factory=lambda: str(uuid4()))
    received_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        normalized = self.command.strip().casefold()
        if not normalized:
            raise CommandParseError("Command name cannot be empty.")
        object.__setattr__(self, "command", normalized)
        if self.received_at.tzinfo is None:
            raise ValueError("received_at must include timezone information.")

    @classmethod
    def from_text(
        cls,
        *,
        platform: CommandPlatform,
        surface: CommandSurface,
        actor: CommandActor,
        content: str,
        prefix: str = "!",
        location: CommandLocation | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> CommandRequest:
        if not prefix:
            raise CommandParseError("Command prefix cannot be empty.")
        stripped = content.strip()
        if not stripped.startswith(prefix):
            raise CommandParseError("Message does not start with the command prefix.")

        command_text = stripped[len(prefix):].strip()
        if not command_text:
            raise CommandParseError("Command name cannot be empty.")
        try:
            tokens = shlex.split(command_text)
        except ValueError as error:
            raise CommandParseError(f"Invalid command quoting: {error}") from error
        if not tokens:
            raise CommandParseError("Command name cannot be empty.")

        return cls(
            platform=platform,
            surface=surface,
            actor=actor,
            command=tokens[0],
            arguments=tuple(tokens[1:]),
            raw_content=content,
            prefix=prefix,
            location=location or CommandLocation(),
            metadata=dict(metadata or {}),
        )

    @property
    def argument_text(self) -> str:
        return " ".join(self.arguments)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "platform": self.platform.value,
            "surface": self.surface.value,
            "actor": self.actor.to_dict(),
            "location": self.location.to_dict(),
            "command": self.command,
            "arguments": list(self.arguments),
            "raw_content": self.raw_content,
            "prefix": self.prefix,
            "received_at": self.received_at.isoformat(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> CommandRequest:
        return cls(
            request_id=str(value["request_id"]),
            platform=CommandPlatform(value["platform"]),
            surface=CommandSurface(value["surface"]),
            actor=CommandActor.from_dict(value["actor"]),
            location=CommandLocation.from_dict(value.get("location", {})),
            command=str(value["command"]),
            arguments=tuple(str(item) for item in value.get("arguments", ())),
            raw_content=str(value.get("raw_content", "")),
            prefix=str(value.get("prefix", "!")),
            received_at=datetime.fromisoformat(value["received_at"]),
            metadata=dict(value.get("metadata", {})),
        )


@dataclass(frozen=True)
class ResponseField:
    name: str
    value: str
    inline: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "value": self.value, "inline": self.inline}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ResponseField:
        return cls(
            name=str(value["name"]),
            value=str(value["value"]),
            inline=bool(value.get("inline", False)),
        )


@dataclass(frozen=True)
class ResponseCard:
    title: str | None = None
    description: str | None = None
    fields: tuple[ResponseField, ...] = ()
    footer: str | None = None
    accent_color: int | None = None
    thumbnail_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "fields": [item.to_dict() for item in self.fields],
            "footer": self.footer,
            "accent_color": self.accent_color,
            "thumbnail_url": self.thumbnail_url,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ResponseCard:
        return cls(
            title=value.get("title"),
            description=value.get("description"),
            fields=tuple(
                ResponseField.from_dict(item)
                for item in value.get("fields", ())
            ),
            footer=value.get("footer"),
            accent_color=value.get("accent_color"),
            thumbnail_url=value.get("thumbnail_url"),
        )


@dataclass(frozen=True)
class ResponseAttachment:
    name: str
    path: str | None = None
    url: str | None = None
    media_type: str | None = None

    def __post_init__(self):
        if not self.path and not self.url:
            raise ValueError("An attachment requires a path or URL.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "url": self.url,
            "media_type": self.media_type,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ResponseAttachment:
        return cls(
            name=str(value["name"]),
            path=value.get("path"),
            url=value.get("url"),
            media_type=value.get("media_type"),
        )


@dataclass(frozen=True)
class ResponseMessage:
    content: str | None = None
    card: ResponseCard | None = None
    attachments: tuple[ResponseAttachment, ...] = ()

    def __post_init__(self):
        if not self.content and self.card is None and not self.attachments:
            raise ValueError("A response message cannot be empty.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "card": self.card.to_dict() if self.card else None,
            "attachments": [item.to_dict() for item in self.attachments],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ResponseMessage:
        card = value.get("card")
        return cls(
            content=value.get("content"),
            card=ResponseCard.from_dict(card) if card else None,
            attachments=tuple(
                ResponseAttachment.from_dict(item)
                for item in value.get("attachments", ())
            ),
        )


@dataclass(frozen=True)
class CommandResponse:
    messages: tuple[ResponseMessage, ...]
    visibility: ResponseVisibility = ResponseVisibility.PUBLIC
    status: CommandStatus = CommandStatus.SUCCESS
    error_code: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.messages:
            raise ValueError("A command response requires at least one message.")
        if self.status == CommandStatus.SUCCESS and self.error_code:
            raise ValueError("Successful responses cannot have an error code.")

    @classmethod
    def text(
        cls,
        content: str,
        *,
        visibility: ResponseVisibility = ResponseVisibility.PUBLIC,
        metadata: Mapping[str, Any] | None = None,
    ) -> CommandResponse:
        return cls(
            messages=(ResponseMessage(content=content),),
            visibility=visibility,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def error(
        cls,
        content: str,
        *,
        error_code: str,
        visibility: ResponseVisibility = ResponseVisibility.REQUESTER,
    ) -> CommandResponse:
        return cls(
            messages=(ResponseMessage(content=content),),
            visibility=visibility,
            status=CommandStatus.ERROR,
            error_code=error_code,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "messages": [item.to_dict() for item in self.messages],
            "visibility": self.visibility.value,
            "status": self.status.value,
            "error_code": self.error_code,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> CommandResponse:
        return cls(
            messages=tuple(
                ResponseMessage.from_dict(item)
                for item in value.get("messages", ())
            ),
            visibility=ResponseVisibility(value["visibility"]),
            status=CommandStatus(value["status"]),
            error_code=value.get("error_code"),
            metadata=dict(value.get("metadata", {})),
        )
