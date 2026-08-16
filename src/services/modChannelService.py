import re

import discord


USER_MENTION_RE = re.compile(r"<@!?(\d+)>")


class ModChannelHandler:
    """Send moderator-channel messages without mentioning Discord users."""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def username(user) -> str:
        """Return a readable username without Discord mention markup."""
        return str(
            getattr(user, "name", None)
            or getattr(user, "display_name", None)
            or getattr(user, "id", "Unknown user")
        )

    def sanitize_text(self, guild, value):
        if not isinstance(value, str) or not value:
            return value

        def replace(match):
            user_id = int(match.group(1))
            member = guild.get_member(user_id) if guild is not None else None
            if member is None:
                user = self.bot.get_user(user_id) if self.bot is not None else None
                member = user
            return self.username(member) if member is not None else f"user-{user_id}"

        return USER_MENTION_RE.sub(replace, value)

    def sanitize_embed(self, guild, embed):
        if embed is None:
            return None

        def sanitize(value):
            if isinstance(value, str):
                return self.sanitize_text(guild, value)
            if isinstance(value, list):
                return [sanitize(item) for item in value]
            if isinstance(value, dict):
                return {key: sanitize(item) for key, item in value.items()}
            return value

        return discord.Embed.from_dict(sanitize(embed.to_dict()))

    def configured_channel(self, guild):
        if guild is None:
            return None
        service = getattr(self.bot, "platform_config_service", None)
        if service is None:
            return None
        guild_config = service.discord_guilds().get(str(guild.id), {})
        channel_id = guild_config.get("mod_channel")
        try:
            channel_id = int(channel_id)
        except (TypeError, ValueError):
            return None
        return guild.get_channel(channel_id)

    async def send(self, guild, *, channel=None, content=None, embed=None, **kwargs):
        """Send sanitized content to a guild's designated moderator channel."""
        destination = channel or self.configured_channel(guild)
        if destination is None:
            return None

        if content is not None:
            content = self.sanitize_text(guild, content)
        if embed is not None:
            embed = self.sanitize_embed(guild, embed)

        # Prevent user, role, and everyone notifications even if a future caller
        # passes mention syntax that this handler does not need to display.
        kwargs["allowed_mentions"] = discord.AllowedMentions.none()
        return await destination.send(content=content, embed=embed, **kwargs)
