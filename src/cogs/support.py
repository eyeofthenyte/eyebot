"""Discord-only private support ticket workflow."""

from __future__ import annotations

import asyncio
import io
import mimetypes
import time
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from services.supportTicketService import (
    ACTIVE_STATUSES,
    SupportTicket,
    SupportTicketError,
    SupportTicketService,
    TicketImage,
)


CLAIM_EMOJI = "📋"
RESOLVE_EMOJI = "✅"
CANCEL_EMOJI = "❌"
GENERIC_FAILURE = "EyeBot could not complete that ticket action. Please try again later."
UNSET_VIEW = object()


def is_moderator(member) -> bool:
    permissions = getattr(member, "guild_permissions", None)
    return bool(
        permissions
        and (
            permissions.administrator
            or permissions.manage_guild
            or permissions.manage_messages
            or permissions.manage_threads
        )
    )


async def download_ticket_images(service, attachments) -> tuple[TicketImage, ...]:
    attachments = tuple(attachments or ())
    if len(attachments) > service.maximum_images:
        raise SupportTicketError(
            f"A ticket may include at most {service.maximum_images} images."
        )
    maximum_each = max(1, int(service.settings.get("max_image_bytes", 5_242_880)))
    images = []
    for attachment in attachments:
        if int(getattr(attachment, "size", 0)) > maximum_each:
            raise SupportTicketError(
                f"Image `{attachment.filename}` exceeds the per-image size limit."
            )
        content_type = str(
            attachment.content_type
            or mimetypes.guess_type(attachment.filename)[0]
            or "application/octet-stream"
        ).split(";", 1)[0].casefold()
        images.append(
            TicketImage(
                filename=attachment.filename,
                content_type=content_type,
                data=await attachment.read(use_cached=True),
            )
        )
    service.validate_images(images)
    sanitized = tuple(service.sanitize_image(image) for image in images)
    return service.validate_images(sanitized)


class TicketModal(discord.ui.Modal):
    def __init__(self, cog: "Support", guild_id: int, opener_id: int):
        super().__init__(title="Open a Support Ticket", timeout=900)
        self.cog = cog
        self.guild_id = guild_id
        self.opener_id = opener_id
        self.description_input = discord.ui.TextInput(
            style=discord.TextStyle.paragraph,
            placeholder="Describe the issue and what assistance you need.",
            required=True,
            min_length=10,
            max_length=cog.maximum_description_length,
        )
        self.link_input = discord.ui.TextInput(
            placeholder="https://discord.com/channels/server/channel/message",
            required=False,
            max_length=200,
        )
        self.images_input = None
        self.add_item(
            discord.ui.Label(text="Issue description", component=self.description_input)
        )
        self.add_item(
            discord.ui.Label(
                text="Message link (optional)",
                description="Must link to a message you can view in this server.",
                component=self.link_input,
            )
        )
        if cog.service.maximum_images:
            self.images_input = discord.ui.FileUpload(
                required=False,
                min_values=0,
                max_values=cog.service.maximum_images,
            )
            self.add_item(
                discord.ui.Label(
                    text="Images (optional)",
                    description=(
                        f"Upload up to {cog.service.maximum_images} images. "
                        "Remove visible secrets first."
                    ),
                    component=self.images_input,
                )
            )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await self.cog.submit_ticket(
                interaction,
                description=self.description_input.value,
                message_link=self.link_input.value,
                attachments=(self.images_input.values if self.images_input else ()),
            )
        except SupportTicketError as error:
            self.cog.clear_open_cooldown(self.guild_id, self.opener_id)
            await interaction.followup.send(f"❌ {error}", ephemeral=True)
        except Exception as error:
            self.cog.clear_open_cooldown(self.guild_id, self.opener_id)
            self.cog.logger.error(
                "Support ticket submission failed: " + self.cog.safe_error(error),
                guild_id=self.guild_id,
            )
            await interaction.followup.send(f"❌ {GENERIC_FAILURE}", ephemeral=True)

    async def on_error(self, interaction, error):
        self.cog.logger.error(
            "Support ticket modal failed: " + self.cog.safe_error(error),
            guild_id=self.guild_id,
        )
        method = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
        await method(f"❌ {GENERIC_FAILURE}", ephemeral=True)


class SupportChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            custom_id="eyebot:ticket:setup:channel",
            channel_types=[discord.ChannelType.text],
            placeholder="Select the support ticket channel",
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        view: TicketSetupView = self.view
        channel = self.values[0]
        await interaction.response.defer(ephemeral=True, thinking=True)
        await view.cog.configure_support_channel(interaction, channel)


