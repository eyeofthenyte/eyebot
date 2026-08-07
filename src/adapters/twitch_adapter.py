from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable

from core.command_model import (
    CommandActor,
    CommandLocation,
    CommandPlatform,
    CommandRequest,
    CommandResponse,
    CommandSurface,
    ResponseMessage,
    ResponseVisibility,
)
from core.transport import (
    CommandTransportAdapter,
    strip_non_discord_attachment_suffix,
)


TWITCH_MESSAGE_LIMIT = 500
SAFE_TWITCH_MESSAGE_LIMIT = 450

DestinationResolver = Callable[
    [object, CommandResponse],
    Iterable[object] | Awaitable[Iterable[object]],
]


def _first_value(value, *names):
    for name in names:
        found = getattr(value, name, None)
        if found is not None:
            return found
    return None


def _has_badge(tags, badge_name):
    badges = tags.get("badges", {})
    if isinstance(badges, dict):
        return badge_name in badges
    return any(
        badge.partition("/")[0] == badge_name
        for badge in str(badges).split(",")
    )


def request_from_twitch_message(message, *, prefix: str) -> CommandRequest:
    author = message.author
    channel = message.channel
    tags = dict(getattr(message, "tags", {}) or {})
    actor_id = _first_value(author, "id", "_id", "name")
    username = _first_value(author, "name", "display_name")
    channel_name = _first_value(channel, "name")
    channel_id = _first_value(channel, "id", "_id", "name")
    actor_id = actor_id or username
    channel_id = channel_id or channel_name
    roles = tuple(
        role
        for role, enabled in (
            ("broadcaster", _has_badge(tags, "broadcaster")),
            ("moderator", tags.get("mod") == "1"),
            ("subscriber", tags.get("subscriber") == "1"),
        )
        if enabled
    )
    return CommandRequest.from_text(
        platform=CommandPlatform.TWITCH,
        surface=CommandSurface.LIVESTREAM_CHAT,
        actor=CommandActor(
            id=str(actor_id),
            username=str(username),
            display_name=_first_value(author, "display_name", "name"),
            roles=roles,
            metadata={"tags": tags},
        ),
        content=message.content,
        prefix=prefix,
        location=CommandLocation(
            channel_id=str(channel_id),
            channel_name=str(channel_name),
            community_id=str(channel_id),
            community_name=str(channel_name),
            stream_id=tags.get("room-id"),
        ),
        metadata={"message_id": str(tags.get("id", ""))},
    )


def _flatten_message(message: ResponseMessage) -> str:
    sections = []
    if message.content:
        sections.append(message.content)
    if message.card:
        card = message.card
        if card.title:
            sections.append(card.title)
        if card.description:
            sections.append(card.description)
        sections.extend(
            f"{field.name}: {field.value}" for field in card.fields
        )
        if card.footer:
            sections.append(card.footer)
    flattened = " | ".join(
        part.strip() for part in sections if part and part.strip()
    )
    return strip_non_discord_attachment_suffix(flattened)


def split_twitch_text(
    content: str,
    *,
    limit: int = SAFE_TWITCH_MESSAGE_LIMIT,
) -> tuple[str, ...]:
    if limit < 1 or limit > TWITCH_MESSAGE_LIMIT:
        raise ValueError("Twitch message limit must be between 1 and 500.")
    remaining = content.strip()
    chunks = []
    while len(remaining) > limit:
        split_at = max(
            remaining.rfind(" ", 0, limit + 1),
            remaining.rfind("\n", 0, limit + 1),
        )
        if split_at <= 0:
            split_at = limit
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    if remaining:
        chunks.append(remaining)
    return tuple(chunks)


async def send_twitch_response(
    source_message,
    response: CommandResponse,
    *,
    destination_resolver: DestinationResolver | None = None,
):
    if destination_resolver is not None:
        destinations = destination_resolver(source_message, response)
        if hasattr(destinations, "__await__"):
            destinations = await destinations
        destinations = tuple(destinations)
    elif response.visibility == ResponseVisibility.PUBLIC:
        destinations = (source_message.channel,)
    elif response.visibility == ResponseVisibility.REQUESTER:
        private_send = getattr(source_message.author, "send", None)
        destinations = (source_message.author,) if callable(private_send) else ()
    else:
        destinations = ()

    if not destinations:
        await source_message.channel.send(
            f"@{source_message.author.name} this command requires a configured "
            "private or moderator destination."
        )
        return

    for destination in destinations:
        for message in response.messages:
            for chunk in split_twitch_text(_flatten_message(message)):
                await destination.send(chunk)


class TwitchTransportAdapter(CommandTransportAdapter):
    def __init__(
        self,
        router,
        *,
        prefix="!",
        destination_resolver: DestinationResolver | None = None,
    ):
        super().__init__(router, prefix=prefix)
        self.destination_resolver = destination_resolver

    def to_request(self, native_message):
        return request_from_twitch_message(native_message, prefix=self.prefix)

    async def send_response(self, native_message, response):
        await send_twitch_response(
            native_message,
            response,
            destination_resolver=self.destination_resolver,
        )
