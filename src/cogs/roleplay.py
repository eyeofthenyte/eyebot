"""Discord-only interactive server role and player-lounge setup."""

from __future__ import annotations

import re

import discord
from discord import app_commands
from discord.ext import commands


ROLE_SPECS = {
    "mod_role": ("Moderator", discord.Permissions(manage_messages=True, moderate_members=True, manage_threads=True, view_audit_log=True)),
    "admin_role": ("Admin", discord.Permissions(administrator=True)),
    "dm_role": ("DM", discord.Permissions(manage_messages=True, manage_threads=True)),
    "player_role": ("Player", discord.Permissions.none()),
}


def private_lounge_name(username: str) -> str:
    suffix = "'s Private Lounge"
    clean = (username or "Player").strip() or "Player"
    return f"{clean[:100 - len(suffix)]}{suffix}"


def player_channel_name(username: str, suffix: str) -> str:
    clean = re.sub(r"[^a-z0-9_-]+", "-", (username or "player").lower())
    clean = re.sub(r"-+", "-", clean).strip("-_") or "player"
    return f"{clean[:99 - len(suffix)]}-{suffix}"


def configured_gm_roles(guild: discord.Guild, config: dict) -> list[discord.Role]:
    roles = []
    for key in ("admin_role", "mod_role", "dm_role"):
        name = config.get(key)
        if isinstance(name, str) and name and name.upper() != "UNSET":
            role = discord.utils.get(guild.roles, name=name)
            if role is not None and role not in roles:
                roles.append(role)
    return roles


