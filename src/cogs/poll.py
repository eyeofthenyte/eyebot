"""Discord reaction polls and portable livestream-chat polls."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks

from services.modChannelService import ModChannelHandler
from services.pollService import (
    PollError,
    PollService,
    format_duration,
    format_portable_results,
    parse_portable_duration,
    parse_portable_poll,
)


POLL_EMOJIS = (
    "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "✅", "❌", "👍", "👎", "❤️",
    "🔥", "🎲", "⚔️", "🛡️", "🧙", "🐉", "⭐", "🌙", "☀️", "🎉",
)
def is_moderator(member) -> bool:
    permissions = getattr(member, "guild_permissions", None)
    return bool(permissions and (
        permissions.administrator or permissions.manage_guild or permissions.manage_messages
    ))


def poll_embed(poll) -> discord.Embed:
    timestamp = int(datetime.fromisoformat(poll.ends_at).timestamp())
    counts = [0] * len(poll.options)
    for selected in poll.votes.values():
        if 0 <= int(selected) < len(counts):
            counts[int(selected)] += 1
    embed = discord.Embed(title=poll.title, description=poll.description, color=0x5865F2)
    for emoji, option, count in zip(poll.emojis, poll.options, counts):
        embed.add_field(name=f"{emoji} {count}", value=option, inline=False)
    embed.add_field(name="Poll ends", value=f"<t:{timestamp}:R> (<t:{timestamp}:F>)", inline=False)
    embed.set_footer(text="React with one listed emoji. Your first vote is final.")
    return embed


class PollDetailsModal(discord.ui.Modal, title="Create a Poll"):
    duration = discord.ui.TextInput(
        label="Duration", placeholder="30m, 2h, or 1d (maximum 30 days)", max_length=8
    )
    poll_title = discord.ui.TextInput(label="Poll title", max_length=200)
    description = discord.ui.TextInput(
        label="Description", style=discord.TextStyle.paragraph, max_length=2000
    )
    option_1 = discord.ui.TextInput(label="Option 1", max_length=300)
    option_2 = discord.ui.TextInput(label="Option 2", max_length=300)

    def __init__(self, cog: "PollCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            duration = parse_portable_duration(self.duration.value)
        except PollError as error:
            return await interaction.response.send_message(f"❌ {error}", ephemeral=True)
        draft = {
            "duration": duration,
            "title": self.poll_title.value.strip(),
            "description": self.description.value.strip(),
            "options": [self.option_1.value.strip(), self.option_2.value.strip()],
        }
        await interaction.response.send_message(
            "Add up to three more options, or continue with these two options.",
            view=AdditionalOptionsView(self.cog, draft), ephemeral=True,
        )


class ExtraOptionsModal(discord.ui.Modal, title="Optional Poll Options"):
    option_3 = discord.ui.TextInput(label="Option 3", required=False, max_length=300)
    option_4 = discord.ui.TextInput(label="Option 4", required=False, max_length=300)
    option_5 = discord.ui.TextInput(label="Option 5", required=False, max_length=300)

    def __init__(self, cog: "PollCog", draft):
        super().__init__()
        self.cog = cog
        self.draft = draft

    async def on_submit(self, interaction: discord.Interaction):
        extras = [self.option_3.value, self.option_4.value, self.option_5.value]
        self.draft["options"] = self.draft["options"] + [
            value.strip() for value in extras if value.strip()
        ]
        view = EmojiSetupView(self.cog, self.draft, interaction.guild)
        await interaction.response.edit_message(
            content=view.prompt(), view=view,
        )


class AdditionalOptionsView(discord.ui.View):
    def __init__(self, cog: "PollCog", draft):
        super().__init__(timeout=900)
        self.cog = cog
        self.draft = draft

    @discord.ui.button(label="Use 2 Options", style=discord.ButtonStyle.primary)
    async def use_two(self, interaction, _button):
        view = EmojiSetupView(self.cog, self.draft, interaction.guild)
        await interaction.response.edit_message(
            content=view.prompt(), view=view,
        )

    @discord.ui.button(label="Add Options 3–5", style=discord.ButtonStyle.secondary)
    async def add_more(self, interaction, _button):
        await interaction.response.send_modal(ExtraOptionsModal(self.cog, self.draft))


class EmojiSetupSelect(discord.ui.Select):
    def __init__(self, view: "EmojiSetupView"):
        start = view.page * 25
        page_items = view.available_emojis[start:start + 25]
        choices = [
            discord.SelectOption(label=label[:100], value=value, emoji=display)
            for value, label, display in page_items
        ]
        option = view.draft["options"][view.option_index]
        super().__init__(
            placeholder=f"Reaction for option {view.option_index + 1}: {option[:55]}",
            min_values=1, max_values=1, options=choices, row=0,
        )
        self.setup_view = view

    async def callback(self, interaction: discord.Interaction):
        await self.setup_view.accept_emoji(interaction, self.values[0])


class ManualEmojiModal(discord.ui.Modal, title="Enter Any Emoji"):
    emoji = discord.ui.TextInput(
        label="Unicode or server emoji",
        placeholder="Paste 😀 or <:server_emoji:123456789>",
        max_length=100,
    )

    def __init__(self, setup_view: "EmojiSetupView"):
        super().__init__()
        self.setup_view = setup_view

    async def on_submit(self, interaction: discord.Interaction):
        value = self.emoji.value.strip()
        partial = discord.PartialEmoji.from_str(value)
        if partial.id is not None:
            guild_emoji = interaction.guild.get_emoji(partial.id)
            usable = getattr(guild_emoji, "is_usable", None) if guild_emoji else None
            if guild_emoji is None or (callable(usable) and not usable()):
                return await interaction.response.send_message(
                    "❌ That custom emoji is not available to EyeBot in this server.", ephemeral=True
                )
            value = str(guild_emoji)
        await self.setup_view.accept_emoji(interaction, value)


class EmojiSetupView(discord.ui.View):
    def __init__(self, cog: "PollCog", draft, guild):
        super().__init__(timeout=900)
        self.cog = cog
        self.draft = draft
        self.guild = guild
        self.emojis = []
        self.option_index = 0
        self.page = 0
        standard = [(emoji, f"Standard {emoji}", emoji) for emoji in POLL_EMOJIS]
        custom = []
        for emoji in getattr(guild, "emojis", ()):
            usable = getattr(emoji, "is_usable", None)
            if callable(usable) and not usable():
                continue
            custom.append((str(emoji), f":{emoji.name}:", emoji))
        self.catalog = standard + custom
        self.rebuild()

    @property
    def available_emojis(self):
        selected = set(self.emojis)
        return [item for item in self.catalog if item[0] not in selected]

    @property
    def page_count(self):
        return max(1, (len(self.available_emojis) + 24) // 25)

    def prompt(self):
        option = self.draft["options"][self.option_index]
        return (
            f"Choose a reaction for option {self.option_index + 1}: **{option}** "
            f"(emoji page {self.page + 1}/{self.page_count}). Use **Enter Any Emoji** "
            "to paste another Unicode emoji."
        )

    async def accept_emoji(self, interaction, value):
        if value in self.emojis:
            return await interaction.response.send_message(
                "❌ Each option must use a different emoji.", ephemeral=True
            )
        self.emojis.append(value)
        self.option_index += 1
        self.page = 0
        if self.option_index == len(self.draft["options"]):
            await interaction.response.defer(ephemeral=True, thinking=True)
            return await self.cog.create_discord_poll(interaction, self.draft, self.emojis)
        self.rebuild()
        await interaction.response.edit_message(content=self.prompt(), view=self)

    def rebuild(self):
        self.clear_items()
        self.page = min(self.page, self.page_count - 1)
        self.add_item(EmojiSetupSelect(self))
        previous = discord.ui.Button(
            label="Previous Emoji Page", style=discord.ButtonStyle.secondary,
            disabled=self.page == 0, row=1,
        )
        next_page = discord.ui.Button(
            label="Next Emoji Page", style=discord.ButtonStyle.secondary,
            disabled=self.page >= self.page_count - 1, row=1,
        )
        manual = discord.ui.Button(
            label="Enter Any Emoji", style=discord.ButtonStyle.primary, row=2,
        )

        async def previous_callback(interaction):
            self.page -= 1
            self.rebuild()
            await interaction.response.edit_message(content=self.prompt(), view=self)

        async def next_callback(interaction):
            self.page += 1
            self.rebuild()
            await interaction.response.edit_message(content=self.prompt(), view=self)

        async def manual_callback(interaction):
            await interaction.response.send_modal(ManualEmojiModal(self))

        previous.callback = previous_callback
        next_page.callback = next_callback
        manual.callback = manual_callback
        self.add_item(previous)
        self.add_item(next_page)
        self.add_item(manual)


def results_embed(poll) -> discord.Embed:
    embed = discord.Embed(title=poll.title, color=0x57F287)
    for emoji, option, count in zip(poll.emojis, poll.options, poll.results):
        embed.add_field(name=f"{emoji} {count}", value=option, inline=False)
    embed.set_footer(text="Final poll results")
    return embed


class PollButton(discord.ui.Button):
    def __init__(self, cog: "PollCog", poll, action: str, *, disabled=False):
        publish = action == "publish"
        super().__init__(
            label="Publish Poll Results" if publish else "Cancel Poll",
            emoji="📣" if publish else "✖️",
            style=discord.ButtonStyle.success if publish else discord.ButtonStyle.danger,
            custom_id=f"eyebot:poll:{action}:{poll.id}",
            disabled=disabled,
        )
        self.cog = cog
        self.poll_id = poll.id
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        if not is_moderator(interaction.user):
            return await interaction.response.send_message(
                "❌ Only moderators may manage polls.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True, thinking=True)
        if self.action == "cancel":
            await self.cog.cancel_poll(interaction, self.poll_id)
        else:
            await self.cog.publish_poll(interaction, self.poll_id)


class PollControlView(discord.ui.View):
    def __init__(self, cog: "PollCog", poll, action: str, *, disabled=False):
        super().__init__(timeout=None)
        self.add_item(PollButton(cog, poll, action, disabled=disabled))


class PollCog(commands.Cog, name="Poll"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = getattr(bot, "logger", None)
        self.mod_channels = ModChannelHandler(bot)
        default_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "guilds")
        )
        guild_root = os.getenv("EYEBOT_GUILD_CONFIG_DIR", default_root)
        self.service = PollService(os.path.join(guild_root, ".polls"))
        self._restored = False
        self.portable_polls = {}
        self.portable_destinations = {}

    async def cog_load(self):
        if hasattr(self.bot, "tree") and not self.poll_timer.is_running():
            self.poll_timer.start()

    async def cog_unload(self):
        if self.poll_timer.is_running():
            self.poll_timer.cancel()
        for value in self.portable_polls.values():
            task = value.get("task")
            if task:
                task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if self._restored:
            return
        self._restored = True
        for poll in self.service.list():
            if poll.status == "active":
                if poll.mod_message_id:
                    self.bot.add_view(PollControlView(self, poll, "cancel"), message_id=int(poll.mod_message_id))
            elif poll.status == "ended" and poll.mod_message_id:
                self.bot.add_view(PollControlView(self, poll, "publish"), message_id=int(poll.mod_message_id))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if self.bot.user is None or payload.user_id == self.bot.user.id:
            return
        poll = self.service.find_active_by_message(payload.message_id)
        if poll is None:
            return
        selected_emoji = str(payload.emoji)
        if selected_emoji not in poll.emojis:
            return
        accepted = self.service.record_vote(
            poll.id, payload.user_id, poll.emojis.index(selected_emoji)
        )
        channel = await self._channel(poll.channel_id)
        if channel is None:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
            if accepted:
                await message.edit(embed=poll_embed(self.service.get(poll.id)))
                return
            member = payload.member or self.bot.get_user(payload.user_id)
            if member is None:
                member = await self.bot.fetch_user(payload.user_id)
            await message.remove_reaction(payload.emoji, member)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    @staticmethod
    def poll_permission_problem(channel, guild):
        permissions = channel.permissions_for(guild.me)
        required = (
            ("view_channel", "View Channel"),
            ("send_messages", "Send Messages"),
            ("embed_links", "Embed Links"),
            ("add_reactions", "Add Reactions"),
            ("read_message_history", "Read Message History"),
            ("manage_messages", "Manage Messages"),
        )
        missing = [label for attribute, label in required if not getattr(permissions, attribute, False)]
        if not missing:
            return None
        return "EyeBot is missing required poll permissions in this channel: " + ", ".join(missing) + "."

    @app_commands.command(name="poll", description="Create a timed poll")
    @app_commands.guild_only()
    async def poll_slash(self, interaction: discord.Interaction):
        mod_channel = self.mod_channels.configured_channel(interaction.guild)
        if mod_channel is None:
            return await interaction.response.send_message(
                "❌ A moderator log channel must be configured before creating a poll.", ephemeral=True
            )
        permission_problem = self.poll_permission_problem(interaction.channel, interaction.guild)
        if permission_problem:
            return await interaction.response.send_message(
                f"❌ {permission_problem}", ephemeral=True
            )
        await interaction.response.send_modal(PollDetailsModal(self))

    async def create_discord_poll(self, interaction, draft, emojis):
        mod_channel = self.mod_channels.configured_channel(interaction.guild)
        if mod_channel is None:
            return await interaction.followup.send(
                "❌ The configured moderator log channel is no longer available.", ephemeral=True
            )
        permission_problem = self.poll_permission_problem(interaction.channel, interaction.guild)
        if permission_problem:
            return await interaction.followup.send(f"❌ {permission_problem}", ephemeral=True)
        try:
            poll = self.service.create(
                guild_id=interaction.guild_id, channel_id=interaction.channel_id,
                creator_id=interaction.user.id, title=draft["title"],
                description=draft["description"], options=draft["options"],
                emojis=emojis, duration=draft["duration"],
                mod_channel_id=mod_channel.id,
            )
        except PollError as error:
            return await interaction.followup.send(f"❌ {error}", ephemeral=True)
        try:
            message = await interaction.channel.send(embed=poll_embed(poll))
            poll = self.service.update_delivery(poll.id, message_id=message.id)
            for emoji in poll.emojis:
                await message.add_reaction(emoji)
            mod_message = await self.mod_channels.send(
                interaction.guild,
                content=f"📊 Poll **{poll.title}** started in {interaction.channel.mention} by {interaction.user}.",
                view=PollControlView(self, poll, "cancel"), silent=True,
            )
            poll = self.service.update_delivery(poll.id, mod_message_id=mod_message.id)
            self.bot.add_view(PollControlView(self, poll, "cancel"), message_id=mod_message.id)
        except (discord.Forbidden, discord.HTTPException) as error:
            try:
                self.service.cancel(poll.id)
            except PollError:
                pass
            return await interaction.followup.send(
                "❌ EyeBot could not create the poll or add its selected reactions. Check the selected emoji and channel permissions.",
                ephemeral=True,
            )
        await interaction.followup.send(f"✅ Poll created: {message.jump_url}", ephemeral=True)

    @commands.command(name="poll")
    async def poll_portable(self, ctx, *, specification: str = ""):
        request = getattr(ctx, "request", None)
        if request is None or getattr(request.platform, "value", "discord") == "discord":
            return await ctx.send("Use `/poll` to create a Discord poll.")
        try:
            duration, title, description, options = parse_portable_poll(request.raw_content, request.prefix)
        except PollError as error:
            return await ctx.send(f"❌ {error}")
        key = (request.platform.value, str(request.location.channel_id))
        existing = self.portable_polls.get(key)
        if existing and not existing["task"].done():
            return await ctx.send("❌ A poll is already active in this channel.")
        state = {
            "title": title, "description": description, "options": options,
            "votes": {}, "duration": duration, "task": None,
        }
        self.portable_polls[key] = state
        state["task"] = asyncio.create_task(self._finish_portable_poll(key, duration.total_seconds()))
        await ctx.send(
            f"{title} {description} Vote by submitting the number for the option you wish to select. "
            f"The poll is open for {format_duration(duration)}."
        )
        await ctx.send("Select one of the following options: " + ", ".join(
            f"{index}-{option}" for index, option in enumerate(options, 1)
        ))

    def bind_portable_destination(self, platform, channel_id, sender):
        self.portable_destinations[(str(platform), str(channel_id))] = sender

    def record_portable_vote(self, platform, channel_id, actor_id, content) -> bool:
        key = (str(platform), str(channel_id))
        state = self.portable_polls.get(key)
        selected = str(content or "").strip()
        if state is None or not selected.isdecimal():
            return False
        choice = int(selected)
        if not 1 <= choice <= len(state["options"]):
            return False
        voter = str(actor_id)
        if voter in state["votes"]:
            return True
        state["votes"][voter] = choice
        return True

    async def _finish_portable_poll(self, key, seconds):
        try:
            await asyncio.sleep(seconds)
            state = self.portable_polls.get(key)
            if state is None:
                return
            sender = self.portable_destinations.get(key)
            if sender is not None:
                await sender(format_portable_results(
                    state["title"], state["options"], state["votes"].values()
                ))
        finally:
            self.portable_polls.pop(key, None)

    @tasks.loop(seconds=15)
    async def poll_timer(self):
        for poll in self.service.due():
            try:
                await self.end_poll(poll.id)
            except Exception as error:
                if self.logger:
                    self.logger.error(f"Poll {poll.id} could not be ended: {error}", guild_id=poll.guild_id)

    @poll_timer.before_loop
    async def before_poll_timer(self):
        await self.bot.wait_until_ready()

    async def _channel(self, channel_id):
        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(int(channel_id))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return None
        return channel

    async def _message(self, channel_id, message_id):
        channel = await self._channel(channel_id)
        if channel is None or not message_id:
            return channel, None
        try:
            return channel, await channel.fetch_message(int(message_id))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return channel, None

    async def end_poll(self, poll_id):
        poll = self.service.get(poll_id)
        if poll.status != "active":
            return
        channel, message = await self._message(poll.channel_id, poll.message_id)
        counts = {emoji: 0 for emoji in poll.emojis}
        for option_index in poll.votes.values():
            if 0 <= int(option_index) < len(poll.emojis):
                counts[poll.emojis[int(option_index)]] += 1
        if message is not None:
            try:
                await message.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass
        poll = self.service.end(poll.id, [counts[emoji] for emoji in poll.emojis])
        if channel is not None:
            await channel.send(f"Poll - {poll.title} - has ended.")
        guild = self.bot.get_guild(int(poll.guild_id))
        mod_channel = await self._channel(poll.mod_channel_id) if poll.mod_channel_id else None
        if guild is not None and mod_channel is not None:
            mod_message = await self.mod_channels.send(
                guild, channel=mod_channel,
                content=f"⏱️ Poll **{poll.title}** has ended.",
                view=PollControlView(self, poll, "publish"), silent=True,
            )
            poll = self.service.update_delivery(poll.id, mod_message_id=mod_message.id)
            self.bot.add_view(PollControlView(self, poll, "publish"), message_id=mod_message.id)

    async def cancel_poll(self, interaction, poll_id):
        try:
            poll = self.service.cancel(poll_id)
        except PollError as error:
            return await interaction.followup.send(f"❌ {error}", ephemeral=True)
        channel, message = await self._message(poll.channel_id, poll.message_id)
        if message is not None:
            try:
                await message.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass
        notice = f"Poll - {poll.title} - was canceled."
        if channel is not None:
            await channel.send(notice)
        await interaction.channel.send(notice, allowed_mentions=discord.AllowedMentions.none())
        if interaction.message:
            await interaction.message.edit(view=PollControlView(self, poll, "cancel", disabled=True))
        await interaction.followup.send("✅ Poll canceled.", ephemeral=True)

    async def publish_poll(self, interaction, poll_id):
        try:
            poll = self.service.get(poll_id)
            if poll.status != "ended":
                raise PollError(f"Poll is already {poll.status}.")
            channel = await self._channel(poll.channel_id)
            if channel is None:
                raise PollError("The original poll channel is unavailable.")
            await channel.send(embed=results_embed(poll))
            poll = self.service.publish(poll.id)
        except PollError as error:
            return await interaction.followup.send(f"❌ {error}", ephemeral=True)
        await interaction.channel.send(
            f"Poll - {poll.title} - has been published to {channel.mention}",
            allowed_mentions=discord.AllowedMentions.none(),
        )
        if interaction.message:
            await interaction.message.edit(view=PollControlView(self, poll, "publish", disabled=True))
        await interaction.followup.send("✅ Poll results published.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(PollCog(bot))
