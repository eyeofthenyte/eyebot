"""Route authenticated Kick chat events through EyeBot's portable commands."""

from __future__ import annotations

from adapters.kick_adapter import request_from_kick_chat_event, send_kick_response
from core.command_model import CommandParseError, CommandResponse
from services.tokenRefreshService import TokenRefreshService


class KickCommandService:
    def __init__(self, config, platform_service, command_router, replay_store, logger=None):
        self.config = config
        self.platforms = platform_service
        self.router = command_router
        self.replay_store = replay_store
        self.logger = logger
        self.tokens = TokenRefreshService(platform_service, logger)

    def _matching_guilds(self, event) -> tuple[str, ...]:
        if event.event_type != "chat.message.sent":
            return ()
        broadcaster = event.payload.get("broadcaster")
        if not isinstance(broadcaster, dict):
            return ()
        broadcaster_id = str(broadcaster.get("user_id") or "")
        if not broadcaster_id:
            return ()
        global_settings = self.platforms.platform("kick")
        if global_settings.get("available") is not True:
            return ()
        if global_settings.get("livestream_chat_commands_enabled") is not True:
            return ()
        matches = []
        for guild_id in sorted(self.platforms.discord_guilds()):
            settings = self.platforms.effective_guild_platform(guild_id, "kick")
            if settings.get("enabled") is not True:
                continue
            if settings.get("livestream_chat_commands_enabled") is not True:
                continue
            if settings.get("connected") is not True:
                continue
            if str(settings.get("broadcaster_user_id") or "") != broadcaster_id:
                continue
            configured_subscription = str(settings.get("chat_subscription_id") or "")
            if configured_subscription and configured_subscription != event.subscription_id:
                continue
            matches.append(str(guild_id))
        return tuple(matches)

    async def handle(self, event, headers, session) -> str:
        if event.event_type != "chat.message.sent":
            return "ignored_event"
        matches = self._matching_guilds(event)
        if not matches:
            return "unrouted"
        if len(matches) != 1:
            if self.logger:
                self.logger.error(
                    "Kick broadcaster maps to multiple chat-enabled guilds; "
                    "command ignored to prevent duplicate replies"
                )
            return "ambiguous"
        guild_id = matches[0]
        guild = self.platforms.discord_guilds().get(guild_id, {})
        prefix = str(guild.get("prefix") or self.config.get("prefix") or "!")
        poll = getattr(self.router, "poll_cog", None)
        payload = event.payload
        broadcaster = payload.get("broadcaster") if isinstance(payload, dict) else {}
        sender = payload.get("sender") if isinstance(payload, dict) else {}
        channel_id = str((broadcaster or {}).get("user_id") or "")
        actor_id = str((sender or {}).get("user_id") or "")
        content = str(payload.get("content") or "") if isinstance(payload, dict) else ""
        if poll is not None and poll.record_portable_vote(
            "kick", channel_id, actor_id, content
        ):
            return "processed_poll_vote"
        try:
            command_request = request_from_kick_chat_event(
                event.payload,
                prefix=prefix,
                headers=headers,
            )
        except CommandParseError:
            return "not_command"
        if self.router.canonical_name(command_request.command) is None:
            return "unknown_command"

        await self.tokens.refresh_guild(guild_id, "kick", session)
        settings = self.platforms.effective_guild_platform(guild_id, "kick")
        if poll is not None:
            async def send_poll_result(text):
                await send_kick_response(
                    session, settings, command_request, CommandResponse.text(text)
                )
            poll.bind_portable_destination("kick", channel_id, send_poll_result)
        response = await self.router.dispatch(command_request)
        sent_ids = await send_kick_response(
            session, settings, command_request, response
        )
        for message_id in sent_ids:
            try:
                self.replay_store.remember_message_id(message_id)
            except ValueError:
                pass
        if self.logger:
            self.logger.info(
                f"Processed Kick command {command_request.command} for guild {guild_id}",
                guild_id=guild_id,
            )
        return "processed"
