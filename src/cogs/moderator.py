"""Discord-only moderator setup commands and interactive configuration views."""

from __future__ import annotations

import re

import discord
from discord import app_commands
from discord.ext import commands


UNSET = "UNSET"


def _safe_channel_name(value: str) -> str:
    value = re.sub(r"[^a-z0-9-]+", "-", value.casefold()).strip("-")
    return value[:90] or "private-rolls"


class ManagedView(discord.ui.View):
    def __init__(self, cog, guild: discord.Guild, *, owner_id: int | None = None):
        super().__init__(timeout=300)
        self.cog = cog
        self.guild = guild
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild_id != self.guild.id:
            await interaction.response.send_message("This setup belongs to another server.", ephemeral=True)
            return False
        member = self.guild.get_member(interaction.user.id)
        permitted = bool(
            member
            and (
                member.guild_permissions.manage_guild
                or member.guild_permissions.administrator
                or interaction.user.id == self.owner_id
            )
        )
        if not permitted:
            await interaction.response.send_message(
                "You need Manage Server permission to use this setup.", ephemeral=True
            )
        return permitted

    async def finish(self, interaction, message: str):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content=message, view=self)
        self.stop()


class TextChannelPicker(discord.ui.ChannelSelect):
    def __init__(self, callback_handler, *, placeholder="Select a text channel"):
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text],
            row=1,
        )
        self.callback_handler = callback_handler

    async def callback(self, interaction):
        selected = self.values[0]
        guild = getattr(self.view, "guild", None)
        channel = guild.get_channel(selected.id) if guild is not None else None
        await self.callback_handler(interaction, channel or selected)


class RolePicker(discord.ui.RoleSelect):
    def __init__(self, callback_handler, *, placeholder="Select a role"):
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, row=1)
        self.callback_handler = callback_handler

    async def callback(self, interaction):
        selected = self.values[0]
        guild = getattr(self.view, "guild", None)
        role = guild.get_role(selected.id) if guild is not None else None
        await self.callback_handler(interaction, role or selected)


class UserPicker(discord.ui.UserSelect):
    def __init__(self, callback_handler):
        super().__init__(placeholder="Optionally select a server member", min_values=0, max_values=1, row=0)
        self.callback_handler = callback_handler

    async def callback(self, interaction):
        selected = self.values[0] if self.values else interaction.user
        guild = getattr(self.view, "guild", None)
        member = guild.get_member(selected.id) if guild is not None else None
        await self.callback_handler(interaction, member or selected)


class ModChannelView(ManagedView):
    def __init__(self, cog, guild, *, owner_id=None, onboarding=False):
        super().__init__(cog, guild, owner_id=owner_id)
        self.onboarding = onboarding
        self.add_item(TextChannelPicker(self.select_channel, placeholder="Select the moderator channel"))

    async def configured(self, interaction, channel):
        self.cog.set_value(self.guild, "mod_channel", str(channel.id))
        await self.cog.audit(self.guild, f"{interaction.user.mention} set the moderator channel to {channel.mention}.")
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"✅ Moderator channel set to {channel.mention}.", view=self
        )
        self.stop()
        await interaction.followup.send(
            "Would you also like to configure the Game Master role and channel?",
            view=OnboardingGMView(self.cog, self.guild, owner_id=interaction.user.id),
            ephemeral=not self.onboarding,
        )

    @discord.ui.button(label="Use/Create #mod-logs", style=discord.ButtonStyle.primary, row=0)
    async def default_channel(self, interaction, _button):
        channel = discord.utils.get(self.guild.text_channels, name="mod-logs")
        if channel is None:
            channel = await self.guild.create_text_channel(
                "mod-logs",
                overwrites=self.cog.private_overwrites(self.guild),
                reason=f"EyeBot moderator setup by {interaction.user}",
            )
        await self.configured(interaction, channel)

    async def select_channel(self, interaction, channel):
        await self.configured(interaction, channel)

    @discord.ui.button(label="Disable", style=discord.ButtonStyle.danger, row=0)
    async def disable(self, interaction, _button):
        self.cog.set_value(self.guild, "mod_channel", "DISABLED")
        await self.finish(interaction, "✅ Moderator-channel logging disabled.")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=0)
    async def cancel(self, interaction, _button):
        await self.finish(interaction, "Setup cancelled; no moderator-channel setting changed.")


