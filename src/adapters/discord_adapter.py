from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from pathlib import Path

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
from core.transport import CommandTransportAdapter


DestinationResolver = Callable[
    [object, CommandResponse],
    Iterable[object] | Awaitable[Iterable[object]],
]


def request_from_discord_message(message, *, prefix: str) -> CommandRequest:
    guild = getattr(message, "guild", None)
    channel = message.channel
    roles = tuple(
        role.name for role in getattr(message.author, "roles", ())
        if getattr(role, "name", None)
    )
    permissions = getattr(message.author, "guild_permissions", None)
    return CommandRequest.from_text(
        platform=CommandPlatform.DISCORD,
        surface=(
            CommandSurface.DIRECT_MESSAGE
            if guild is None
            else CommandSurface.CHANNEL
        ),
        actor=CommandActor(
            id=str(message.author.id),
            username=str(message.author),
            display_name=getattr(message.author, "display_name", None),
            roles=roles,
            metadata={
                "manage_guild": bool(
                    permissions and getattr(permissions, "manage_guild", False)
                ),
                "administrator": bool(
                    permissions and getattr(permissions, "administrator", False)
                ),
            },
        ),
        content=message.content,
        prefix=prefix,
        location=CommandLocation(
            channel_id=str(channel.id),
            channel_name=getattr(channel, "name", None),
            community_id=str(guild.id) if guild else None,
            community_name=getattr(guild, "name", None),
        ),
        metadata={"message_id": str(message.id)},
    )


def _discord_embed(card):
    import discord

    embed = discord.Embed(
        title=card.title,
        description=card.description,
        color=card.accent_color,
    )
    for field in card.fields:
        embed.add_field(
            name=field.name,
            value=field.value,
            inline=field.inline,
        )
    if card.footer:
        embed.set_footer(text=card.footer)
    if card.thumbnail_url:
        embed.set_thumbnail(url=card.thumbnail_url)
    return embed


async def _send_message(destination, message: ResponseMessage):
    kwargs = {}
    if message.card:
        kwargs["embed"] = _discord_embed(message.card)
    files = []
    if message.attachments:
        import discord

        files = [
            discord.File(Path(item.path), filename=item.name)
            for item in message.attachments
            if item.path
        ]
    if files:
        kwargs["files"] = files
    await destination.send(content=message.content, **kwargs)


async def send_discord_response(
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
        destinations = (source_message.author,)
    else:
        destinations = ()

    if not destinations:
        await source_message.author.send(
            "❌ No Discord destination is configured for this response."
        )
        return
    for destination in destinations:
        for message in response.messages:
            await _send_message(destination, message)


class DiscordTransportAdapter(CommandTransportAdapter):
    def __init__(
        self,
        router,
        *,
        prefix="!",
        prefix_resolver=None,
        destination_resolver: DestinationResolver | None = None,
    ):
        super().__init__(router, prefix=prefix)
        self.prefix_resolver = prefix_resolver
        self.destination_resolver = destination_resolver

    def to_request(self, native_message):
        prefix = (
            self.prefix_resolver(native_message)
            if self.prefix_resolver is not None
            else self.prefix
        )
        return request_from_discord_message(native_message, prefix=prefix)

    async def send_response(self, native_message, response):
        await send_discord_response(
            native_message,
            response,
            destination_resolver=self.destination_resolver,
        )
