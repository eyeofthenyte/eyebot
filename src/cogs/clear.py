import discord
import os
import json
import asyncio
from datetime import datetime, timedelta
from discord.ext import commands, tasks

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "clear/config.json")

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()
        self._last_runs = {}
        self.timer_loop.start()

    def cog_unload(self):
        self.timer_loop.cancel()

    # ---------------------------------------
    # Config Handling
    # ---------------------------------------
    def load_config(self):
        default = {
            "mod_channels": {},
            "mod_channel_name": "UNSET",
            "timers": {}
        }

        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

        if not os.path.exists(CONFIG_PATH) or os.path.getsize(CONFIG_PATH) == 0:
            with open(CONFIG_PATH, "w") as f:
                json.dump(default, f, indent=4)
            return default

        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            with open(CONFIG_PATH, "w") as f:
                json.dump(default, f, indent=4)
            return default

    def save_config(self):
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=4)

    # ---------------------------------------
    # Mod Channel Setup
    # ---------------------------------------
    async def ensure_mod_channel(self, ctx):
        guild_id = str(ctx.guild.id)
        current = self.config["mod_channels"].get(guild_id)

        if current and current != "UNSET":
            return ctx.guild.get_channel(current)

        if current == "DISABLED":
            return None

        mod_channel_name = self.config.get("mod_channel_name", "mod-logs")

        existing = discord.utils.get(ctx.guild.text_channels, name=mod_channel_name)
        if existing:
            msg = await ctx.send(
                f":clipboard: A `{mod_channel_name}` channel exists. Use it for logging?\nReact with :white_check_mark: to confirm, :x: to skip."
            )
            await msg.add_reaction(":white_check_mark:")
            await msg.add_reaction(":x:")

            def check(r, u):
                return u == ctx.author and r.message.id == msg.id and str(r.emoji) in [":white_check_mark:", ":x:"]

            try:
                r, _ = await self.bot.wait_for("reaction_add", timeout=120.0, check=check)
                await msg.delete()
            except asyncio.TimeoutError:
                await msg.delete()
                return None

            if str(r.emoji) == ":white_check_mark:":
                self.config["mod_channels"][guild_id] = existing.id
                self.save_config()
                await existing.send(f":white_check_mark: Logging enabled by {ctx.author.mention}")
                return existing
            else:
                self.config["mod_channels"][guild_id] = "DISABLED"
                self.save_config()
                return None

        return await self.prompt_mod_channel_selection(ctx)

    async def prompt_mod_channel_selection(self, ctx):
        guild = ctx.guild
        guild_id = str(guild.id)

        prompt = await ctx.send(
            ":wrench: No mod-log channel set. Choose:\n"
            ":one: Select an existing channel\n"
            ":two: Create `mod-logs`\n"
            ":mute: Disable logging\n"
            ":x: Cancel"
        )
        for emoji in [":one:", ":two:", ":mute:", ":x:"]:
            await prompt.add_reaction(emoji)

        def check(r, u):
            return r.message.id == prompt.id and u == ctx.author and str(r.emoji) in ["1️⃣", "2️⃣", "🔇", "❌"]

        try:
            r, _ = await self.bot.wait_for("reaction_add", timeout=120.0, check=check)
            await prompt.delete()
        except asyncio.TimeoutError:
            await prompt.delete()
            return None

        if str(r.emoji) == ":one:":
            channels = [ch for ch in guild.text_channels]
            msg_list = ":clipboard: Reply with the number of the channel:\n"
            for idx, ch in enumerate(channels, 1):
                msg_list += f"{idx}. {ch.mention}\n"

            msg = await ctx.send(msg_list)

            def msg_check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

            try:
                reply = await self.bot.wait_for("message", timeout=120.0, check=msg_check)
                index = int(reply.content)
                await msg.delete()
                await reply.delete()
                if 1 <= index <= len(channels):
                    selected = channels[index - 1]
                    self.config["mod_channels"][guild_id] = selected.id
                    self.save_config()
                    await selected.send(f":white_check_mark: Mod channel set by {ctx.author.mention}")
                    return selected
            except asyncio.TimeoutError:
                return None

        elif str(r.emoji) == ":two:":
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            for role in guild.roles:
                if role.permissions.manage_channels:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            try:
                channel = await guild.create_text_channel("mod-logs", overwrites=overwrites)
                self.config["mod_channels"][guild_id] = channel.id
                self.save_config()
                await channel.send(f":white_check_mark: Mod channel created by {ctx.author.mention}")
                return channel
            except discord.Forbidden:
                await ctx.send(":x: I don't have permission to create a channel.")
                return None

        elif str(r.emoji) == ":mute:":
            self.config["mod_channels"][guild_id] = "DISABLED"
            self.save_config()
            await ctx.send(":mute: Logging disabled.")
            return None

        return None

    # ---------------------------------------
    # Commands
    # ---------------------------------------
    @commands.command(name="clear", aliases=["purge"], as=[":wastebasket:  **__Clear__**", "**Usage: `!clear # `\nWhere `# = number of messages you want to clear`**\nWill delete the number of messeges indicated or 100 if no number is given.\n"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 100):
        mod_channel = await self.ensure_mod_channel(ctx)
        if amount < 1:
            return await ctx.send(":x: Amount must be at least 1.")

        amount = min(amount, 100)
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f":wastebasket: Cleared {len(deleted) - 1} messages.", delete_after=5)

        if mod_channel:
            embed = discord.Embed(
                title=":broom: Clear Log",
                description=f"{ctx.author.mention} cleared {len(deleted)-1} messages in {ctx.channel.mention}",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            await mod_channel.send(embed=embed)

    @commands.command(name="setmodchannel", extras=[":bookmark:  **__Set Mod Channel__**", "**Usage: `!setmodchannel`**\n:one: Will keep current channel.\n:two: Will reset to new channel.\n:three: Will create a new mod channel.\n:mute: Disables mod channel\n:x: Cancels out of menu and applies no changes."])
    @commands.has_permissions(manage_guild=True)
    async def set_mod_channel(self, ctx):
        guild_id = str(ctx.guild.id)
        current_id = self.config["mod_channels"].get(guild_id)
        current_channel = ctx.guild.get_channel(current_id) if isinstance(current_id, int) else None

        if current_channel:
            msg = await ctx.send(
                f":gear: Mod channel is currently set to {current_channel.mention}. Choose:\n"
                ":one: Keep it\n"
                ":two: Reset\n"
                ":three: Create new\n"
                ":mute: Disable\n"
                ":x: Cancel"
            )
            for emoji in [":one:", ":two:", ":three:", ":mute:", ":x:"]:
                await msg.add_reaction(emoji)

            def check(r, u):
                return r.message.id == msg.id and u == ctx.author and str(r.emoji) in [":one:", ":two:", ":three:", ":mute:", ":x:"]

            try:
                r, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                await msg.delete()
            except asyncio.TimeoutError:
                await msg.delete()
                return await ctx.send("⏰ Timed out.")

            if str(r.emoji) == ":one:":
                return await ctx.send(f":white_check_mark: Keeping {current_channel.mention}")
            elif str(r.emoji) == ":two:":
                self.config["mod_channels"][guild_id] = "UNSET"
                self.save_config()
                await ctx.send(":repeat: Resetting...")
                await self.ensure_mod_channel(ctx)
            elif str(r.emoji) == ":three:":
                self.config["mod_channels"][guild_id] = "UNSET"
                self.save_config()
                await self.ensure_mod_channel(ctx)
            elif str(r.emoji) == ":mute:":
                self.config["mod_channels"][guild_id] = "DISABLED"
                self.save_config()
                await ctx.send(":mute: Logging disabled.")
            elif str(r.emoji) == ":x:":
                await ctx.send(":x; Canceled.")
        else:
            await ctx.send(":information: No mod channel set. Starting setup...")
            await self.ensure_mod_channel(ctx)

    @commands.command(name="settimer")
    @commands.has_permissions(manage_channels=True)
    async def settimer(self, ctx, interval: int, duration: int = None):
        mod_channel = await self.ensure_mod_channel(ctx)
        guild_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)

        if interval < 0:
            return await ctx.send(":stopwatch: Interval must be at least 0. Set to 0 to disable.")

        if interval == 0:
            # Disable timer
            self.config["timers"].get(guild_id, {}).pop(channel_id, None)
            self.save_config()
            await ctx.send(f":octagonal_sign: Auto-clear timer disabled in {ctx.channel.mention}")

            if mod_channel:
                embed = discord.Embed(
                    title=":no_bell: Timer Disabled",
                    description=f"{ctx.author.mention} disabled the auto-clear timer in {ctx.channel.mention}",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await mod_channel.send(embed=embed)
            return

        # Otherwise, set timer...
        self.config["timers"].setdefault(guild_id, {})
        expires_at = None
        if duration:
            expires_at = (datetime.utcnow() + timedelta(minutes=duration)).isoformat()

        self.config["timers"][guild_id][channel_id] = {
            "interval_minutes": interval,
            "expires_at": expires_at,
            "start_time": datetime.utcnow().isoformat()
        }

        self.save_config()

        await ctx.send(f":white_check_mark: Auto-clear every {interval} minutes" + (f" for {duration} minutes." if duration else "."))

        # 🔔 Log to mod channel
        if mod_channel:
            embed = discord.Embed(
                title=":stopwatch: Auto-Clear Timer Set",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Channel", value=ctx.channel.mention)
            embed.add_field(name="Interval", value=f"{interval} minute(s)")
            if duration:
                embed.add_field(name="Duration", value=f"{duration} minute(s)")
            embed.set_footer(text=f"Set by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await mod_channel.send(embed=embed)

    # ---------------------------------------
    # Background Timer Task
    # ---------------------------------------
    @tasks.loop(minutes=1)
    async def timer_loop(self):
        now = datetime.utcnow()
        for guild_id, channels in self.config["timers"].items():
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            for channel_id, data in list(channels.items()):
                channel = guild.get_channel(int(channel_id))
                if not channel:
                    continue

                interval = data["interval_minutes"]
                expires = data.get("expires_at")
                start_time_str = data.get("start_time")

                if expires and now >= datetime.fromisoformat(expires):
                    del self.config["timers"][guild_id][channel_id]
                    self.save_config()
                    # ⬇️ Log to mod channel
                    mod_channel_id = self.config["mod_channels"].get(guild_id)
                    if mod_channel_id and mod_channel_id != "UNSET":
                        mod_channel = guild.get_channel(mod_channel_id)
                        if mod_channel:
                            embed = discord.Embed(
                                title="🛑 Timer Expired",
                                description=f"Auto-clear timer expired for {channel.mention}",
                                color=discord.Color.red(),
                                timestamp=discord.utils.utcnow()
                            )
                            await mod_channel.send(embed=embed)
                    continue

                if not start_time_str:
                    continue  # skip if start_time missing

                from datetime import timezone

                start_time = datetime.fromisoformat(start_time_str)
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)

                last_run_key = f"{guild_id}-{channel_id}"
                if not hasattr(self, "_last_runs"):
                    self._last_runs = {}

                last_run = self._last_runs.get(last_run_key)
                if not last_run or (now - last_run).total_seconds() >= interval * 60:
                    self._last_runs[last_run_key] = now

                    def after_check(message):
                        return message.created_at >= start_time

                    await channel.purge(limit=100, check=after_check)

    @timer_loop.before_loop
    async def before_timer_loop(self):
        await self.bot.wait_until_ready()

# Entry point
async def setup(bot):
    await bot.add_cog(Clear(bot))