class OnboardingGMView(ManagedView):
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(self, interaction, _button):
        await interaction.response.edit_message(
            content="Configure the Game Master role first:",
            view=GMRoleView(self.cog, self.guild, owner_id=interaction.user.id, continue_to_channel=True),
        )

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no(self, interaction, _button):
        await self.finish(interaction, "Moderator-channel setup complete.")


class GMMenuView(ManagedView):
    @discord.ui.button(label="1. GM Role", style=discord.ButtonStyle.primary)
    async def role(self, interaction, _button):
        await interaction.response.edit_message(
            content="Configure the Game Master role:",
            view=GMRoleView(self.cog, self.guild, owner_id=interaction.user.id),
        )

    @discord.ui.button(label="2. GM Channel", style=discord.ButtonStyle.primary)
    async def channel(self, interaction, _button):
        if self.cog.resolve_role(self.guild, "dm_role") is None:
            return await interaction.response.edit_message(
                content="A GM role must be configured before its private channel:",
                view=GMRoleView(self.cog, self.guild, owner_id=interaction.user.id, continue_to_channel=True),
            )
        await interaction.response.edit_message(
            content="Configure the private Game Master channel:",
            view=GMChannelView(self.cog, self.guild, owner_id=interaction.user.id),
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, _button):
        await self.finish(interaction, "Game Master setup cancelled.")


class GMRoleView(ManagedView):
    def __init__(self, cog, guild, *, owner_id=None, continue_to_channel=False):
        super().__init__(cog, guild, owner_id=owner_id)
        self.continue_to_channel = continue_to_channel
        self.add_item(RolePicker(self.select_role, placeholder="Select the Game Master role"))

    async def configured(self, interaction, role):
        self.cog.set_value(self.guild, "dm_role", role.name)
        channel = self.cog.resolve_channel(self.guild, "dm_channel")
        if channel:
            await self.cog.apply_private_channel_permissions(channel, self.guild, gm_role=role)
        await self.cog.audit(self.guild, f"{interaction.user.mention} set the Game Master role to {role.name}.")
        if self.continue_to_channel:
            return await interaction.response.edit_message(
                content=f"✅ GM role set to **{role.name}**. Now configure the GM channel:",
                view=GMChannelView(self.cog, self.guild, owner_id=interaction.user.id),
            )
        await self.finish(interaction, f"✅ Game Master role set to **{role.name}**.")

    @discord.ui.button(label="Create GM Role", style=discord.ButtonStyle.primary, row=0)
    async def create_role(self, interaction, _button):
        role = discord.utils.get(self.guild.roles, name="Game Master")
        if role is None:
            role = await self.guild.create_role(
                name="Game Master", reason=f"EyeBot GM setup by {interaction.user}"
            )
        await self.configured(interaction, role)

    async def select_role(self, interaction, role):
        if role.is_default() or role.managed:
            return await interaction.response.send_message(
                "Select an editable server role, not @everyone or an integration role.", ephemeral=True
            )
        await self.configured(interaction, role)

    @discord.ui.button(label="Disable", style=discord.ButtonStyle.danger, row=0)
    async def disable(self, interaction, _button):
        old_role = self.cog.resolve_role(self.guild, "dm_role")
        self.cog.set_value(self.guild, "dm_role", UNSET)
        channel = self.cog.resolve_channel(self.guild, "dm_channel")
        if channel and old_role:
            await channel.set_permissions(old_role, overwrite=None, reason="EyeBot GM role disabled")
        await self.finish(interaction, "✅ Game Master role cleared. The Discord role was not deleted.")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=0)
    async def cancel(self, interaction, _button):
        await self.finish(interaction, "Game Master role setup cancelled.")


