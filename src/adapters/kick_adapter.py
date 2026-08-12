"""Kick API adapter and verified chat-webhook command conversion."""

from __future__ import annotations

from collections.abc import Mapping

from adapters.platform_api_adapter import PlatformApiAdapter, PlatformCapabilityError
from core.command_model import (
    CommandActor,
    CommandLocation,
    CommandParseError,
    CommandPlatform,
    CommandRequest,
    CommandSurface,
)


KICK_CHAT_EVENT = "chat.message.sent"


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


class KickAdapter(PlatformApiAdapter):
    def __init__(self):
        super().__init__(CommandPlatform.KICK, ("live_events",))

    async def connect_chat(self, settings, handler):
        raise PlatformCapabilityError(
            "Kick chat requires the app's approved event/chat API contract; "
            "live-event polling is implemented, but chat is not enabled."
        )


KICK_ADAPTER = KickAdapter()
