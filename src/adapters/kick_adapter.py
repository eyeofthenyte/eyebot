"""Kick API adapter and verified chat-webhook command conversion."""

from __future__ import annotations

from collections.abc import Mapping

from adapters.platform_api_adapter import PlatformApiAdapter
from core.command_model import (
    CommandActor,
    CommandLocation,
    CommandParseError,
    CommandPlatform,
    CommandRequest,
    CommandSurface,
    CommandResponse,
    ResponseMessage,
    ResponseVisibility,
)
from core.transport import strip_non_discord_attachment_suffix


KICK_CHAT_EVENT = "chat.message.sent"
KICK_CHAT_URL = "https://api.kick.com/public/v1/chat"
KICK_MESSAGE_LIMIT = 500
SAFE_KICK_MESSAGE_LIMIT = 450


def _mapping(value, field_name: str) -> Mapping:
    if not isinstance(value, Mapping):
        raise CommandParseError(f"Kick chat payload is missing `{field_name}`.")
    return value


def _identity_roles(sender: Mapping, broadcaster: Mapping) -> tuple[str, ...]:
    roles = []
    sender_id = str(sender.get("user_id") or "")
    broadcaster_id = str(broadcaster.get("user_id") or "")
    if sender_id and sender_id == broadcaster_id:
        roles.append("broadcaster")

    identity = sender.get("identity")
    badges = identity.get("badges", ()) if isinstance(identity, Mapping) else ()
    if isinstance(badges, (list, tuple)):
        badge_types = {
            str(badge.get("type") or "").strip().casefold()
            for badge in badges
            if isinstance(badge, Mapping)
        }
        for role, accepted_types in (
            ("moderator", {"moderator", "mod"}),
            ("subscriber", {"subscriber", "sub"}),
        ):
            if badge_types & accepted_types:
                roles.append(role)
    return tuple(roles)


def request_from_kick_chat_event(
    payload: Mapping,
    *,
    prefix: str,
    headers: Mapping | None = None,
) -> CommandRequest:
    """Convert a verified Kick ``chat.message.sent`` payload to a command.

    Signature verification deliberately belongs to the HTTPS gateway. Callers
    must invoke this converter only after authenticating the raw webhook body.
    """
    event_headers = {str(key).casefold(): value for key, value in (headers or {}).items()}
    event_type = str(event_headers.get("kick-event-type") or KICK_CHAT_EVENT)
    if event_type != KICK_CHAT_EVENT:
        raise CommandParseError("Kick event is not a chat message.")
    if not isinstance(payload, Mapping):
        raise CommandParseError("Kick chat payload must be an object.")

    sender = _mapping(payload.get("sender"), "sender")
    broadcaster = _mapping(payload.get("broadcaster"), "broadcaster")
    sender_id = sender.get("user_id")
    username = str(sender.get("username") or sender.get("channel_slug") or "").strip()
    content = payload.get("content")
    channel_id = broadcaster.get("user_id")
    channel_name = str(
        broadcaster.get("channel_slug") or broadcaster.get("username") or ""
    ).strip()
    if sender.get("is_anonymous") is True or sender_id in (None, "") or not username:
        raise CommandParseError("Anonymous Kick chat messages cannot run commands.")
    if not isinstance(content, str):
        raise CommandParseError("Kick chat payload is missing text content.")
    if channel_id in (None, "") or not channel_name:
        raise CommandParseError("Kick chat payload is missing its broadcaster.")

    message_id = str(
        payload.get("message_id")
        or event_headers.get("kick-event-message-id")
        or ""
    )
    subscription_id = str(event_headers.get("kick-event-subscription-id") or "")
    return CommandRequest.from_text(
        platform=CommandPlatform.KICK,
        surface=CommandSurface.LIVESTREAM_CHAT,
        actor=CommandActor(
            id=str(sender_id),
            username=username,
            display_name=username,
            roles=_identity_roles(sender, broadcaster),
            metadata={
                "is_verified": bool(sender.get("is_verified")),
                "channel_slug": str(sender.get("channel_slug") or ""),
                "profile_picture": str(sender.get("profile_picture") or ""),
            },
        ),
        content=content,
        prefix=prefix,
        location=CommandLocation(
            channel_id=str(channel_id),
            channel_name=channel_name,
            community_id=str(channel_id),
            community_name=str(broadcaster.get("username") or channel_name),
            metadata={"channel_slug": channel_name},
        ),
        metadata={
            "event_type": event_type,
            "event_version": str(event_headers.get("kick-event-version") or "1"),
            "message_id": message_id,
            "subscription_id": subscription_id,
            "created_at": str(payload.get("created_at") or ""),
            "replies_to": payload.get("replies_to"),
        },
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
        sections.extend(f"{field.name}: {field.value}" for field in card.fields)
        if card.footer:
            sections.append(card.footer)
    return strip_non_discord_attachment_suffix(
        " | ".join(str(section).strip() for section in sections if str(section).strip())
    )


def split_kick_text(content: str, *, limit: int = SAFE_KICK_MESSAGE_LIMIT) -> tuple[str, ...]:
    if not 1 <= limit <= KICK_MESSAGE_LIMIT:
        raise ValueError("Kick message limit must be between 1 and 500")
    remaining = content.strip()
    chunks = []
    while len(remaining) > limit:
        split_at = max(remaining.rfind(" ", 0, limit + 1), remaining.rfind("\n", 0, limit + 1))
        if split_at <= 0:
            split_at = limit
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    if remaining:
        chunks.append(remaining)
    return tuple(chunks)


async def send_kick_response(session, settings, request, response: CommandResponse) -> tuple[str, ...]:
    if response.visibility != ResponseVisibility.PUBLIC:
        return ()
    token = str(settings.get("access_token") or "")
    if not token:
        raise ValueError("Kick access token is unavailable")
    sent_ids = []
    for message in response.messages:
        for chunk in split_kick_text(_flatten_message(message)):
            payload = {"content": chunk, "type": "bot"}
            reply_id = str(request.metadata.get("message_id") or "")
            if reply_id:
                payload["reply_to_message_id"] = reply_id
            async with session.post(
                KICK_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as http_response:
                body = await http_response.json(content_type=None)
                if not 200 <= http_response.status < 300:
                    message_text = body.get("message") if isinstance(body, Mapping) else None
                    raise ValueError(
                        f"Kick chat API returned HTTP {http_response.status}: "
                        f"{message_text or 'request failed'}"
                    )
            result = body.get("data", {}) if isinstance(body, Mapping) else {}
            message_id = str(result.get("message_id") or "")
            if message_id:
                sent_ids.append(message_id)
    return tuple(sent_ids)


class KickAdapter(PlatformApiAdapter):
    def __init__(self):
        super().__init__(CommandPlatform.KICK, ("live_events", "livestream_chat"))

KICK_ADAPTER = KickAdapter()