class GMChannelView(ManagedView):
    def __init__(self, cog, guild, *, owner_id=None):
        super().__init__(cog, guild, owner_id=owner_id)
        self.add_item(TextChannelPicker(self.select_channel, placeholder="Select the Game Master channel"))

    async def configured(self, interaction, channel):
        role = self.cog.resolve_role(self.guild, "dm_role")
        if role is None:
            return await interaction.response.send_message(
                "Configure a Game Master role first.", ephemeral=True
            )
        await self.cog.apply_private_channel_permissions(channel, self.guild, gm_role=role)
        self.cog.set_value(self.guild, "dm_channel", str(channel.id))
        await self.cog.audit(self.guild, f"{interaction.user.mention} set the GM channel to {channel.mention}.")
        await self.finish(interaction, f"✅ Private Game Master channel set to {channel.mention}.")

    @discord.ui.button(label="Use/Create #gm-rolls", style=discord.ButtonStyle.primary, row=0)
    async def default_channel(self, interaction, _button):
        role = self.cog.resolve_role(self.guild, "dm_role")
        if role is None:
            return await interaction.response.edit_message(
                content="Configure a Game Master role first:",
                view=GMRoleView(self.cog, self.guild, owner_id=interaction.user.id, continue_to_channel=True),
            )
        channel = discord.utils.get(self.guild.text_channels, name="gm-rolls")
        if channel is None:
            channel = await self.guild.create_text_channel(
                "gm-rolls",
                overwrites=self.cog.private_overwrites(self.guild, gm_role=role),
                reason=f"EyeBot GM setup by {interaction.user}",
            )
        await self.configured(interaction, channel)

    async def select_channel(self, interaction, channel):
        await self.configured(interaction, channel)

    @discord.ui.button(label="Disable", style=discord.ButtonStyle.danger, row=0)
    async def disable(self, interaction, _button):
        self.cog.set_value(self.guild, "dm_channel", UNSET)
        await self.finish(interaction, "✅ Game Master channel cleared. The Discord channel was not deleted.")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=0)
    async def cancel(self, interaction, _button):
        await self.finish(interaction, "Game Master channel setup cancelled.")


class PrivateRollView(ManagedView):
    def __init__(self, cog, guild, target):
        super().__init__(cog, guild, owner_id=None)
        self.target = target
        self.add_item(UserPicker(self.select_user))
        self.add_item(TextChannelPicker(self.select_channel, placeholder="Select the private-roll channel"))

    async def select_user(self, interaction, user):
        member = self.guild.get_member(user.id)
        if member is None:
            return await interaction.response.send_message("Select a member of this server.", ephemeral=True)
        self.target = member
        await interaction.response.send_message(
            f"Private-roll target changed to **{member.display_name}**. Choose an action below.", ephemeral=True
        )

    async def configured(self, interaction, channel):
        if not channel.permissions_for(self.target).send_messages:
            await channel.set_permissions(
                self.target,
                view_channel=True,
                read_message_history=True,
                send_messages=True,
                reason=f"EyeBot private-roll setup by {interaction.user}",
            )
        self.cog.set_user_channel(self.guild, self.target.id, str(channel.id))
        await self.cog.audit(self.guild, f"{interaction.user.mention} set {self.target.name}'s private-roll channel to {channel.mention}.")
        await self.finish(interaction, f"✅ **{self.target.display_name}** will use {channel.mention} for private rolls.")

    @discord.ui.button(label="Create Channel", style=discord.ButtonStyle.primary, row=2)
    async def create_channel(self, interaction, _button):
        channel = await self.guild.create_text_channel(
            _safe_channel_name(f"{self.target.display_name}-rolls"),
            overwrites=self.cog.private_overwrites(self.guild, extra_member=self.target),
            reason=f"EyeBot private-roll setup by {interaction.user}",
        )
        await self.configured(interaction, channel)

    async def select_channel(self, interaction, channel):
        await self.configured(interaction, channel)

    @discord.ui.button(label="Disable", style=discord.ButtonStyle.danger, row=2)
    async def disable(self, interaction, _button):
        self.cog.set_user_channel(self.guild, self.target.id, None)
        await self.finish(interaction, f"✅ Private-roll routing disabled for **{self.target.display_name}**.")

    @discord.ui.button(label="List Assignments", style=discord.ButtonStyle.secondary, row=3)
    async def list_assignments(self, interaction, _button):
        assignments = self.cog.guild_config(self.guild).get("user_channels", {})
        lines = []
        for user_id, channel_id in assignments.items():
            member = self.guild.get_member(int(user_id)) if str(user_id).isdigit() else None
            channel = self.guild.get_channel(int(channel_id)) if str(channel_id).isdigit() else None
            if member is not None and channel is not None:
                lines.append(f"• **{member.display_name}** → {channel.mention}")
        content = (
            "🔒 **Private-roll channel assignments**\n" + "\n".join(lines)
            if lines
            else "📭 No private-roll channels are configured in this server."
        )
        await interaction.response.send_message(content[:2000], ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=2)
    async def cancel(self, interaction, _button):
        await self.finish(interaction, "Private-roll setup cancelled.")


ROLE_PERMISSIONS = {
    "admin_role": discord.Permissions(administrator=True),
    "mod_role": discord.Permissions(
        view_audit_log=True,
        kick_members=True,
        ban_members=True,
        manage_channels=True,
        manage_messages=True,
        moderate_members=True,
        manage_nicknames=True,
    ),
}