class TicketSetupView(discord.ui.View):
    def __init__(self, cog: "Support", user_id: int):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.add_item(SupportChannelSelect())

    async def interaction_check(self, interaction):
        if interaction.user.id == self.user_id and is_moderator(interaction.user):
            return True
        await interaction.response.send_message(
            "❌ Only the moderator who opened this setup may use it.", ephemeral=True
        )
        return False

    @discord.ui.button(
        label="Create #support_tickets",
        emoji="🛠️",
        style=discord.ButtonStyle.primary,
        custom_id="eyebot:ticket:setup:create",
    )
    async def create_channel(self, interaction, _button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.cog.create_support_channel(interaction)

    @discord.ui.button(
        label="Disable tickets",
        emoji="🔇",
        style=discord.ButtonStyle.danger,
        custom_id="eyebot:ticket:setup:disable",
    )
    async def disable_tickets(self, interaction, _button):
        self.cog.set_guild_ticket_config(
            interaction.guild, enabled=False, channel_id="DISABLED"
        )
        await interaction.response.send_message(
            "🔇 Support tickets are disabled for this server.", ephemeral=True
        )
        await self.cog.audit(
            interaction.guild,
            f"{self.cog.plain_username(interaction.user)} disabled the support ticket system.",
        )


class TicketActionButton(discord.ui.Button):
    def __init__(self, cog: "Support", ticket: SupportTicket, action: str, *, disabled=False):
        details = {
            "claim": (CLAIM_EMOJI, "Assign", discord.ButtonStyle.primary),
            "resolve": (RESOLVE_EMOJI, "Resolve", discord.ButtonStyle.success),
            "cancel": (CANCEL_EMOJI, "Cancel", discord.ButtonStyle.danger),
        }
        emoji, label, style = details[action]
        super().__init__(
            emoji=emoji,
            label=label,
            style=style,
            disabled=disabled,
            custom_id=f"eyebot:ticket:{action}:{ticket.guild_id}:{ticket.number}",
        )
        self.cog = cog
        self.ticket_number = ticket.number
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        if not is_moderator(interaction.user):
            return await interaction.response.send_message(
                "❌ Only moderators may manage support tickets.", ephemeral=True
            )
        if self.action in {"resolve", "cancel"}:
            return await interaction.response.send_modal(
                TicketCloseModal(self.cog, self.ticket_number, self.action)
            )
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.cog.claim_ticket(interaction, self.ticket_number)


class TicketControlView(discord.ui.View):
    def __init__(self, cog: "Support", ticket: SupportTicket):
        super().__init__(timeout=None)
        disabled = ticket.status not in ACTIVE_STATUSES
        self.add_item(TicketActionButton(cog, ticket, "claim", disabled=disabled or ticket.status != "open"))
        self.add_item(TicketActionButton(cog, ticket, "resolve", disabled=disabled))
        self.add_item(TicketActionButton(cog, ticket, "cancel", disabled=disabled))

    async def on_error(self, interaction, error, _item):
        cog = next(
            (item.cog for item in self.children if hasattr(item, "cog")),
            None,
        )
        if cog is not None:
            cog.logger.error(
                "Support ticket control failed: " + cog.safe_error(error),
                guild_id=interaction.guild_id,
            )
        method = (
            interaction.followup.send
            if interaction.response.is_done()
            else interaction.response.send_message
        )
        await method(f"❌ {GENERIC_FAILURE}", ephemeral=True)


class TicketCloseModal(discord.ui.Modal):
    def __init__(self, cog: "Support", ticket_number: str, action: str):
        verb = "Resolve" if action == "resolve" else "Cancel"
        super().__init__(title=f"{verb} {ticket_number}", timeout=300)
        self.cog = cog
        self.ticket_number = ticket_number
        self.action = action
        self.note_input = discord.ui.TextInput(
            style=discord.TextStyle.paragraph,
            placeholder=(
                "Briefly describe the resolution."
                if action == "resolve"
                else "Briefly explain why the ticket is being canceled."
            ),
            required=True,
            min_length=5,
            max_length=cog.maximum_close_note_length,
        )
        self.add_item(
            discord.ui.Label(
                text="Resolution description" if action == "resolve" else "Cancellation reason",
                component=self.note_input,
            )
        )

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        if self.action == "resolve":
            await self.cog.resolve_ticket(interaction, self.ticket_number, self.note_input.value)
        else:
            await self.cog.cancel_ticket(interaction, self.ticket_number, self.note_input.value)


class Support(commands.Cog, name="Support Tickets"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.platform_config = bot.platform_config_service
        self.settings = dict(bot.config.get("support_tickets", {}))
        self.service = SupportTicketService(
            self.settings,
            self.platform_config.guild_config_dir,
            self.logger,
        )
        self.maximum_description_length = max(
            100, min(4000, int(self.settings.get("max_description_length", 4000)))
        )
        self.maximum_close_note_length = max(
            20, min(1000, int(self.settings.get("max_close_note_length", 1000)))
        )
        self._ticket_locks = {}
        self._open_attempts = {}
        self._restored = False
        self._synced = False

    def lock_for(self, guild_id, number):
        return self._ticket_locks.setdefault((str(guild_id), number), asyncio.Lock())

    def clear_open_cooldown(self, guild_id, user_id):
        self._open_attempts.pop((str(guild_id), str(user_id)), None)

    def safe_error(self, error):
        return f"{type(error).__name__}: {error}"[:500]

    async def cog_app_command_error(self, interaction, error):
        self.logger.error(
            "Support ticket application command failed: " + self.safe_error(error),
            guild_id=interaction.guild_id,
        )
        method = (
            interaction.followup.send
            if interaction.response.is_done()
            else interaction.response.send_message
        )
        await method(f"❌ {GENERIC_FAILURE}", ephemeral=True)

    def guild_config(self, guild):
        return self.platform_config.ensure_discord_guild(
            str(guild.id), guild.name, self.bot.config.get("prefix", "!")
        )

    def ticket_config(self, guild):
        config = self.guild_config(guild).setdefault(
            "support_tickets", {"enabled": True, "channel_id": "UNSET"}
        )
        config.setdefault("enabled", True)
        config.setdefault("channel_id", "UNSET")
        return config

    def set_guild_ticket_config(self, guild, **values):
        self.ticket_config(guild).update(values)
        self.platform_config.save_discord_guild(guild.id)

    def support_channel(self, guild):
        selected = self.ticket_config(guild).get("channel_id", "UNSET")
        try:
            return guild.get_channel(int(selected))
        except (TypeError, ValueError):
            return None

    def mod_channel(self, guild):
        selected = self.guild_config(guild).get("mod_channel", "UNSET")
        try:
            return guild.get_channel(int(selected))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def ticket_permission_problem(channel, guild, user, *, has_images=False):
        """Return an actionable permission failure before ticket creation."""
        bot_permissions = channel.permissions_for(guild.me)
        required_bot_permissions = (
            ("view_channel", "View Channel"),
            ("send_messages", "Send Messages"),
            ("create_private_threads", "Create Private Threads"),
            ("send_messages_in_threads", "Send Messages in Threads"),
            ("manage_threads", "Manage Threads"),
        )
        if has_images:
            required_bot_permissions += (("attach_files", "Attach Files"),)
        missing = [
            label
            for attribute, label in required_bot_permissions
            if not getattr(bot_permissions, attribute, False)
        ]
        if missing:
            return (
                "EyeBot is missing required permissions in "
                f"{channel.mention}: {', '.join(missing)}."
            )

        user_permissions = channel.permissions_for(user)
        if not getattr(user_permissions, "view_channel", False):
            return (
                f"You cannot view the configured support channel {channel.mention}. "
                "A moderator must grant your role View Channel permission there."
            )
        if not getattr(user_permissions, "send_messages_in_threads", False):
            return (
                f"You cannot participate in threads in {channel.mention}. "
                "A moderator must grant your role Send Messages in Threads permission there."
            )
        return None

    async def resolve_thread(self, guild, thread_id):
        if not thread_id:
            return None
        selected = int(thread_id)
        thread = guild.get_thread(selected) or self.bot.get_channel(selected)
        if thread is not None:
            return thread
        try:
            fetched = await self.bot.fetch_channel(selected)
            return fetched if isinstance(fetched, discord.Thread) else None
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    async def audit(self, guild, message, *, file=None):
        destination = self.mod_channel(guild)
        if destination is not None:
            try:
                await destination.send(
                    f"🧾 {message}",
                    file=file,
                    allowed_mentions=discord.AllowedMentions.none(),
                    silent=True,
                )
            except (discord.Forbidden, discord.HTTPException) as error:
                self.logger.error(
                    "Support ticket audit delivery failed: " + self.safe_error(error),
                    guild_id=guild.id,
                )

    @staticmethod
    def plain_username(user, *, fallback="unknown user"):
        name = getattr(user, "name", None)
        return discord.utils.escape_markdown(str(name or fallback))

    @commands.Cog.listener()
    async def on_ready(self):
        if not self._synced:
            try:
                synced = await self.bot.tree.sync()
                self.logger.info(f"Synchronized {len(synced)} Discord application commands.")
                self._synced = True
            except discord.HTTPException as error:
                self.logger.error("Application command synchronization failed: " + self.safe_error(error))
        if self._restored:
            return
        self._restored = True
        for guild in self.bot.guilds:
            for ticket in self.service.list(guild.id, active_only=True):
                if ticket.public_message_id:
                    self.bot.add_view(
                        TicketControlView(self, ticket),
                        message_id=int(ticket.public_message_id),
                    )
            await self.cleanup_expired_statuses(guild)

    @app_commands.command(name="ticket", description="Open a private EyeBot support ticket")
    @app_commands.guild_only()
    async def ticket(self, interaction: discord.Interaction):
        if self.settings.get("enabled", True) is not True:
            return await interaction.response.send_message(
                "❌ Support tickets are not currently available.", ephemeral=True
            )
        config = self.ticket_config(interaction.guild)
        channel = self.support_channel(interaction.guild)
        if config.get("enabled") is not True or channel is None:
            if is_moderator(interaction.user):
                return await interaction.response.send_message(
                    "Support tickets need a destination channel. Select one or create `#support_tickets`.",
                    view=TicketSetupView(self, interaction.user.id),
                    ephemeral=True,
                )
            return await interaction.response.send_message(
                "❌ Support tickets are not configured for this server. Please contact a moderator.",
                ephemeral=True,
            )
        if self.mod_channel(interaction.guild) is None:
            return await interaction.response.send_message(
                "❌ A moderator log channel must be configured before tickets can be opened.",
                ephemeral=True,
            )
        active = [
            item for item in self.service.list(interaction.guild_id, active_only=True)
            if item.opener_id == str(interaction.user.id)
        ]
        if len(active) >= self.service.maximum_open_per_user:
            return await interaction.response.send_message(
                f"❌ You already have {len(active)} open tickets; the maximum is {self.service.maximum_open_per_user}.",
                ephemeral=True,
            )
        cooldown = max(
            0, min(3600, int(self.settings.get("opening_cooldown_seconds", 60)))
        )
        key = (str(interaction.guild_id), str(interaction.user.id))
        retry_after = cooldown - (time.monotonic() - self._open_attempts.get(key, 0))
        if retry_after > 0:
            return await interaction.response.send_message(
                f"⏳ Please wait {retry_after:.0f} seconds before opening another ticket form.",
                ephemeral=True,
            )
        self._open_attempts[key] = time.monotonic()
        await interaction.response.send_modal(
            TicketModal(self, interaction.guild_id, interaction.user.id)
        )

    @app_commands.command(name="ticket-setup", description="Configure this server's support ticket channel")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def ticket_setup(self, interaction: discord.Interaction):
        if not is_moderator(interaction.user):
            return await interaction.response.send_message("❌ Moderator permission is required.", ephemeral=True)
        await interaction.response.send_message(
            "Select an existing text channel or create `#support_tickets`.",
            view=TicketSetupView(self, interaction.user.id),
            ephemeral=True,
        )

    @app_commands.command(
        name="ticket-guide",
        description="Post the support ticket instructions in the configured channel",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def ticket_guide(self, interaction: discord.Interaction):
        if not is_moderator(interaction.user):
            return await interaction.response.send_message(
                "❌ Moderator permission is required.", ephemeral=True
            )
        channel = self.support_channel(interaction.guild)
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "❌ Configure a support ticket channel with `/ticket-setup` first.",
                ephemeral=True,
            )
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            guide_message = await self.post_support_instructions(channel)
        except (discord.Forbidden, discord.HTTPException) as error:
            self.logger.error(
                "Support ticket guide delivery failed: " + self.safe_error(error),
                guild_id=interaction.guild_id,
            )
            return await interaction.followup.send(
                "❌ EyeBot could not post the guide. Check its Send Messages and "
                "Embed Links permissions.",
                ephemeral=True,
            )
        await interaction.followup.send(
            f"✅ Support ticket guide posted: {guide_message.jump_url}",
            ephemeral=True,
        )
        await self.audit(
            interaction.guild,
            f"{self.plain_username(interaction.user)} posted the support ticket guide "
            f"in {channel.mention}.",
        )

    async def configure_support_channel(self, interaction, channel):
        resolved = interaction.guild.get_channel(channel.id)
        if not isinstance(resolved, discord.TextChannel):
            return await interaction.followup.send(
                "❌ Select a standard text channel.", ephemeral=True
            )
        try:
            guide_message = await self.post_support_instructions(resolved)
        except (discord.Forbidden, discord.HTTPException) as error:
            self.logger.error(
                "Support ticket guide delivery failed: " + self.safe_error(error),
                guild_id=interaction.guild_id,
            )
            return await interaction.followup.send(
                "❌ EyeBot could not post in that channel. Check its Send Messages and Embed Links permissions.",
                ephemeral=True,
            )
        self.set_guild_ticket_config(interaction.guild, enabled=True, channel_id=str(resolved.id))
        await interaction.followup.send(
            f"✅ Support tickets will use {resolved.mention}. The instruction guide was posted: "
            f"{guide_message.jump_url}",
            ephemeral=True,
        )
        await self.audit(
            interaction.guild,
            f"{self.plain_username(interaction.user)} selected {resolved.mention} "
            "as the support ticket channel.",
        )

    async def create_support_channel(self, interaction):
        guild = interaction.guild
        existing = discord.utils.get(guild.text_channels, name="support_tickets")
        if existing is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=False,
                    read_message_history=True,
                    send_messages_in_threads=True,
                ),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True,
                    create_private_threads=True,
                    send_messages_in_threads=True,
                    manage_threads=True,
                    attach_files=True,
                    embed_links=True,
                    read_message_history=True,
                ),
            }
            try:
                existing = await guild.create_text_channel("support_tickets", overwrites=overwrites)
            except (discord.Forbidden, discord.HTTPException):
                return await interaction.followup.send(
                    "❌ EyeBot could not create the channel. Check its Manage Channels permission.",
                    ephemeral=True,
                )
        try:
            guide_message = await self.post_support_instructions(existing)
        except (discord.Forbidden, discord.HTTPException) as error:
            self.logger.error(
                "Support ticket guide delivery failed: " + self.safe_error(error),
                guild_id=guild.id,
            )
            return await interaction.followup.send(
                "❌ EyeBot could not post the ticket instructions. Check its Send Messages and Embed Links permissions.",
                ephemeral=True,
            )
        self.set_guild_ticket_config(guild, enabled=True, channel_id=str(existing.id))
        await interaction.followup.send(
            f"✅ Support tickets will use {existing.mention}. The instruction guide was posted: "
            f"{guide_message.jump_url}",
            ephemeral=True,
        )
        await self.audit(
            guild,
            f"{self.plain_username(interaction.user)} configured {existing.mention} "
            "for support tickets.",
        )

    @staticmethod
    def support_instructions_embed():
        embed = discord.Embed(
            title="EyeBot Support Ticket Guide",
            description="Use this channel to open and track private support requests.",
            color=0x5865F2,
        )
        embed.add_field(
            name="👤 User Instructions",
            value=(
                "**Open a ticket**\n"
                "Use `/ticket`, describe the issue, and optionally include a message "
                "link and up to four images. Remove visible secrets before submitting.\n\n"
                "**What happens next**\n"
                "EyeBot creates a private thread shared with you and the moderators. "
                "The public status shows only a `T-######` ticket number. You may have "
                "up to three active tickets.\n\n"
                "You will receive a DM when the ticket is assigned, closed, or reopened. "
                "Resolution and cancellation DMs include the moderator's note."
            ),
            inline=True,
        )
        embed.add_field(
            name="🛡️ Moderator Instructions",
            value=(
                "**Controls**\n"
                "📋 assigns the ticket to you. ✅ resolves it. ❌ cancels it. Resolve and "
                "Cancel require a brief note and can only be completed by the assigned moderator.\n\n"
                "**Commands**\n"
                "Inside a ticket thread: `/resolved reason:...` or `/cancel reason:...`\n"
                "Outside a thread, also provide `ticketnumber:T-######`.\n"
                "Use `/ticket-list`, `/ticket-status`, and `/ticket-reopen` for management.\n\n"
                "Closing archives the private thread and transcript. Reopening restores the "
                "thread, user access, controls, and user notification."
            ),
            inline=True,
        )
        embed.set_footer(
            text="Ticket contents remain private; moderator actions are written to the configured mod log."
        )
        return embed

    @staticmethod
    async def post_support_instructions(channel):
        return await channel.send(embed=Support.support_instructions_embed())

    async def submit_ticket(self, interaction, *, description, message_link, attachments):
        guild = interaction.guild
        if guild is None or guild.id != self._snowflake(interaction.guild_id):
            raise SupportTicketError("Support tickets must be opened from a server.")
        channel = self.support_channel(guild)
        mod_channel = self.mod_channel(guild)
        if channel is None or mod_channel is None:
            raise SupportTicketError("The support or moderator channel is no longer available.")
        if message_link:
            parts = str(message_link).strip().rstrip("/>").split("/")
            if len(parts) >= 2 and parts[-2].isdecimal():
                linked_channel = guild.get_channel(int(parts[-2]))
                if linked_channel is None or not linked_channel.permissions_for(interaction.user).view_channel:
                    raise SupportTicketError("You may only link to a message you can view.")
        images = await download_ticket_images(self.service, attachments)
        permission_problem = self.ticket_permission_problem(
            channel,
            guild,
            interaction.user,
            has_images=bool(images),
        )
        if permission_problem:
            raise SupportTicketError(permission_problem)
        ticket = self.service.create(
            guild.id,
            interaction.user.id,
            description,
            message_link,
            image_count=len(images),
        )
        thread = None
        public_message = None
        delivery_stage = "creating the private thread"
        try:
            thread = await channel.create_thread(
                name=f"{ticket.number.lower()}-support",
                type=discord.ChannelType.private_thread,
                invitable=False,
                auto_archive_duration=self.thread_archive_minutes,
                reason=f"Support ticket {ticket.number} opened",
            )
            delivery_stage = "adding the requester to the private thread"
            await thread.add_user(interaction.user)
            text = f"## {ticket.number}\n{ticket.description}"
            if ticket.message_link:
                text += f"\n\nMessage link: {ticket.message_link}"
            files = [
                discord.File(io.BytesIO(image.data), filename=image.filename)
                for image in images
            ]
            delivery_stage = "posting the ticket contents"
            await thread.send(
                text,
                files=files,
                suppress_embeds=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            delivery_stage = "posting the public ticket status"
            public_message = await channel.send(
                view=TicketControlView(self, ticket),
                content=f"🎫 Ticket `{ticket.number}` has been opened.",
            )
        except (discord.Forbidden, discord.HTTPException) as error:
            self.logger.error(
                f"Support ticket {ticket.number} failed while {delivery_stage}: "
                f"{self.safe_error(error)}",
                guild_id=guild.id,
            )
            self.service.close(
                guild.id,
                ticket.number,
                getattr(self.bot.user, "id", 0),
                "canceled",
                "EyeBot canceled ticket creation after Discord delivery failed.",
            )
            try:
                if public_message is not None:
                    await public_message.delete()
                if thread is not None:
                    await thread.edit(locked=True, archived=True)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass
            raise SupportTicketError(
                f"EyeBot could not finish {delivery_stage}. No ticket was opened. "
                "A moderator can check EyeBot's permissions and error log for details."
            ) from error
        ticket = self.service.update_delivery(
            guild.id,
            ticket.number,
            public_message_id=public_message.id,
            thread_id=thread.id,
        )
        self.bot.add_view(
            TicketControlView(self, ticket),
            message_id=public_message.id,
        )
        await self.audit(
            guild,
            f"Ticket `{ticket.number}` was opened by "
            f"{self.plain_username(interaction.user)}. "
            f"Images attached: **{ticket.image_count}**. "
            f"Message link included: **{'yes' if ticket.message_link else 'no'}**.",
        )
        self.logger.info(
            f"Support ticket {ticket.number} opened",
            guild_id=guild.id,
        )
        await interaction.followup.send(
            f"✅ Ticket `{ticket.number}` was opened. Its contents are in a "
            "private thread shared with you and server moderators.",
            ephemeral=True,
        )

    def ticket_embed(self, ticket, *, opener=None):
        embed = discord.Embed(
            title=f"Support Ticket {ticket.number}",
            description=ticket.description[:4096],
            color={"open": 0xF1C40F, "assigned": 0x3498DB, "resolved": 0x2ECC71, "canceled": 0xE74C3C}.get(ticket.status, 0x5865F2),
        )
        embed.add_field(name="Status", value=ticket.status.title(), inline=True)
        embed.add_field(name="Opened by", value=(opener.mention if opener else f"<@{ticket.opener_id}>"), inline=True)
        embed.add_field(name="Images", value=str(ticket.image_count), inline=True)
        if ticket.assigned_to:
            embed.add_field(name="Assigned to", value=f"<@{ticket.assigned_to}>", inline=True)
        if ticket.message_link:
            embed.add_field(name="Message link", value=ticket.message_link, inline=False)
        if ticket.close_note:
            embed.add_field(name="Closure note", value=ticket.close_note[:1024], inline=False)
        embed.set_footer(text="Ticket controls are restricted to moderators.")
        return embed

    async def claim_ticket(self, interaction, number):
        async with self.lock_for(interaction.guild_id, number):
            ticket = self.service.get(interaction.guild_id, number)
            if ticket.status != "open":
                return await interaction.followup.send(f"❌ Ticket `{number}` is already {ticket.status}.", ephemeral=True)
            opener = interaction.guild.get_member(int(ticket.opener_id))
            if opener is None:
                try:
                    opener = await interaction.guild.fetch_member(int(ticket.opener_id))
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    return await interaction.followup.send("❌ The ticket opener is no longer available.", ephemeral=True)
            thread = await self.resolve_thread(interaction.guild, ticket.thread_id)
            if thread is None:
                return await interaction.followup.send(
                    "❌ The private ticket thread is unavailable.", ephemeral=True
                )
            ticket = self.service.claim(interaction.guild_id, number, interaction.user.id)
            await thread.send(
                f"{CLAIM_EMOJI} Ticket assigned to {interaction.user.mention}.",
                allowed_mentions=discord.AllowedMentions(users=True),
            )
            await self.update_public_status(
                interaction.guild,
                ticket,
                f"📋 Ticket `{ticket.number}` has been assigned.",
                view=TicketControlView(self, ticket),
            )
            try:
                await opener.send(
                    f"📋 Your support ticket `{ticket.number}` has been assigned. Watch the private support thread in **{interaction.guild.name}** for responses; it will be addressed shortly."
                )
            except (discord.Forbidden, discord.HTTPException):
                await thread.send("ℹ️ I could not DM the ticket opener; updates will remain in this thread.")
            await self.audit(
                interaction.guild,
                f"{self.plain_username(interaction.user)} claimed ticket "
                f"`{ticket.number}` opened by "
                f"{self.plain_username(opener, fallback=f'user ID {ticket.opener_id}')}.",
            )
            self.logger.info(
                f"Support ticket {ticket.number} assigned",
                guild_id=interaction.guild_id,
            )
            await interaction.followup.send(f"✅ Ticket `{ticket.number}` is assigned to you.", ephemeral=True)

    async def resolve_ticket(self, interaction, number, note):
        await self.close_ticket(interaction, number, "resolved", note)

    async def cancel_ticket(self, interaction, number, note):
        await self.close_ticket(interaction, number, "canceled", note)

    async def close_ticket(self, interaction, number, status, note):
        async with self.lock_for(interaction.guild_id, number):
            ticket = self.service.get(interaction.guild_id, number)
            if ticket.status not in ACTIVE_STATUSES:
                return await interaction.followup.send(
                    f"ℹ️ Ticket `{number}` is already {ticket.status}.",
                    ephemeral=True,
                )
            if ticket.status != "assigned":
                return await interaction.followup.send("❌ Claim this ticket before closing it.", ephemeral=True)
            if ticket.assigned_to != str(interaction.user.id):
                return await interaction.followup.send("❌ Only the assigned moderator may close this ticket.", ephemeral=True)
            ticket = self.service.close(
                interaction.guild_id, number, interaction.user.id, status, note
            )
            guild = interaction.guild
            await self.archive_thread(guild, ticket)
            verb = "resolved" if status == "resolved" else "canceled"
            icon = RESOLVE_EMOJI if status == "resolved" else CANCEL_EMOJI
            await self.update_public_status(
                guild,
                ticket,
                f"{icon} Ticket `{ticket.number}` has been {verb}.",
                view=None,
            )
            delete_at = datetime.now(timezone.utc) + timedelta(seconds=self.status_delete_seconds)
            ticket = self.service.update_delivery(guild.id, number, public_delete_at=delete_at.isoformat())
            self.schedule_public_delete(guild.id, ticket)
            opener = guild.get_member(int(ticket.opener_id))
            if opener:
                try:
                    await opener.send(
                        f"{icon} Your support ticket `{ticket.number}` in **{guild.name}** "
                        f"was {verb}.\n\n**Moderator note:** {ticket.close_note}"
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
            await self.audit(
                guild,
                f"{self.plain_username(interaction.user)} marked ticket `{ticket.number}` "
                f"opened by {self.plain_username(opener, fallback=f'user ID {ticket.opener_id}')} "
                f"as {verb}. Note: {ticket.close_note}",
            )
            self.logger.info(
                f"Support ticket {ticket.number} marked {verb}",
                guild_id=guild.id,
            )
            await interaction.followup.send(f"{icon} Ticket `{ticket.number}` was {verb}.", ephemeral=True)

    async def archive_thread(self, guild, ticket):
        if not ticket.thread_id:
            return None
        thread = await self.resolve_thread(guild, ticket.thread_id)
        if thread is None:
            return None
        try:
            await thread.send(
                f"{'✅' if ticket.status == 'resolved' else '❌'} Ticket "
                f"`{ticket.number}` is now {ticket.status}.\n\n"
                f"**Moderator note:** {ticket.close_note}",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            lines = [f"Transcript for {ticket.number}"]
            limit = max(1, min(1000, int(self.settings.get("transcript_max_messages", 500))))
            async for message in thread.history(limit=limit, oldest_first=True):
                content = str(message.content or "").replace("\r", " ")
                lines.append(f"[{message.created_at.isoformat()}] {message.author} ({message.author.id}): {content}")
            data = "\n".join(lines).encode("utf-8")[:2_000_000]
            opener = guild.get_member(int(ticket.opener_id))
            if opener is not None:
                await thread.remove_user(opener)
            await thread.send(
                f"🔒 Ticket `{ticket.number}` is being archived.",
                file=discord.File(
                    io.BytesIO(data),
                    filename=f"{ticket.number}-transcript.txt",
                ),
            )
            await thread.edit(locked=True, archived=True, reason=f"Support ticket {ticket.number} closed")
        except (discord.Forbidden, discord.HTTPException) as error:
            self.logger.error("Support ticket thread archival failed: " + self.safe_error(error), guild_id=guild.id)
        return None

    async def update_public_status(self, guild, ticket, content, *, view=UNSET_VIEW):
        channel = self.support_channel(guild)
        if channel is None or not ticket.public_message_id:
            return
        try:
            message = await channel.fetch_message(int(ticket.public_message_id))
            kwargs = {"content": content}
            if view is not UNSET_VIEW:
                kwargs["view"] = view
            await message.edit(**kwargs)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    def schedule_public_delete(self, guild_id, ticket):
        self.bot.loop.create_task(self.delete_public_status(guild_id, ticket))

    async def delete_public_status(self, guild_id, ticket):
        if ticket.public_delete_at:
            target = datetime.fromisoformat(ticket.public_delete_at)
            delay = max(0, (target - datetime.now(timezone.utc)).total_seconds())
            await asyncio.sleep(delay)
        guild = self.bot.get_guild(int(guild_id))
        if guild is None:
            return
        channel = self.support_channel(guild)
        if channel and ticket.public_message_id:
            try:
                message = await channel.fetch_message(int(ticket.public_message_id))
                await message.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

    async def cleanup_expired_statuses(self, guild):
        now = datetime.now(timezone.utc)
        for ticket in self.service.list(guild.id):
            if not ticket.public_delete_at:
                continue
            try:
                target = datetime.fromisoformat(ticket.public_delete_at)
            except ValueError:
                target = now
            if target <= now:
                await self.delete_public_status(guild.id, ticket)
            else:
                self.schedule_public_delete(guild.id, ticket)

    @property
    def status_delete_seconds(self):
        return max(5, min(3600, int(self.settings.get("status_delete_seconds", 30))))

    @property
    def thread_archive_minutes(self):
        selected = int(self.settings.get("thread_auto_archive_minutes", 1440))
        return min((60, 1440, 4320, 10080), key=lambda value: abs(value - selected))

    @staticmethod
    def _snowflake(value):
        return int(value) if value is not None else 0

    def ticket_from_context(self, interaction, ticketnumber):
        if ticketnumber:
            return self.service.get(interaction.guild_id, ticketnumber)
        ticket = self.service.find_by_thread(interaction.guild_id, interaction.channel_id)
        if ticket is None:
            raise SupportTicketError("Specify a ticket number when outside its private thread.")
        return ticket

    @app_commands.command(name="resolved", description="Resolve an assigned support ticket")
    @app_commands.describe(
        reason="Brief description of the resolution",
        ticketnumber="Ticket number; optional inside its private thread",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    async def resolved(self, interaction, reason: str, ticketnumber: str | None = None):
        if not is_moderator(interaction.user):
            return await interaction.response.send_message("❌ Moderator permission is required.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            ticket = self.ticket_from_context(interaction, ticketnumber)
            await self.resolve_ticket(interaction, ticket.number, reason)
        except SupportTicketError as error:
            await interaction.followup.send(f"❌ {error}", ephemeral=True)

    @app_commands.command(name="cancel", description="Cancel an assigned support ticket")
    @app_commands.describe(
        reason="Brief reason for cancellation",
        ticketnumber="Ticket number; optional inside its private thread",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    async def cancel(self, interaction, reason: str, ticketnumber: str | None = None):
        if not is_moderator(interaction.user):
            return await interaction.response.send_message("❌ Moderator permission is required.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            ticket = self.ticket_from_context(interaction, ticketnumber)
            await self.cancel_ticket(interaction, ticket.number, reason)
        except SupportTicketError as error:
            await interaction.followup.send(f"❌ {error}", ephemeral=True)

    @app_commands.command(name="ticket-status", description="Show a support ticket's current state")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    async def ticket_status(self, interaction, ticketnumber: str):
        if not is_moderator(interaction.user):
            return await interaction.response.send_message("❌ Moderator permission is required.", ephemeral=True)
        try:
            ticket = self.service.get(interaction.guild_id, ticketnumber)
        except SupportTicketError as error:
            return await interaction.response.send_message(f"❌ {error}", ephemeral=True)
        await interaction.response.send_message(embed=self.ticket_embed(ticket), ephemeral=True, suppress_embeds=True)

    @app_commands.command(name="ticket-list", description="List this server's active support tickets")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    async def ticket_list(self, interaction):
        if not is_moderator(interaction.user):
            return await interaction.response.send_message("❌ Moderator permission is required.", ephemeral=True)
        tickets = self.service.list(interaction.guild_id, active_only=True)
        text = "\n".join(
            f"• `{ticket.number}` — {ticket.status}"
            + (f" — assigned to <@{ticket.assigned_to}>" if ticket.assigned_to else "")
            for ticket in tickets
        ) or "No active support tickets."
        await interaction.response.send_message(text[:4000], ephemeral=True)

    @app_commands.command(name="ticket-reopen", description="Reopen a resolved or canceled support ticket")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def ticket_reopen(self, interaction, ticketnumber: str):
        permissions = interaction.user.guild_permissions
        if not (permissions.administrator or permissions.manage_guild):
            return await interaction.response.send_message("❌ Manage Server permission is required.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            closed_ticket = self.service.get(interaction.guild_id, ticketnumber)
            channel = self.support_channel(interaction.guild)
            thread = await self.resolve_thread(
                interaction.guild,
                closed_ticket.thread_id,
            )
            if thread is None:
                raise SupportTicketError(
                    "The original private ticket thread is unavailable."
                )
            ticket = self.service.reopen(
                interaction.guild_id,
                ticketnumber,
                interaction.user.id,
            )
            await thread.edit(
                archived=False,
                locked=False,
                reason=f"Support ticket {ticket.number} reopened",
            )
            opener = interaction.guild.get_member(int(ticket.opener_id))
            if opener is not None:
                await thread.add_user(opener)
            await thread.send(
                f"🔓 Ticket `{ticket.number}` was reopened by "
                f"{interaction.user.mention}.",
                allowed_mentions=discord.AllowedMentions(users=True),
            )
            if opener is not None:
                try:
                    await opener.send(
                        f"🔓 Your support ticket `{ticket.number}` in "
                        f"**{interaction.guild.name}** was reopened. Watch the "
                        "private support thread for further responses."
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
            public = await channel.send(
                f"🎫 Ticket `{ticket.number}` has been reopened.",
                view=TicketControlView(self, ticket),
            )
            ticket = self.service.update_delivery(interaction.guild_id, ticket.number, public_message_id=public.id)
            self.bot.add_view(
                TicketControlView(self, ticket),
                message_id=public.id,
            )
            await self.audit(
                interaction.guild,
                f"{self.plain_username(interaction.user)} reopened ticket "
                f"`{ticket.number}` opened by "
                f"{self.plain_username(opener, fallback=f'user ID {ticket.opener_id}')}.",
            )
            await interaction.followup.send(f"✅ Ticket `{ticket.number}` was reopened.", ephemeral=True)
        except SupportTicketError as error:
            await interaction.followup.send(f"❌ {error}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Support(bot))
