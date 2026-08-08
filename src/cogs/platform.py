"""Discord administration for per-guild platform overrides."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from urllib.parse import quote
from urllib.parse import urlparse

import discord
from discord.ext import commands
from core.platform_setup_instructions import (
    PLATFORM_ORDER,
    render_setup_instructions,
    split_markdown_messages,
)
from core.oauth_provider import OAUTH_PROVIDERS
from services.oauthStateService import OAuthStateService, resolve_oauth_state_key
from services.platformConnectionService import PlatformConnectionService


MAX_VALUE_LENGTH = 500
MAX_LIST_ITEMS = 100
PLATFORM_NAMES = (
    "discord",
    "twitch",
    "youtube",
    "facebook",
    "kick",
    "twitter",
    "bluesky",
    "tiktok",
    "instagram",
    "substack",
    "kofi",
)
SOCIAL_SOURCE_PLATFORMS = frozenset({"twitter", "facebook", "bluesky"})
SECRET_PARAMETERS = frozenset(
    {
        "access_token",
        "access_token_secret",
        "api_key",
        "api_secret",
        "app_password",
        "app_secret",
        "bearer_token",
        "bot_token",
        "client_id",
        "client_key",
        "client_secret",
        "credential",
        "email",
        "refresh_token",
        "tmi_token",
        "verification_token",
    }
)
TRUE_VALUES = frozenset({"1", "true", "yes", "on", "enable", "enabled"})
FALSE_VALUES = frozenset({"0", "false", "no", "off", "disable", "disabled"})
DISCORD_CHANNEL_PATTERN = re.compile(
    r"^(?:<#([1-9][0-9]{14,19})>|([1-9][0-9]{14,19}))$"
)
CHANNEL_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,25}$")
SLUG_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,49}$")
DISCORD_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,99}$")
YOUTUBE_CHANNEL_PATTERN = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
HANDLE_LABEL_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class PlatformValueError(ValueError):
    """A user-supplied platform value failed validation."""


@dataclass(frozen=True)
class ParameterRule:
    kind: str
    description: str


def _rules(*, ids=(), booleans=(), channels=(), names=(), urls=()) -> dict:
    selected = {}
    selected.update({name: ParameterRule("numeric_id", "numeric platform identifier") for name in ids})
    selected.update({name: ParameterRule("bool", "true or false") for name in booleans})
    selected.update(
        {name: ParameterRule("discord_channel", "Discord channel ID or mention") for name in channels}
    )
    selected.update({name: ParameterRule("name", "account or channel name") for name in names})
    selected.update({name: ParameterRule("url", "HTTPS URL") for name in urls})
    return selected


PLATFORM_RULES = {
    "discord": {
        "enabled": ParameterRule("bool", "true or false"),
        "mod_channel_name": ParameterRule("discord_name", "Discord channel name"),
    },
    "twitch": {
        "enabled": ParameterRule("bool", "true or false"),
        "nick": ParameterRule("twitch_name", "Twitch login name"),
        "channel": ParameterRule("twitch_name", "Twitch channel login name"),
        "destination_channel": ParameterRule(
            "discord_channel",
            "Discord channel ID or mention for Twitch go-live posts",
        ),
    },
    "youtube": {
        **_rules(
            booleans=(
                "enabled",
                "videos_enabled",
                "community_posts_enabled",
                "livestream_chat_commands_enabled",
            ),
            channels=("destination_channel",),
        ),
        "channel_id": ParameterRule("youtube_channel", "YouTube UC channel ID"),
    },
    "facebook": _rules(
        ids=("page_id",),
        booleans=("enabled", "posting_enabled", "livestream_chat_commands_enabled"),
        channels=("destination_channel",),
    ),
    "kick": _rules(
        booleans=("enabled", "livestream_chat_commands_enabled"),
        channels=("destination_channel",),
        names=("channel",),
    ),
    "twitter": _rules(
        ids=("user_id",),
        booleans=("enabled", "posting_enabled"),
        channels=("destination_channel",),
    ),
    "bluesky": {
        **_rules(booleans=("enabled", "posting_enabled")),
        "handle": ParameterRule("bluesky_handle", "DNS-style Bluesky handle"),
    },
    "tiktok": _rules(
        booleans=("enabled", "posting_enabled"),
        channels=("destination_channel",),
    ),
    "instagram": _rules(
        ids=("account_id",),
        booleans=("enabled", "posting_enabled"),
        channels=("destination_channel",),
    ),
    "substack": _rules(
        booleans=("enabled", "newsletters_enabled", "podcasts_enabled"),
        channels=("destination_channel",),
        urls=("publication_url",),
    ),
    "kofi": {
        **_rules(
            booleans=(
                "enabled",
                "donations_enabled",
                "memberships_enabled",
                "shop_orders_enabled",
                "webhooks_enabled",
            ),
            channels=("destination_channel",),
        ),
        "page_url": ParameterRule("kofi_url", "HTTPS ko-fi.com page URL"),
    },
}


def _validate_url(value: str, *, hostname: str | None = None) -> str:
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise PlatformValueError("must be an HTTPS URL without credentials or a fragment")
    if hostname and parsed.hostname.casefold() not in {hostname, f"www.{hostname}"}:
        raise PlatformValueError(f"must use the {hostname} domain")
    if len(value) > MAX_VALUE_LENGTH:
        raise PlatformValueError(f"must be at most {MAX_VALUE_LENGTH} characters")
    return value


def _validate_bluesky_handle(value: str) -> str:
    handle = value.casefold().removeprefix("@")
    if len(handle) > 253 or "." not in handle:
        raise PlatformValueError("must be a DNS-style handle such as name.bsky.social")
    labels = handle.split(".")
    if any(not HANDLE_LABEL_PATTERN.fullmatch(label) for label in labels):
        raise PlatformValueError("contains an invalid DNS label")
    return handle


def validate_parameter_value(rule: ParameterRule, raw_value: str):
    """Validate and normalize a guild-scoped platform value."""
    value = raw_value.strip()
    if not value:
        raise PlatformValueError("cannot be empty")
    if len(value) > MAX_VALUE_LENGTH:
        raise PlatformValueError(f"must be at most {MAX_VALUE_LENGTH} characters")

    if rule.kind == "bool":
        normalized = value.casefold()
        if normalized in TRUE_VALUES:
            return True
        if normalized in FALSE_VALUES:
            return False
        raise PlatformValueError("must be true/false, yes/no, on/off, or 1/0")
    if rule.kind == "discord_channel":
        match = DISCORD_CHANNEL_PATTERN.fullmatch(value)
        if not match:
            raise PlatformValueError("must be a Discord channel ID or channel mention")
        return match.group(1) or match.group(2)
    if rule.kind == "youtube_channel":
        if not YOUTUBE_CHANNEL_PATTERN.fullmatch(value):
            raise PlatformValueError("must be a 24-character YouTube channel ID beginning with UC")
        return value
    if rule.kind == "numeric_id":
        if not value.isascii() or not value.isdigit() or not 5 <= len(value) <= 30:
            raise PlatformValueError("must be a 5-30 digit platform identifier")
        return value
    if rule.kind == "twitch_name":
        if not CHANNEL_NAME_PATTERN.fullmatch(value):
            raise PlatformValueError("must be a 3-25 character Twitch login name")
        return value.casefold()
    if rule.kind == "twitch_list":
        values = [item.strip().casefold().removeprefix("#") for item in value.split(",")]
        values = list(dict.fromkeys(values))
        if not values or len(values) > MAX_LIST_ITEMS:
            raise PlatformValueError(f"must contain 1-{MAX_LIST_ITEMS} channel names")
        invalid = [item for item in values if not CHANNEL_NAME_PATTERN.fullmatch(item)]
        if invalid:
            raise PlatformValueError(f"contains an invalid Twitch channel: {invalid[0]}")
        return values
    if rule.kind == "discord_name":
        name = value.casefold()
        if not DISCORD_NAME_PATTERN.fullmatch(name):
            raise PlatformValueError("must be a 1-100 character lowercase Discord channel name")
        return name
    if rule.kind == "name":
        if not SLUG_PATTERN.fullmatch(value):
            raise PlatformValueError("must be a 2-50 character account or channel name")
        return value.casefold()
    if rule.kind == "bluesky_handle":
        return _validate_bluesky_handle(value)
    if rule.kind == "url":
        return _validate_url(value)
    if rule.kind == "kofi_url":
        return _validate_url(value, hostname="ko-fi.com")
    raise PlatformValueError("uses an unsupported value type")


def available_parameters(platform_name: str) -> str:
    return ", ".join(f"`{name}`" for name in PLATFORM_RULES[platform_name])


class Platform(commands.Cog):
    """Manage validated platform settings for the current Discord guild."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="platform",
        extras=[
            "🌐  **__Platform Settings__**",
            "**Usage:** `!platform <platform> set <parameter> <value>`\n"
            "`!platform <platform> default <parameter|all>`\n\n"
            "`!platform <platform> <enable|disable>`\n\n"
            "`!platform <platform> <connect|disconnect>`\n\n"
            "`!platform <platform|all> instructions`\n\n"
            "In a DM with multiple managed servers, prefix the command with "
            "the guild ID: `!platform <guild_id> <platform> ...`\n\n"
            "Platforms: discord, twitch, youtube, facebook, kick, twitter, "
            "bluesky, tiktok, instagram, substack, kofi.\n"
            "Requires the Manage Server permission. Credentials and tokens "
            "must be stored with the host-side manage_secrets.py tool.",
        ],
    )
    async def platform_command(
        self,
        ctx,
        platform_name: str | None = None,
        action: str | None = None,
        parameter: str | None = None,
        *,
        value: str | None = None,
    ):
        """Set or reset a server platform setting.

        Usage: !platform <platform> set <parameter> <value>
               !platform <platform> default <parameter|all>
               !platform <platform> <enable|disable>
               !platform <platform> <connect|disconnect>
               !platform <platform|all> instructions
        DM:    !platform <guild_id> <platform> <action> ...

        The default action removes the server override so it inherits the
        platform-wide value from platforms.yaml. Requires Manage Server.
        Authentication credentials cannot be entered through Discord.
        """
        service = self._service()
        if service is None:
            return await ctx.send("❌ Per-server configuration is unavailable.")

        resolved = await self._resolve_target(
            ctx,
            platform_name,
            action,
            parameter,
            value,
        )
        if resolved is None:
            return
        target_guild, platform_name, action, parameter, value = resolved

        if not self._can_manage(target_guild, ctx.author):
            return await ctx.send(
                "❌ You need the Manage Server permission in the selected server."
            )
        if ctx.guild is not None:
            await self._delete_invocation(ctx)

        selected_platform = (platform_name or "").casefold()
        selected_action = (action or "").casefold()
        if selected_platform == "instructions" and not selected_action:
            selected_platform = "all"
            selected_action = "instructions"
        if selected_action == "instructions":
            if selected_platform not in {*PLATFORM_RULES, "all"}:
                return await ctx.send(
                    "❌ Select a platform or `all`: "
                    + ", ".join(PLATFORM_NAMES)
                    + "."
                )
            if parameter is not None or value is not None:
                return await ctx.send(
                    "❌ `instructions` does not accept a parameter or value."
                )
            return await self._send_setup_instructions(
                ctx,
                service,
                target_guild,
                selected_platform,
            )

        if ctx.guild is not None:
            if not await self._require_mod_channel(ctx, service, target_guild):
                return

        if selected_platform not in PLATFORM_RULES:
            return await ctx.send(
                "❌ Select a platform: " + ", ".join(PLATFORM_NAMES) + "."
            )

        if selected_action in {"connect", "disconnect"}:
            if parameter is not None or value is not None:
                return await ctx.send(
                    f"❌ `{selected_action}` does not accept a parameter or value."
                )
            if selected_platform not in OAUTH_PROVIDERS:
                return await ctx.send(
                    f"❌ `{selected_platform}` does not use the OAuth connection flow. "
                    "Use its setup instructions instead."
                )
            if selected_action == "disconnect":
                PlatformConnectionService(service).disconnect(
                    target_guild.id, selected_platform
                )
                return await ctx.send(
                    f"✅ `{selected_platform}` authorization was removed for this server."
                )
            gateway = getattr(self.bot, "config", {}).get("gateway", {})
            public_url = str(gateway.get("public_base_url") or "").rstrip("/")
            if gateway.get("enabled") is not True or not public_url.startswith("https://"):
                return await ctx.send(
                    "❌ The host must enable the HTTPS OAuth gateway and configure "
                    "`gateway.public_base_url` first."
                )
            try:
                states = OAuthStateService(resolve_oauth_state_key())
                request_token = states.sign_start_request(
                    target_guild.id, selected_platform, ctx.author.id
                )
                connection_url = (
                    f"{public_url}/oauth/{selected_platform}/start?request="
                    f"{quote(request_token, safe='')}"
                )
                await ctx.author.send(
                    f"Connect `{selected_platform}` to **{target_guild.name}**:\n"
                    f"<{connection_url}>\n\nThis signed request expires in 10 minutes. "
                    "Confirm the platform account carefully before authorizing."
                )
            except (OSError, RuntimeError, ValueError, discord.Forbidden) as error:
                return await ctx.send(f"❌ Unable to create a private connection link: {error}")
            if ctx.guild is not None:
                return await ctx.send("✅ A time-limited connection link was sent to your DM.")
            return

        if selected_action not in {
            "set",
            "default",
            "enable",
            "disable",
            "connect",
            "disconnect",
        }:
            return await ctx.send(
                "❌ Action must be `set`, `default`, `enable`, `disable`, "
                "`connect`, or `disconnect`. Use "
                f"`!help platform` for syntax. Available {selected_platform} "
                f"parameters: {available_parameters(selected_platform)}."
            )

        if selected_action in {"enable", "disable"}:
            if parameter is not None or value is not None:
                return await ctx.send(
                    f"❌ `{selected_action}` does not accept a parameter or value."
                )
            enabled = selected_action == "enable"
            service.set_guild_platform_override(
                target_guild.id,
                selected_platform,
                "enabled",
                enabled,
            )
            state = "enabled" if enabled else "disabled"
            await ctx.send(
                f"✅ `{selected_platform}` is now {state} for this server. "
                "Other platform settings were not changed."
            )
            if enabled and selected_platform in SOCIAL_SOURCE_PLATFORMS:
                await self._ensure_socialmedia_source_channel(
                    ctx, service, target_guild
                )
            return

        selected_parameter = (parameter or "").casefold()
        if selected_parameter in SECRET_PARAMETERS:
            return await ctx.send(
                "❌ Credentials cannot be entered through Discord. Use the "
                "host-side `manage_secrets.py set` command with this guild ID "
                "to store an encrypted server-specific secret."
            )
        if selected_action == "default" and selected_parameter == "all":
            changed = service.clear_guild_platform_override(
                target_guild.id,
                selected_platform,
                "all",
            )
            status = "removed" if changed else "already absent"
            return await ctx.send(
                f"✅ All `{selected_platform}` server overrides are {status}; "
                "platform-wide defaults now apply."
            )
        if selected_parameter not in PLATFORM_RULES[selected_platform]:
            return await ctx.send(
                f"❌ Unsupported `{selected_platform}` parameter. Available: "
                f"{available_parameters(selected_platform)}."
            )

        if selected_action == "default":
            if value is not None:
                return await ctx.send("❌ The `default` action does not accept a value.")
            changed = service.clear_guild_platform_override(
                target_guild.id,
                selected_platform,
                selected_parameter,
            )
            inherited = service.platform(selected_platform).get(selected_parameter)
            status = "reset" if changed else "already using the default"
            return await ctx.send(
                f"✅ `{selected_platform}.{selected_parameter}` {status}: "
                f"`{inherited!s}`."
            )

        if value is None:
            return await ctx.send("❌ The `set` action requires a value.")
        rule = PLATFORM_RULES[selected_platform][selected_parameter]
        try:
            normalized = validate_parameter_value(rule, value)
        except PlatformValueError as error:
            return await ctx.send(
                f"❌ Invalid `{selected_platform}.{selected_parameter}` value: {error}."
            )

        service.set_guild_platform_override(
            target_guild.id,
            selected_platform,
            selected_parameter,
            normalized,
        )
        displayed = ", ".join(normalized) if isinstance(normalized, list) else str(normalized)
        await ctx.send(
            f"✅ `{selected_platform}.{selected_parameter}` set to `{displayed}` "
            "for this server."
        )

    def _service(self):
        return getattr(self.bot, "platform_config_service", None)

    async def _ensure_socialmedia_source_channel(self, ctx, service, guild):
        guild_config = service.ensure_discord_guild(str(guild.id), guild.name)
        current = guild_config.get("socialmedia_sources_channel")
        if str(current).isdigit() and guild.get_channel(int(current)) is not None:
            return guild.get_channel(int(current))

        await ctx.send(
            "🖼️ No moderator-only social-media source channel is configured. "
            "Reply with `1` to create `#socialmedia_sources`, `2` to select an "
            "existing private channel, or `3` to skip for now."
        )

        def reply_check(message):
            return (
                getattr(message.author, "id", None) == ctx.author.id
                and message.channel == ctx.channel
                and message.content.strip() in {"1", "2", "3"}
            )

        try:
            reply = await self.bot.wait_for("message", timeout=120, check=reply_check)
        except asyncio.TimeoutError:
            return await ctx.send("⌛ Social-media source channel setup timed out.")

        choice = reply.content.strip()
        if ctx.guild is not None:
            try:
                await reply.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass
        if choice == "3":
            return await ctx.send(
                "ℹ️ Image posting remains unavailable until a source channel is configured."
            )
        if choice == "1":
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                ),
            }
            member = guild.get_member(ctx.author.id)
            if member is not None:
                overwrites[member] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                )
            for role in guild.roles:
                permissions = role.permissions
                if permissions.manage_guild or permissions.manage_channels:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                    )
            try:
                channel = await guild.create_text_channel(
                    "socialmedia_sources",
                    overwrites=overwrites,
                    reason="EyeBot moderator social-media source channel",
                )
            except (discord.Forbidden, discord.HTTPException) as error:
                return await ctx.send(f"❌ Unable to create the source channel: {error}")
        else:
            private_channels = [
                channel
                for channel in guild.text_channels
                if not channel.permissions_for(guild.default_role).view_channel
            ]
            if not private_channels:
                return await ctx.send(
                    "❌ No existing text channel hidden from `@everyone` is available. "
                    "Enable the platform again and choose channel creation."
                )
            visible = private_channels[:25]
            choices = "\n".join(
                f"{index}. {channel.mention}"
                for index, channel in enumerate(visible, 1)
            )
            await ctx.send(
                "Reply with the number of the existing private channel:\n" + choices
            )

            def channel_check(message):
                return (
                    getattr(message.author, "id", None) == ctx.author.id
                    and message.channel == ctx.channel
                    and message.content.strip().isdigit()
                )

            try:
                selection = await self.bot.wait_for(
                    "message", timeout=120, check=channel_check
                )
            except asyncio.TimeoutError:
                return await ctx.send("⌛ Channel selection timed out.")
            index = int(selection.content.strip())
            if not 1 <= index <= len(visible):
                return await ctx.send("❌ That channel number is not valid.")
            channel = visible[index - 1]
            if ctx.guild is not None:
                try:
                    await selection.delete()
                except (discord.Forbidden, discord.HTTPException):
                    pass

        guild_config["socialmedia_sources_channel"] = channel.id
        service.save_discord_guild(guild.id)
        await ctx.send(f"✅ Social-media image sources will use {channel.mention}.")
        return channel

    def _can_manage(self, guild, author) -> bool:
        member = guild.get_member(author.id)
        permissions = getattr(member, "guild_permissions", None)
        return bool(permissions and permissions.manage_guild)

    async def _resolve_target(
        self,
        ctx,
        platform_name,
        action,
        parameter,
        value,
    ):
        if ctx.guild is not None:
            return ctx.guild, platform_name, action, parameter, value

        managed_guilds = [
            guild
            for guild in getattr(self.bot, "guilds", ())
            if self._can_manage(guild, ctx.author)
        ]
        possible_guild_id = str(platform_name or "")
        if possible_guild_id.isdigit():
            target = next(
                (guild for guild in managed_guilds if str(guild.id) == possible_guild_id),
                None,
            )
            if target is None:
                await ctx.send(
                    "❌ That server is unavailable or you do not have Manage "
                    "Server permission there."
                )
                return None
            shifted = (value or "").split(maxsplit=1)
            shifted_parameter = shifted[0] if shifted else None
            shifted_value = shifted[1] if len(shifted) > 1 else None
            return target, action, parameter, shifted_parameter, shifted_value

        if len(managed_guilds) == 1:
            return managed_guilds[0], platform_name, action, parameter, value
        if not managed_guilds:
            await ctx.send(
                "❌ No shared server was found where you have Manage Server permission."
            )
            return None

        choices = "\n".join(
            f"- `{guild.id}` — {guild.name}" for guild in managed_guilds
        )
        await ctx.send(
            "❌ Select a server by ID in DMs:\n"
            "`!platform <guild_id> <platform> <action> ...`\n"
            f"{choices}"
        )
        return None

    async def _require_mod_channel(self, ctx, service, guild) -> bool:
        guild_config = service.discord_guilds().get(str(guild.id), {})
        mod_channel = guild_config.get("mod_channel", "UNSET")
        try:
            mod_channel_id = int(mod_channel)
        except (TypeError, ValueError):
            await ctx.send(
                "❌ No moderation channel is configured for this server. Run "
                "`!setmodchannel` or retry this command in a direct message "
                "with the bot."
            )
            return False
        if getattr(ctx.channel, "id", None) != mod_channel_id:
            await ctx.send(
                f"❌ Platform settings can only be changed in <#{mod_channel_id}> "
                "or in a direct message with the bot."
            )
            return False
        return True

    async def _send_setup_instructions(
        self,
        ctx,
        service,
        guild,
        selected_platform,
    ):
        destination = None
        guild_config = service.discord_guilds().get(str(guild.id), {})
        try:
            mod_channel_id = int(guild_config.get("mod_channel", "UNSET"))
        except (TypeError, ValueError):
            mod_channel_id = None
        if mod_channel_id is not None:
            destination = guild.get_channel(mod_channel_id)
        if destination is None:
            destination = ctx.author

        selected = (
            PLATFORM_ORDER
            if selected_platform == "all"
            else (selected_platform,)
        )
        try:
            for platform_name in selected:
                guide = render_setup_instructions(platform_name, guild.id)
                for page in split_markdown_messages(guide):
                    await destination.send(page)
        except (discord.Forbidden, discord.HTTPException):
            return await ctx.send(
                "❌ I could not send setup instructions to the moderation "
                "channel or your direct messages. Check channel permissions "
                "and allow DMs, then try again."
            )

        if destination is ctx.author and ctx.guild is not None:
            await ctx.send("✅ I sent the platform setup instructions by DM.")

    async def _delete_invocation(self, ctx):
        message = getattr(ctx, "message", None)
        if message is None:
            return
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            logger = getattr(self.bot, "logger", None)
            if logger is not None:
                logger.warning("Could not delete a platform command invocation.")

    @platform_command.error
    async def platform_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return await ctx.send("❌ You need the Manage Server permission to use this command.")
        if isinstance(error, commands.BadArgument):
            return await ctx.send(f"❌ Invalid platform command: {error}")
        raise error


async def setup(bot):
    await bot.add_cog(Platform(bot))