class StaffRoleView(ManagedView):
    def __init__(self, cog, guild, key, label, default_name, *, owner_id=None):
        super().__init__(cog, guild, owner_id=owner_id)
        self.key, self.label, self.default_name = key, label, default_name
        self.add_item(RolePicker(self.select_role, placeholder=f"Select the {label} role"))

    async def configured(self, interaction, role):
        try:
            await role.edit(
                permissions=ROLE_PERMISSIONS[self.key],
                reason=f"EyeBot {self.label} role setup by {interaction.user}",
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "EyeBot cannot edit that role. Move the EyeBot role above it and grant Manage Roles.", ephemeral=True
            )
        self.cog.set_value(self.guild, self.key, str(role.id))
        await self.cog.audit(self.guild, f"{interaction.user.mention} set the {self.label} role to {role.name}.")
        await self.finish(interaction, f"✅ {self.label.title()} role set to **{role.name}** with the required permissions.")

    @discord.ui.button(label="Create Role", style=discord.ButtonStyle.primary, row=0)
    async def create_role(self, interaction, _button):
        role = await self.guild.create_role(
            name=self.default_name,
            permissions=ROLE_PERMISSIONS[self.key],
            reason=f"EyeBot {self.label} role setup by {interaction.user}",
        )
        await self.configured(interaction, role)

    async def select_role(self, interaction, role):
        if role.is_default() or role.managed:
            return await interaction.response.send_message(
                "Select an editable server role, not @everyone or an integration role.", ephemeral=True
            )
        await self.configured(interaction, role)

    @discord.ui.button(label="Disable", style=discord.ButtonStyle.danger, row=0)
    async def disable(self, interaction, _button):
        self.cog.set_value(self.guild, self.key, UNSET)
        await self.finish(interaction, f"✅ Configured {self.label} role cleared. The Discord role was not deleted.")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=0)
    async def cancel(self, interaction, _button):
        await self.finish(interaction, f"{self.label.title()} role setup cancelled.")