class ExpiringView(discord.ui.View):
    """Invoker-only view whose ephemeral message disappears on timeout."""

    def __init__(self, owner_id: int, *, timeout: float = 120) -> None:
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.origin: discord.Interaction | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.owner_id:
            return True
        await interaction.response.send_message(
            "Only the administrator who opened this menu can use it.", ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        if self.origin is not None:
            try:
                await self.origin.delete_original_response()
            except (discord.NotFound, discord.HTTPException):
                pass

    async def remove_origin(self) -> None:
        self.stop()
        if self.origin is not None:
            try:
                await self.origin.delete_original_response()
            except (discord.NotFound, discord.HTTPException):
                pass


class CreateRoleModal(discord.ui.Modal, title="Create server role"):
    role_name = discord.ui.TextInput(label="Role name", min_length=1, max_length=100)

    def __init__(self, menu: "RoleSetupView") -> None:
        super().__init__(timeout=120)
        self.menu = menu

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            role = await self.menu.cog.create_and_store_role(
                interaction.guild, self.menu.setting, str(self.role_name), interaction.user
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I could not create that role. Check my Manage Roles permission and role position.",
                ephemeral=True,
            )
            return
        await self.menu.remove_origin()
        await self.menu.cog.role_saved_response(interaction, self.menu.setting, role)


class ExistingPlayerRoleSelect(discord.ui.RoleSelect):
    def __init__(self) -> None:
        super().__init__(placeholder="Select an existing Player role", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        menu: RoleSetupView = self.view  # type: ignore[assignment]
        role = self.values[0]
        if role.is_default() or role.managed:
            await interaction.response.send_message(
                "Select a normal server role that EyeBot can assign.", ephemeral=True
            )
            return
        await menu.cog.store_role(interaction.guild, menu.setting, role)
        await menu.cog.role_saved_response(interaction, menu.setting, role, edit=True)
        menu.stop()


class RoleSetupView(ExpiringView):
    def __init__(self, cog: "Roleplay", owner_id: int, setting: str) -> None:
        super().__init__(owner_id)
        self.cog = cog
        self.setting = setting
        if setting == "player_role":
            self.add_item(ExistingPlayerRoleSelect())

    @discord.ui.button(label="Default", style=discord.ButtonStyle.primary)
    async def default(self, interaction: discord.Interaction, _button) -> None:
        try:
            role = await self.cog.create_and_store_role(
                interaction.guild, self.setting, ROLE_SPECS[self.setting][0], interaction.user
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I could not create that role. Check my Manage Roles permission and role position.",
                ephemeral=True,
            )
            return
        await self.cog.role_saved_response(interaction, self.setting, role, edit=True)
        self.stop()

    @discord.ui.button(label="Create", style=discord.ButtonStyle.success)
    async def create(self, interaction: discord.Interaction, _button) -> None:
        await interaction.response.send_modal(CreateRoleModal(self))

    @discord.ui.button(label="Disable", style=discord.ButtonStyle.danger)
    async def disable(self, interaction: discord.Interaction, _button) -> None:
        await self.cog.store_role(interaction.guild, self.setting, None)
        await interaction.response.edit_message(
            content=f"{self.cog.label(self.setting)} has been disabled.", view=None
        )
        self.stop()


class AddPlayerPrompt(ExpiringView):
    def __init__(self, cog: "Roleplay", owner_id: int, role: discord.Role) -> None:
        super().__init__(owner_id)
        self.cog = cog
        self.role = role

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, _button) -> None:
        view = PlayerSelectView(self.cog, self.owner_id, self.role)
        view.origin = self.origin
        await interaction.response.edit_message(
            content="Select or search for a member who does not already have the Player role.",
            view=view,
        )
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no(self, interaction: discord.Interaction, _button) -> None:
        await interaction.response.edit_message(content="Player role saved.", view=None)
        self.stop()


class PlayerSelect(discord.ui.UserSelect):
    def __init__(self) -> None:
        super().__init__(placeholder="Search for or select a member", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: PlayerSelectView = self.view  # type: ignore[assignment]
        member = interaction.guild.get_member(self.values[0].id)
        if member is None or member.bot:
            await interaction.response.send_message(
                "Select a non-bot member of this server.", ephemeral=True
            )
            return
        if view.role in member.roles:
            await interaction.response.send_message(
                "That member already has the Player role.", ephemeral=True
            )
            return
        try:
            await member.add_roles(view.role, reason=f"Player setup by {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message(
                "I could not assign that role. Check my Manage Roles permission and role position.",
                ephemeral=True,
            )
            return
        lounge = LoungePrompt(view.cog, view.owner_id, member)
        lounge.origin = view.origin
        await interaction.response.edit_message(
            content=(f"Added {member.mention} to {view.role.mention}. "
                     "Create this player's private lounge channels?"),
            view=lounge,
        )
        view.stop()


class PlayerSelectView(ExpiringView):
    def __init__(self, cog: "Roleplay", owner_id: int, role: discord.Role) -> None:
        super().__init__(owner_id)
        self.cog = cog
        self.role = role
        self.add_item(PlayerSelect())


class LoungePrompt(ExpiringView):
    def __init__(self, cog: "Roleplay", owner_id: int, member: discord.Member) -> None:
        super().__init__(owner_id)
        self.cog = cog
        self.member = member

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, _button) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            category, channels = await self.cog.create_private_lounge(
                interaction.guild, self.member, interaction.user
            )
        except discord.Forbidden:
            await interaction.edit_original_response(
                content="I could not create the lounge. Check my Manage Channels permission.",
                view=None,
            )
            return
        mentions = ", ".join(channel.mention for channel in channels)
        await interaction.edit_original_response(
            content=f"Created **{category.name}** with {mentions}.", view=None
        )
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no(self, interaction: discord.Interaction, _button) -> None:
        await interaction.response.edit_message(content="Player setup complete.", view=None)
        self.stop()


class Roleplay(commands.Cog):
    """Role-setup workflow used by the shared ``/set`` command group."""
    def __init__(self, bot) -> None:
        self.bot = bot

    @staticmethod
    def label(setting: str) -> str:
        return setting.replace("_", " ").title()

    async def store_role(self, guild, setting: str, role: discord.Role | None) -> None:
        service = self.bot.platform_config_service
        config = service.ensure_discord_guild(
            str(guild.id), guild.name, self.bot.config.get("prefix", "!")
        )
        config[setting] = role.name if role else None
        service.save_discord_guild(guild.id)

    async def create_and_store_role(self, guild, setting: str, name: str, actor):
        name = name.strip() or ROLE_SPECS[setting][0]
        role = discord.utils.get(guild.roles, name=name)
        if role is None:
            role = await guild.create_role(
                name=name,
                permissions=ROLE_SPECS[setting][1],
                reason=f"EyeBot {self.label(setting)} setup by {actor}",
            )
        await self.store_role(guild, setting, role)
        return role

    async def role_saved_response(self, interaction, setting, role, *, edit=False):
        content = f"{self.label(setting)} is now {role.mention}."
        view = None
        if setting == "player_role":
            content += " Would you like to make someone a player now?"
            view = AddPlayerPrompt(self, interaction.user.id, role)
            view.origin = interaction
        if edit:
            await interaction.response.edit_message(content=content, view=view)
        else:
            await interaction.response.send_message(content, view=view, ephemeral=True)

    async def create_private_lounge(self, guild, member, actor):
        service = self.bot.platform_config_service
        config = service.ensure_discord_guild(
            str(guild.id), guild.name, self.bot.config.get("prefix", "!")
        )
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        if guild.me:
            overwrites[guild.me] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True, manage_channels=True
            )
        for role in configured_gm_roles(guild, config):
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True, manage_messages=True
            )
        reason = f"Private player lounge setup by {actor}"
        category_name = private_lounge_name(member.name)
        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            category = await guild.create_category(category_name, overwrites=overwrites, reason=reason)
        else:
            await category.edit(overwrites=overwrites, reason=reason)

        channels = []
        for suffix in ("notes", "references", "private-rp"):
            name = player_channel_name(member.name, suffix)
            channel = discord.utils.get(category.channels, name=name)
            if channel is None:
                if suffix == "references" and hasattr(guild, "create_forum"):
                    try:
                        channel = await guild.create_forum(
                            name, category=category, reason=reason, media=True
                        )
                    except (TypeError, discord.HTTPException):
                        channel = await guild.create_text_channel(
                            name, category=category, reason=reason
                        )
                else:
                    channel = await guild.create_text_channel(
                        name, category=category, reason=reason
                    )
            channels.append(channel)
        for channel in category.channels:
            await channel.edit(sync_permissions=True, reason=reason)
        return category, channels

    async def open_menu(self, interaction, setting: str) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("Use this command in a server.", ephemeral=True)
            return
        view = RoleSetupView(self, interaction.user.id, setting)
        await interaction.response.send_message(
            f"Configure the **{self.label(setting)}**. This menu expires in 2 minutes.",
            view=view, ephemeral=True,
        )
        view.origin = interaction

    async def modrole(self, interaction: discord.Interaction):
        await self.open_menu(interaction, "mod_role")

    async def adminrole(self, interaction: discord.Interaction):
        await self.open_menu(interaction, "admin_role")

    async def gmrole(self, interaction: discord.Interaction):
        await self.open_menu(interaction, "dm_role")

    async def playerrole(self, interaction: discord.Interaction):
        await self.open_menu(interaction, "player_role")

    def configured_player_role(self, guild):
        service = self.bot.platform_config_service
        config = service.ensure_discord_guild(
            str(guild.id), guild.name, self.bot.config.get("prefix", "!")
        )
        value = config.get("player_role")
        if value in (None, "", "UNSET"):
            return None
        if str(value).isdigit():
            return guild.get_role(int(value))
        return discord.utils.get(guild.roles, name=value)

    async def assign_player(self, interaction, member):
        role = self.configured_player_role(interaction.guild)
        if role is None:
            return await interaction.response.send_message(
                "Configure the Player role first with `/set playerrole`.", ephemeral=True
            )
        if member.bot:
            return await interaction.response.send_message(
                "Bot accounts cannot be assigned the Player role.", ephemeral=True
            )
        if role in member.roles:
            return await interaction.response.send_message(
                f"{member.mention} already has the {role.mention} role.", ephemeral=True
            )
        try:
            await member.add_roles(role, reason=f"Player setup by {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message(
                "I could not assign that role. Check my Manage Roles permission and role position.",
                ephemeral=True,
            )
        await interaction.response.send_message(
            f"Added {member.mention} to {role.mention}.", ephemeral=True
        )

    async def prompt_player_lounge(self, interaction, member):
        role = self.configured_player_role(interaction.guild)
        if role is None:
            return await interaction.response.send_message(
                "Configure the Player role first with `/set playerrole`.", ephemeral=True
            )
        if role not in member.roles:
            return await interaction.response.send_message(
                f"{member.mention} must have the {role.mention} role first. Use `/set player`.",
                ephemeral=True,
            )
        category_name = private_lounge_name(member.name)
        if discord.utils.get(interaction.guild.categories, name=category_name) is not None:
            return await interaction.response.send_message(
                f"{member.mention} already has **{category_name}**.", ephemeral=True
            )
        view = LoungePrompt(self, interaction.user.id, member)
        await interaction.response.send_message(
            f"Create **{category_name}** for {member.mention}?",
            view=view,
            ephemeral=True,
        )
        view.origin = interaction

    async def open_gm_channel(self, interaction, moderator_cog):
        from cogs.moderator import GMChannelView, GMRoleView

        if moderator_cog.resolve_role(interaction.guild, "dm_role") is None:
            return await interaction.response.send_message(
                "A GM role must be configured before its private channel:",
                view=GMRoleView(
                    moderator_cog,
                    interaction.guild,
                    owner_id=interaction.user.id,
                    continue_to_channel=True,
                ),
                ephemeral=True,
            )
        await interaction.response.send_message(
            "Configure the private Game Master channel:",
            view=GMChannelView(
                moderator_cog,
                interaction.guild,
                owner_id=interaction.user.id,
            ),
            ephemeral=True,
        )

    async def cog_app_command_error(self, interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            message = "You need the Manage Server permission to use this command."
        elif isinstance(error, app_commands.BotMissingPermissions):
            message = "EyeBot is missing required permissions: " + ", ".join(error.missing_permissions)
        else:
            message = "Role setup failed unexpectedly. Please check the bot log."
            self.bot.logger.error(f"Slash role setup error: {error}")
        sender = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
        await sender(message, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Roleplay(bot))
