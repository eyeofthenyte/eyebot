import asyncio
import io
from datetime import timedelta

import discord
from discord.ext import commands
from eyebot import send_restart_command
from services.modChannelService import ModChannelHandler

# ---------------------------------------------------------
# Admin Commands
# ---------------------------------------------------------
class Admin (commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.config = bot.config
        self.prefix = self.config["prefix"]
        self.mod_channel_handler = ModChannelHandler(bot)
        bot.mod_channel_handler = self.mod_channel_handler


    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("Core functions started.")

    def _message_edit_previews(
        self,
        before_content,
        after_content,
        *,
        context=500,
        max_length=3900,
    ):
        """Return matching, change-focused previews of two message versions."""
        prefix_length = 0
        shared_length = min(len(before_content), len(after_content))
        while (
            prefix_length < shared_length
            and before_content[prefix_length] == after_content[prefix_length]
        ):
            prefix_length += 1

        suffix_length = 0
        before_remaining = len(before_content) - prefix_length
        after_remaining = len(after_content) - prefix_length
        while (
            suffix_length < before_remaining
            and suffix_length < after_remaining
            and before_content[-(suffix_length + 1)]
            == after_content[-(suffix_length + 1)]
        ):
            suffix_length += 1

        def preview(value):
            changed_end = len(value) - suffix_length
            start = max(0, prefix_length - context)
            end = min(len(value), changed_end + context)
            selected = value[start:end]

            if len(selected) > max_length:
                selected = selected[: max_length - 14] + "\n…[truncated]"
                end = len(value)

            if start:
                selected = "…\n" + selected
            if end < len(value):
                selected += "\n…"
            return selected or "*No text in this version of the changed region.*"

        return preview(before_content), preview(after_content)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Audit cached user-message content edits in the moderator channel."""
        guild = getattr(after, "guild", None)
        author = getattr(after, "author", None)
        if guild is None or author is None or getattr(author, "bot", False):
            return

        before_content = getattr(before, "content", "") or ""
        after_content = getattr(after, "content", "") or ""
        if before_content == after_content:
            return

        destination = self.mod_channel_handler.configured_channel(guild)
        if destination is None:
            return

        original_content = self.mod_channel_handler.sanitize_text(
            guild,
            before_content,
        )
        revised_content = self.mod_channel_handler.sanitize_text(
            guild,
            after_content,
        )
        original_preview, revised_preview = self._message_edit_previews(
            original_content,
            revised_content,
        )

        channel = getattr(after, "channel", None)
        channel_name = getattr(channel, "name", None)
        channel_value = f"#{channel_name}" if channel_name else "Unknown channel"
        author_value = self.mod_channel_handler.username(author)
        jump_url = getattr(after, "jump_url", None)

        original = discord.Embed(
            title="Message edited — original",
            description=original_preview,
        )
        original.add_field(name="Author", value=author_value, inline=True)
        original.add_field(name="Channel", value=channel_value, inline=True)
        if jump_url:
            original.add_field(
                name="Message",
                value=f"[Open edited message]({jump_url})",
                inline=False,
            )

        revised = discord.Embed(
            title="Message edited — revised",
            description=revised_preview,
            timestamp=getattr(after, "edited_at", None),
        )

        files = []
        if len(original_content) > 4096 or len(revised_content) > 4096:
            message_id = getattr(after, "id", "unknown")
            files = [
                discord.File(
                    io.BytesIO(original_content.encode("utf-8")),
                    filename=f"message-{message_id}-original.txt",
                ),
                discord.File(
                    io.BytesIO(revised_content.encode("utf-8")),
                    filename=f"message-{message_id}-revised.txt",
                ),
            ]
            revised.set_footer(
                text="Complete original and revised messages are attached."
            )

        try:
            await self.mod_channel_handler.send(
                guild,
                channel=destination,
                embeds=[original, revised],
                files=files,
            )
        except Exception as error:
            self.logger.error(
                "Unable to deliver message-edit audit for guild %s, "
                "message %s: %s",
                getattr(guild, "id", "unknown"),
                getattr(after, "id", "unknown"),
                error,
            )

    async def _resolve_message_deleter(self, message):
        """Best-effort lookup of a moderator who deleted a cached message."""
        guild = message.guild
        detected_at = discord.utils.utcnow()
        author_id = getattr(message.author, "id", None)
        channel_id = getattr(message.channel, "id", None)

        for attempt in range(3):
            if attempt:
                await asyncio.sleep(0.75)
            try:
                async for entry in guild.audit_logs(
                    limit=6,
                    action=discord.AuditLogAction.message_delete,
                    after=detected_at - timedelta(seconds=15),
                ):
                    target_id = getattr(getattr(entry, "target", None), "id", None)
                    entry_channel_id = getattr(
                        getattr(getattr(entry, "extra", None), "channel", None),
                        "id",
                        None,
                    )
                    if target_id == author_id and entry_channel_id == channel_id:
                        return (
                            self.mod_channel_handler.username(entry.user),
                            "Identified from Discord's audit log.",
                        )
            except (discord.Forbidden, discord.HTTPException) as error:
                self.logger.warning(
                    "Unable to inspect the Discord audit log for deleted "
                    "message %s in guild %s: %s",
                    getattr(message, "id", "unknown"),
                    getattr(guild, "id", "unknown"),
                    error,
                )
                return "Unknown", "Discord audit log unavailable to EyeBot."

        return (
            self.mod_channel_handler.username(message.author),
            "Likely self-deleted; Discord does not audit self-deletions.",
        )

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Record cached user-message deletions in the moderator channel."""
        guild = getattr(message, "guild", None)
        author = getattr(message, "author", None)
        if guild is None or author is None or getattr(author, "bot", False):
            return

        destination = self.mod_channel_handler.configured_channel(guild)
        if destination is None:
            return

        content = self.mod_channel_handler.sanitize_text(
            guild,
            getattr(message, "content", "") or "",
        )
        if content:
            preview = content
            if len(preview) > 4096:
                preview = preview[:4083] + "\n…[truncated]"
        else:
            preview = "*No text content.*"

        deleter, deletion_note = await self._resolve_message_deleter(message)
        channel = getattr(message, "channel", None)
        channel_name = getattr(channel, "name", None)
        channel_value = f"#{channel_name}" if channel_name else "Unknown channel"

        embed = discord.Embed(
            title="Message deleted",
            description=preview,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name="Author",
            value=self.mod_channel_handler.username(author),
            inline=True,
        )
        embed.add_field(name="Channel", value=channel_value, inline=True)
        embed.add_field(name="Deleted by", value=deleter, inline=True)
        embed.add_field(
            name="Deletion identification",
            value=deletion_note,
            inline=False,
        )
        embed.add_field(
            name="Message ID",
            value=str(getattr(message, "id", "Unknown")),
            inline=False,
        )

        attachment_names = [
            getattr(attachment, "filename", "unnamed attachment")
            for attachment in getattr(message, "attachments", ())
        ]
        if attachment_names:
            attachment_summary = "\n".join(
                f"• {name}" for name in attachment_names
            )
            if len(attachment_summary) > 1024:
                attachment_summary = attachment_summary[:1011] + "\n…[truncated]"
            embed.add_field(
                name="Attachments",
                value=attachment_summary,
                inline=False,
            )

        files = []
        if len(content) > 4096:
            files.append(
                discord.File(
                    io.BytesIO(content.encode("utf-8")),
                    filename=(
                        f"message-{getattr(message, 'id', 'unknown')}-deleted.txt"
                    ),
                )
            )
            embed.set_footer(text="The complete deleted message is attached.")

        try:
            await self.mod_channel_handler.send(
                guild,
                channel=destination,
                embed=embed,
                files=files,
            )
        except Exception as error:
            self.logger.error(
                "Unable to deliver message-deletion audit for guild %s, "
                "message %s: %s",
                getattr(guild, "id", "unknown"),
                getattr(message, "id", "unknown"),
                error,
            )

    async def cog_command_error(self, ctx, error):
        self.logger.error(f'Admin encountered error: {error}')
        if isinstance(error, commands.CommandError):
            self.logger.error("There was an error with Admin commands.")
            await ctx.send('Something went wrong.')



    # ---------------------------------------------------------
    # Administrative Commands
    # ---------------------------------------------------------
    @commands.command(name="setprefix")
    @commands.has_permissions(manage_guild=True)
    async def set_prefix(self, ctx, prefix: str):
        """Set this server's prefix, or use ``reset`` for the global default."""
        if ctx.guild is None:
            return await ctx.send("❌ Server prefixes cannot be changed in DMs.")

        global_prefix = self.config.get("prefix", "!") or "!"
        if prefix.casefold() == "reset":
            selected_prefix = global_prefix
        else:
            selected_prefix = prefix.strip()
            if not 1 <= len(selected_prefix) <= 5 or any(
                character.isspace() for character in selected_prefix
            ):
                return await ctx.send(
                    "❌ Prefixes must contain 1–5 non-whitespace characters."
                )

        platform_service = getattr(
            self.bot,
            "platform_config_service",
            None,
        )
        if platform_service is None:
            return await ctx.send("❌ Per-server configuration is unavailable.")

        guild_config = platform_service.ensure_discord_guild(
            str(ctx.guild.id),
            ctx.guild.name,
            global_prefix,
        )
        guild_config["prefix"] = selected_prefix
        platform_service.save_discord_guild(ctx.guild.id)
        await ctx.send(
            f"✅ Server command prefix set to `{selected_prefix}`."
        )

    #Shutdown bot
    @commands.command(aliases=['shutdown','sd'])
    @commands.is_owner()
    async def _shutdown(self,ctx):
        """
        🔒 Gracefully shuts down the bot.

        Usage:
        `!shutdown`

        Aliases:`!sd`, `!_shutdown`
        
        Access: Bot Owner Only
        """


        try:
            await ctx.send("Shutting down the bot...")
            await self.bot.close()

        except Exception as e:
            self.bot.logger.log(f'{e}')     
            await ctx.send("There was a problem shutting down the bot. You might not be the bot owner.")

    @commands.command(name="restart")
    @commands.is_owner()
    async def restart_platform(self, ctx, platform: str):
        """
        🔒 Restarts one enabled platform bot.

        Usage:
        `!restart <platform>`

        Example:
        `!restart twitch`

        Access: Bot Owner Only
        """
        platform = platform.strip().lower()
        if platform == "discord":
            await ctx.send("♻️ Restarting the Discord bot...")
        try:
            result = await asyncio.to_thread(send_restart_command, platform)
        except (OSError, RuntimeError, ValueError) as error:
            if platform != "discord":
                await ctx.send(f"❌ Restart failed: {error}")
            self.logger.error(f"Platform restart failed for {platform}: {error}")
            return
        if platform != "discord":
            await ctx.send(f"✅ {result}.")

    #Disconnect bot from server BOT OWNER ONLY
    @commands.command()
    @commands.check_any(commands.has_permissions(administrator=True),commands.is_owner())
    async def leave(self, ctx, *, guild_name):
        """
        📤 Forces the bot to leave a server by its name.

        Usage:
        `!leave <Server Name>`

        Example:
        `!leave My Cool Server`

        Note: Server name is case-sensitive
        Access: Server Administrator or Bot Owner
        """

        guild = discord.utils.get(self.bot.guilds, name=guild_name)
        if guild is None:
            await ctx.send("I don't recognize that guild. Please enter the server name. (case sensitive)")
            self.logger.error(
                "leaving_error - blank or invalid server name, "
                "please enter the guild name"
            )
            return
        else:
            await guild.leave()
            self.logger.info(
                f"connection_broken: {self.bot.user.name} has left: "
                f"{guild.name} (id: {guild.id})"
            )

    #Check connected servers BOT OWNER ONLY
    @commands.command(name="servers", aliases=["server"])
    @commands.is_owner()
    async def servers(self, ctx):
        """
        📋 Lists all servers the bot is currently connected to via DM.\n"

        Usage:
        `!servers` or `!server`

        Access: Bot Owner Only
        """

        guilds = tuple(self.bot.guilds)
        if not guilds:
            await ctx.author.send("EyeBot is not currently connected to any servers.")
            self.logger.info("End of Server Listing - no connected servers.")
            return

        platform_names = (
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
        platform_service = getattr(
            self.bot,
            "platform_config_service",
            None,
        )
        lines = ["📋 **Connected Servers**"]
        for guild in guilds:
            line = f"• {guild.name} (id: {guild.id})"
            lines.append(line)
            self.logger.info(line)

            statuses = []
            for platform_name in platform_names:
                if platform_service is not None:
                    platform_config = platform_service.effective_guild_platform(
                        guild.id,
                        platform_name,
                    )
                else:
                    platform_config = getattr(self, "config", {}).get(
                        platform_name,
                        {},
                    )
                enabled = (
                    isinstance(platform_config, dict)
                    and platform_config.get("enabled") is True
                )
                statuses.append(
                    f"{platform_name}: {'enabled' if enabled else 'disabled'}"
                )
            lines.append("  Platforms: " + " | ".join(statuses))

        try:
            pages = []
            page = ""
            for line in lines:
                candidate = f"{page}\n{line}" if page else line
                if len(candidate) > 1900:
                    pages.append(page)
                    page = line
                else:
                    page = candidate
            if page:
                pages.append(page)
            for page in pages:
                await ctx.author.send(page)
        except discord.Forbidden:
            await ctx.send(
                "I couldn't send you the server list. Please enable direct "
                "messages and try again."
            )
            return

        await ctx.send("✅ I sent the connected server list by direct message.")
        self.logger.info("End of Server Listing.")


async def setup(bot):
    await bot.add_cog(Admin(bot))