class Moderator(commands.GroupCog, group_name="set", group_description="Configure EyeBot channels and staff roles"):
    def __init__(self, bot):
        self.bot = bot
        self.service = bot.platform_config_service

    def guild_config(self, guild):
        return self.service.ensure_discord_guild(
            str(guild.id), guild.name, self.bot.config.get("prefix", "!")
        )

    def set_value(self, guild, key, value):
        self.guild_config(guild)[key] = value
        self.service.save_discord_guild(guild.id)

    def set_user_channel(self, guild, user_id, channel_id):
        channels = self.guild_config(guild).setdefault("user_channels", {})
        if channel_id is None:
            channels.pop(str(user_id), None)
        else:
            channels[str(user_id)] = str(channel_id)
        self.service.save_discord_guild(guild.id)

    def resolve_channel(self, guild, key):
        value = self.guild_config(guild).get(key, UNSET)
        return guild.get_channel(int(value)) if str(value).isdigit() else None

    def resolve_role(self, guild, key):
        value = self.guild_config(guild).get(key, UNSET)
        if str(value).isdigit():
            return guild.get_role(int(value))
        return discord.utils.get(guild.roles, name=value) if value != UNSET else None

    def private_overwrites(self, guild, *, gm_role=None, extra_member=None):
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, read_message_history=True, send_messages=True, manage_messages=True
            ),
        }
        for role in guild.roles:
            if role.permissions.administrator or role.permissions.manage_guild:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, read_message_history=True, send_messages=True
                )
        for key in ("admin_role", "mod_role"):
            role = self.resolve_role(guild, key)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, read_message_history=True, send_messages=True
                )
        if gm_role:
            overwrites[gm_role] = discord.PermissionOverwrite(
                view_channel=True, read_message_history=True, send_messages=True
            )
        if extra_member:
            overwrites[extra_member] = discord.PermissionOverwrite(
                view_channel=True, read_message_history=True, send_messages=True
            )
        return overwrites

    async def apply_private_channel_permissions(self, channel, guild, *, gm_role=None):
        await channel.edit(
            overwrites=self.private_overwrites(guild, gm_role=gm_role),
            reason="EyeBot private channel configuration",
        )

    async def audit(self, guild, content):
        handler = getattr(self.bot, "mod_channel_handler", None)
        if handler:
            await handler.send(guild, content=content)

    async def prompt_modchannel_setup(self, guild):
        if self.resolve_channel(guild, "mod_channel") is not None:
            return
        destination = guild.system_channel
        if destination is None or not destination.permissions_for(guild.me).send_messages:
            destination = next(
                (channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages),
                None,
            )
        if destination:
            await destination.send(
                "EyeBot needs a moderator channel. A server administrator can complete setup below.",
                view=ModChannelView(self, guild, onboarding=True),
                allowed_mentions=discord.AllowedMentions.none(),
            )

    @app_commands.command(name="modchannel", description="Configure the moderator audit channel")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def modchannel(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Configure the moderator channel:",
            view=ModChannelView(self, interaction.guild, owner_id=interaction.user.id),
            ephemeral=True,
        )

    @app_commands.command(name="gm", description="Configure the Game Master role and private channel")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def gm(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Configure the GM role first, then the private GM channel:",
            view=GMMenuView(self, interaction.guild, owner_id=interaction.user.id),
            ephemeral=True,
        )

    @app_commands.command(name="privateroll", description="Configure a member's private-roll channel")
    @app_commands.describe(member="Member to configure; defaults to yourself")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def privateroll(self, interaction: discord.Interaction, member: discord.Member | None = None):
        target = member or interaction.user
        channel_id = self.guild_config(interaction.guild).get("user_channels", {}).get(str(target.id))
        channel = interaction.guild.get_channel(int(channel_id)) if str(channel_id).isdigit() else None
        current = channel.mention if channel is not None else "not configured"
        await interaction.response.send_message(
            f"Configure the private-roll channel for **{target.display_name}**. Current: {current}.",
            view=PrivateRollView(self, interaction.guild, target),
            ephemeral=True,
        )

    async def open_role_setup(self, interaction, setting):
        role_setup = self.bot.get_cog("Roleplay")
        if role_setup is None:
            await interaction.response.send_message(
                "EyeBot's role setup service is unavailable. Please contact the bot administrator.",
                ephemeral=True,
            )
            return
        await role_setup.open_menu(interaction, setting)

    @app_commands.command(name="modrole", description="Configure the Moderator role")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    @app_commands.guild_only()
    async def modrole(self, interaction: discord.Interaction):
        await self.open_role_setup(interaction, "mod_role")

    @app_commands.command(name="adminrole", description="Configure the Admin role")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    @app_commands.guild_only()
    async def adminrole(self, interaction: discord.Interaction):
        await self.open_role_setup(interaction, "admin_role")

    @app_commands.command(name="gmrole", description="Configure the GM role")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    @app_commands.guild_only()
    async def gmrole(self, interaction: discord.Interaction):
        await self.open_role_setup(interaction, "dm_role")

    @app_commands.command(name="playerrole", description="Configure the Player role")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True, manage_channels=True)
    @app_commands.guild_only()
    async def playerrole(self, interaction: discord.Interaction):
        await self.open_role_setup(interaction, "player_role")

    @app_commands.command(name="player", description="Assign the configured Player role to a member")
    @app_commands.describe(member="Member who does not already have the Player role")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    @app_commands.guild_only()
    async def player(self, interaction: discord.Interaction, member: discord.Member):
        role_setup = self.bot.get_cog("Roleplay")
        if role_setup is None:
            return await interaction.response.send_message(
                "EyeBot's roleplay setup service is unavailable.", ephemeral=True
            )
        await role_setup.assign_player(interaction, member)

    @app_commands.command(name="playerlounge", description="Create a private lounge for an existing player")
    @app_commands.describe(member="Player who does not already have a private lounge")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    @app_commands.guild_only()
    async def playerlounge(self, interaction: discord.Interaction, member: discord.Member):
        role_setup = self.bot.get_cog("Roleplay")
        if role_setup is None:
            return await interaction.response.send_message(
                "EyeBot's roleplay setup service is unavailable.", ephemeral=True
            )
        await role_setup.prompt_player_lounge(interaction, member)

    @app_commands.command(name="gmchannel", description="Configure the private GM roll channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    @app_commands.guild_only()
    async def gmchannel(self, interaction: discord.Interaction):
        role_setup = self.bot.get_cog("Roleplay")
        if role_setup is None:
            return await interaction.response.send_message(
                "EyeBot's roleplay setup service is unavailable.", ephemeral=True
            )
        await role_setup.open_gm_channel(interaction, self)


async def setup(bot):
    await bot.add_cog(Moderator(bot))
