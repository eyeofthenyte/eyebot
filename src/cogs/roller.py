from services.logService import LogService
from statistics import mean
from datetime import datetime
import discord
from discord import Member
import random
import json
import os
import re
import asyncio
from discord.ext import commands

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "roller/config.json")

# load Roller Config
def load_config(bot=None):
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump({}, f)

    with open(CONFIG_PATH, 'r') as f:
        try:
            data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        except json.JSONDecodeError:
            data = {}

    if bot:
        updated = False
        for guild in getattr(bot, 'guilds', []):
            if ensure_guild_defaults(data, str(guild.id), guild.name):
                updated = True
        if updated:
            save_config(data)

    return data

# Save Config Changes
def save_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)

# Check Config file data is present or generate it if not
def ensure_guild_defaults(config, guild_id, guild_name):
    changed = False
    if guild_id not in config:
        config[guild_id] = {}
        changed = True

    gcfg = config[guild_id]
    if "guild_name" not in gcfg or gcfg["guild_name"] != guild_name:
        gcfg["guild_name"] = guild_name
        changed = True
    if "dm_channel" not in gcfg:
        gcfg["dm_channel"] = "UNSET"
        changed = True
    if "dm_role" not in gcfg:
        gcfg["dm_role"] = "UNSET"
        changed = True
    if "aliases" not in gcfg:
        gcfg["aliases"] = {}
        changed = True
    if "user_channels" not in gcfg:
        gcfg["user_channels"] = {}
        changed = True
    return changed


class Roll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config(bot)
        self.bot.loop.create_task(self.ensure_all_guild_defaults())

    async def ensure_all_guild_defaults(self):
        await self.bot.wait_until_ready()
        updated = False
        for guild in self.bot.guilds:
            if ensure_guild_defaults(self.config, str(guild.id), guild.name):
                updated = True
        if updated:
            save_config(self.config)

    def parse_dice_expression(self, expression):
        expr = expression.replace(' ', '')
        dice_match = re.match(r'^(\d*)d(\d+)', expr)
        if not dice_match:
            raise ValueError(f"Invalid dice expression: {expression}")

        num = int(dice_match.group(1)) if dice_match.group(1) else 1
        sides = int(dice_match.group(2))
        mods_str = expr[dice_match.end():]

        keep_highest = drop_lowest = reroll = None
        explode = advantage = disadvantage = False
        repeat = 1

        if match := re.search(r'i(\d+)$', mods_str):
            repeat = int(match.group(1))
            mods_str = mods_str[:match.start()]

        if match := re.search(r'k(\d+)', mods_str):
            keep_highest = int(match.group(1))
            mods_str = mods_str.replace(match.group(0), '')

        if match := re.search(r'l(\d+)', mods_str):
            drop_lowest = int(match.group(1))
            mods_str = mods_str.replace(match.group(0), '')

        if match := re.search(r'r([=<>]?)(\d+)', mods_str):
            comparator = match.group(1) or '='
            reroll = (comparator, int(match.group(2)))
            mods_str = mods_str.replace(match.group(0), '')

        if 'ex' in mods_str:
            explode = True
            mods_str = mods_str.replace('ex', '')

        if 'adv' in mods_str:
            advantage = True
            mods_str = mods_str.replace('adv', '')
        elif 'dis' in mods_str:
            disadvantage = True
            mods_str = mods_str.replace('dis', '')

        if mods_str.strip():
            raise ValueError(f"Unknown modifiers in {mods_str}")

        return {
            'num': num, 'sides': sides, 'keep_highest': keep_highest,
            'drop_lowest': drop_lowest, 'reroll': reroll, 'explode': explode,
            'advantage': advantage, 'disadvantage': disadvantage, 'repeat': repeat
        }


    # Rolls a die with optional reroll and explode logic.
    def roll_die(self, sides, reroll=None, explode=False, max_explode=10):
        def should_reroll(value):
            if not reroll: return False
            comp, val = reroll
            return (comp == '=' and value == val or
                    comp == '<' and value < val or
                    comp == '>' and value > val)

        def roll_once():
            roll = random.randint(1, sides)
            for _ in range(10):
                if not should_reroll(roll): break
                roll = random.randint(1, sides)
            return roll

        rolls = [roll_once()]
        while explode and rolls[-1] == sides and len(rolls) < max_explode:
            rolls.append(roll_once())
        return rolls

    def apply_keep_drop(self, rolls, keep_highest=None, drop_lowest=None):
        if keep_highest is not None:
            return sorted(rolls)[-keep_highest:]
        if drop_lowest is not None:
            return sorted(rolls)[drop_lowest:]
        return rolls

    def tokenize_expression(self, expr):
        expr = expr.replace(' ', '')
        tokens = re.findall(r'[+-]?[^+-]+', expr)
        result = []
        for token in tokens:
            op = '+' if not token.startswith('-') else '-'
            part = token[1:] if token[0] in '+-' else token
            result.append((op, part))
        return result

    # Handles multiple rolls, applying modifiers.
    def roll_single_part(self, parsed):
        results = []
        details = []

        for _ in range(parsed['repeat']):
            individual_rolls = [self.roll_die(parsed['sides'], parsed['reroll'], parsed['explode']) for _ in range(parsed['num'])]
            sums = [sum(r) for r in individual_rolls]
            final_rolls = self.apply_keep_drop(sums, parsed['keep_highest'], parsed['drop_lowest'])

            if parsed['advantage'] or parsed['disadvantage']:
                rolls_2 = [self.roll_die(parsed['sides'], parsed['reroll'], parsed['explode']) for _ in range(parsed['num'])]
                sums2 = [sum(r) for r in rolls_2]
                final_2 = self.apply_keep_drop(sums2, parsed['keep_highest'], parsed['drop_lowest'])
                total_1, total_2 = sum(final_rolls), sum(final_2)

                if parsed['advantage']:
                    chosen = max(total_1, total_2)
                    tag = 'ADV'
                else:
                    chosen = min(total_1, total_2)
                    tag = 'DIS'

                details.append({
                    'advantage': parsed['advantage'],
                    'disadvantage': parsed['disadvantage'],
                    'rolls_1': final_rolls,
                    'rolls_2': final_2,
                    'total': chosen,
                    'tag': tag
                })
                results.append(chosen)
            else:
                total = sum(final_rolls)
                details.append({'rolls': final_rolls, 'total': total})
                results.append(total)

        return results, details

    # Parses additive/subtractive parts (2d6+4-1d8), sums totals, returns roll breakdown.
    def roll_full_expression(self, full_expr):
        total = 0
        all_details = []
        for op, part in self.tokenize_expression(full_expr):
            if re.fullmatch(r'\d+', part):
                number = int(part)
                value = number if op == '+' else -number
                all_details.append((op, [{'rolls': [value], 'total': value}], part))
                total += value
            else:
                parsed = self.parse_dice_expression(part)
                subtotals, details = self.roll_single_part(parsed)
                subtotal_sum = sum(subtotals)
                total += subtotal_sum if op == '+' else -subtotal_sum
                all_details.append((op, details, part))
        return total, all_details


    # ---------------------------------------
    # Alias Command
    # ---------------------------------------
    @commands.group(invoke_without_command=True)
    async def alias(self, ctx):
        """
        Manage custom roll aliases that let you save and reuse dice expressions.

        Subcommands:
        • `add <name> <expression>` – Save a new alias
        • `remove <name>` – Delete an alias (creator or mod only)
        • `list [@user]` – View saved aliases, optionally for a specific user

        Alias names can include spaces or hyphens (up to 32 characters).
        Expressions must be valid dice syntax (e.g. 2d6+4, 1d20adv, etc.).

        Examples:
        `!alias add fireball big hit 8d6`
        `!alias remove fireball big hit`
        `!alias list`
        `!alias list @MyUsername`
        """
        await ctx.send("Usage: `!alias add <name> <roll>`, `!alias remove <name>`, or `!alias list [@user]`")

    # ---------------------------------------
    # Add Alias
    # ---------------------------------------
    @alias.command(name="add")
    async def alias_add(self, ctx, *, input_text: str):
        """
        Add a roll alias. Supports alias names with spaces and asks for confirmation before overwriting.

        Usage:
        `!alias add Name With Spaces <expression>`
        """
        guild_id = str(ctx.guild.id)

        try:
            alias_part, expression = re.split(r'\s+(?=\d+d\d+|\d+\b)', input_text.strip(), maxsplit=1)
        except ValueError:
            return await ctx.send("❌ Usage: `!alias add <alias name> <expression>`")

        alias = alias_part.strip()

        if not re.fullmatch(r'[\w\s\-]{1,32}', alias):
            return await ctx.send("❌ Invalid alias name. Must be 1–32 characters with letters, numbers, spaces, or hyphens.")

        try:
            _ = self.roll_full_expression(expression)  # Validate expression
        except ValueError as e:
            return await ctx.send(f"❌ Invalid expression: {e}")

        self.config.setdefault(guild_id, {}).setdefault("aliases", {})
        existing = self.config[guild_id]["aliases"].get(alias)

        if existing:
            embed = discord.Embed(
                title="⚠️ Confirm Overwrite",
                description=(
                    f"The alias `@{alias}` already exists:\n"
                    f"> `{existing['expression']}` by {existing.get('creator', 'Unknown')}\n\n"
                    f"Do you want to overwrite it with:\n"
                    f"> `{expression}`?"
                ),
                color=discord.Color.orange()
            )
            embed.set_footer(text="React with ✅ to confirm, ❌ to cancel.")

            msg = await ctx.send(embed=embed)
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")

            def check(reaction, user):
                return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in ["✅", "❌"]

            try:
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await msg.edit(content="⏳ Timed out. Alias was not changed.", embed=None)
                return

            if str(reaction.emoji) == "❌":
                await msg.edit(content="❌ Alias update cancelled.", embed=None)
                return

            await msg.delete()

        self.config[guild_id]["aliases"][alias] = {
            "expression": expression,
            "creator": str(ctx.author),
            "created": datetime.utcnow().isoformat()
        }

        save_config(self.config)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        await ctx.send(f"✅ Alias `@{alias}` {'updated' if existing else 'added'}.")

    # ---------------------------------------
    # Remove Alias (with confirmation)
    # ---------------------------------------
    @alias.command(name="remove")
    async def alias_remove(self, ctx, *, alias: str):
        """
        Removes an alias if the user is the creator or has Manage Guild permission.

        Usage:
        `!alias remove <alias name>`
        """

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        guild_id = str(ctx.guild.id)
        alias = alias.strip()
        aliases = self.config.get(guild_id, {}).get("aliases", {})

        if alias not in aliases:
            return await ctx.send(f"❌ Alias `@{alias}` not found.")

        alias_data = aliases[alias]
        creator_str = alias_data.get("creator")

        is_creator = creator_str == str(ctx.author)
        is_mod = ctx.author.guild_permissions.manage_guild

        if not (is_creator or is_mod):
            return await ctx.send("❌ You don't have permission to remove this alias. Only the creator or a server mod can do that.")

        # Send confirmation embed
        embed = discord.Embed(
            title="🗑️ Confirm Alias Deletion",
            description=f"Are you sure you want to delete the alias `@{alias}`?\nCreated by: `{creator_str}`",
            color=discord.Color.red()
        )
        embed.set_footer(text="React with ✅ to confirm, ❌ to cancel.")

        confirm_msg = await ctx.send(embed=embed)
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")

        def check(reaction, user):
            return (
                user == ctx.author and
                str(reaction.emoji) in ["✅", "❌"] and
                reaction.message.id == confirm_msg.id
            )

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=20.0, check=check)
        except asyncio.TimeoutError:
            await confirm_msg.edit(content="⏳ Timed out. Alias not removed.", embed=None)
            return

        if str(reaction.emoji) == "✅":
            del aliases[alias]
            save_config(self.config)
            await confirm_msg.edit(content=f"✅ Alias `@{alias}` has been removed.", embed=None)
        else:
            await confirm_msg.edit(content="❌ Alias removal cancelled.", embed=None)

        try:
            await confirm_msg.clear_reactions()
        except discord.Forbidden:
            pass

    # ---------------------------------------
    # List Aliases
    # ---------------------------------------
    @alias.command(name="list")
    async def alias_list(self, ctx, member: discord.Member = None):
        """
        Lists all aliases on the server or by alias creator.

        Usage:
        `!alias list`
        `!alias list @MyUsername`
        """

        guild_id = str(ctx.guild.id)
        aliases = self.config.get(guild_id, {}).get("aliases", {})

        if not aliases:
            return await ctx.send("📭 No aliases saved for this server.")

        filtered = {}
        if member:
            for name, data in aliases.items():
                if data.get("creator") == str(member):
                    filtered[name] = data
        else:
            filtered = aliases

        if not filtered:
            return await ctx.send(f"📭 No aliases found for {member.display_name}." if member else "📭 No aliases found.")

        title = f"📘 Saved Aliases"
        if member:
            title += f" by {member.display_name}"

        embed = discord.Embed(title=title, color=discord.Color.teal())

        for name, data in filtered.items():
            expression = data.get("expression", "❓")
            creator = data.get("creator", "Unknown")
            created = data.get("created", "Unknown")

            embed.add_field(
                name=f"@{name}",
                value=f"**Roll**: `{expression}`\n👤 **By**: {creator}\n🕓 **On**: {created}",
                inline=False
            )

        await ctx.send(embed=embed)

    # ---------------------------------------
    # DM Channel
    # ---------------------------------------
    @commands.command(name="set_dm")
    async def set_dm(self, ctx):
        """
        Interactive setup for the DM system.

        Allows an admin or DM to configure:
        • 📑 The DM-only channel (existing, new, or reset)
        • 👤 The DM role (existing, new, or reset)

        This setup uses embeds and emoji reactions to guide configuration.
        Only one DM role and channel can be active per server.

        Permissions:
        • Must be a server Admin or have the current DM role

        Usage:
        `!set_dm`
        """

        guild = ctx.guild
        guild_id = str(guild.id)

        if guild_id not in self.config:
            self.config[guild_id] = {
                "dm_channel": "UNSET",
                "dm_role": "UNSET",
                "aliases": {}
            }

        # Permission check
        dm_role_name = self.config[guild_id].get("dm_role", "UNSET")
        dm_channel_id = self.config[guild_id].get("dm_channel", "UNSET")

        dm_role_obj = discord.utils.get(guild.roles, name=dm_role_name) if dm_role_name != "UNSET" else None
        dm_channel_obj = guild.get_channel(int(dm_channel_id)) if dm_channel_id != "UNSET" else None

        is_admin = ctx.author.guild_permissions.administrator
        has_dm_role = dm_role_obj in ctx.author.roles if dm_role_obj else False

        if not (is_admin or has_dm_role):
            return await ctx.send("❌ You must be a server admin or have the DM role to use this command.")

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        # Display current DM channel and role
        current_channel_display = dm_channel_obj.mention if dm_channel_obj else "Unset"
        current_role_display = dm_role_obj.mention if dm_role_obj else "Unset"

        main_embed = discord.Embed(
            title="DM Setup",
            description=(
                f"**Current Settings:**\n"
                f"• 📑 DM Channel: {current_channel_display}\n"
                f"• 👤 DM Role: {current_role_display}\n\n"
                f"**React to configure:**\n"
                f"📑 Set **DM Channel**\n"
                f"👤 Set **DM Role**\n"
                f"❌ Cancel setup"
            ),
            color=discord.Color.blurple()
        )

        menu_msg = await ctx.send(embed=main_embed)
        reactions = {"📑": "channel", "👤": "role", "❌": "cancel"}
        for emoji in reactions:
            await menu_msg.add_reaction(emoji)

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == menu_msg.id and str(reaction.emoji) in reactions

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            return await menu_msg.edit(content="⏳ No response received. Setup cancelled.", embed=None, delete_after=10)

        choice = reactions[str(reaction.emoji)]

        if choice == "cancel":
            return await menu_msg.edit(content="❌ Setup cancelled.", embed=None, delete_after=10)

        # -------- DM CHANNEL SETUP --------
        if choice == "channel":
            channel_embed = discord.Embed(
                title="Set DM Channel",
                description="📁 Choose Existing Channel\n"
                            "🆕 Create New Channel\n"
                            "🔄 Reset to UNSET\n"
                            "❌ Cancel",
                color=discord.Color.green()
            )
            await menu_msg.edit(embed=channel_embed)
            channel_opts = {"📁": "existing", "🆕": "create", "🔄": "reset", "❌": "cancel"}
            await menu_msg.clear_reactions()
            for emoji in channel_opts:
                await menu_msg.add_reaction(emoji)

            def chan_check(reaction, user):
                return user == ctx.author and reaction.message.id == menu_msg.id and str(reaction.emoji) in channel_opts

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=chan_check)
            except asyncio.TimeoutError:
                return await menu_msg.edit(content="⏳ No response. DM channel setup cancelled.", embed=None, delete_after=10)

            chan_choice = channel_opts[str(reaction.emoji)]
            if chan_choice == "cancel":
                return await menu_msg.edit(content="❌ Channel setup cancelled.", embed=None, delete_after=10)
            elif chan_choice == "existing":
                await menu_msg.edit(content="💬 Mention the channel to set as DM channel:", embed=None)
                try:
                    msg = await self.bot.wait_for('message', timeout=60.0, check=lambda m: m.author == ctx.author)
                except asyncio.TimeoutError:
                    return await ctx.send("⏳ No channel mentioned. Cancelled.")
                if msg.channel_mentions:
                    self.config[guild_id]["dm_channel"] = str(msg.channel_mentions[0].id)
                    save_config(self.config)
                    return await ctx.send(f"✅ DM channel set to {msg.channel_mentions[0].mention}.", delete_after=10)
                return await ctx.send("❌ No valid channel mentioned.", delete_after=10)
            elif chan_choice == "create":
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False)
                }
                if dm_role:
                    overwrites[dm_role] = discord.PermissionOverwrite(read_messages=True)

                new_chan = await guild.create_text_channel("dm-rolls", overwrites=overwrites)
                self.config[guild_id]["dm_channel"] = str(new_chan.id)
                save_config(self.config)
                return await ctx.send(f"🆕 Created and set DM channel to {new_chan.mention}.", delete_after=10)
            elif chan_choice == "reset":
                self.config[guild_id]["dm_channel"] = "UNSET"
                save_config(self.config)
                return await ctx.send("🔄 DM channel reset to UNSET.", delete_after=10)

        # -------- DM ROLE SETUP --------
        if choice == "role":
            role_embed = discord.Embed(
                title="Set DM Role",
                description="👥 Choose Existing Role\n"
                            "🛠️ Create New Role\n"
                            "🔄 Reset to UNSET\n"
                            "❌ Cancel",
                color=discord.Color.orange()
            )
            await menu_msg.edit(embed=role_embed)
            role_opts = {"👥": "existing", "🛠️": "create", "🔄": "reset", "❌": "cancel"}
            await menu_msg.clear_reactions()
            for emoji in role_opts:
                await menu_msg.add_reaction(emoji)

            def role_check(reaction, user):
                return user == ctx.author and reaction.message.id == menu_msg.id and str(reaction.emoji) in role_opts

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=role_check)
            except asyncio.TimeoutError:
                return await ctx.send("⏳ No response. DM role setup cancelled.", delete_after=10)

            role_choice = role_opts[str(reaction.emoji)]
            if role_choice == "cancel":
                return await ctx.send("❌ Role setup cancelled.")
            elif role_choice == "existing":
                await menu_msg.edit(content="📝 Type the role name:", embed=None)
                try:
                    msg = await self.bot.wait_for('message', timeout=60.0, check=lambda m: m.author == ctx.author)
                except asyncio.TimeoutError:
                    return await ctx.send("⏳ No role name received.")
                role = discord.utils.get(guild.roles, name=msg.content.strip())
                if role:
                    self.config[guild_id]["dm_role"] = role.name
                    save_config(self.config)
                    return await ctx.send(f"✅ DM role set to **{role.name}**.")
                return await ctx.send("❌ Role not found.", delete_after=10)
            elif role_choice == "create":
                new_role = await guild.create_role(name="DM", permissions=discord.Permissions(0))
                self.config[guild_id]["dm_role"] = new_role.name
                save_config(self.config)
                return await ctx.send(f"🆕 Created and set DM role to **{new_role.name}**.", delete_after=10)
            elif role_choice == "reset":
                self.config[guild_id]["dm_role"] = "UNSET"
                save_config(self.config)
                return await ctx.send("🔄 DM role reset to UNSET.", delete_after=10)

    #----------------------------
    # User Private Roll Channels
    #----------------------------
    @commands.command()
    async def privateroll(self, ctx, action: str = None, channel: discord.TextChannel = None, target_user: discord.Member = None):
        """Manage private roll channels.

        - `set #channel` — Set your own
        - `set #channel @user` — Mods set for someone else
        - `disable` — Remove your private channel
        - `show` — Show your current private channel
        - `list` — [Mods only] Show all users with private roll channels

        Usage:
        `!privaterollchannel set #channel [@user]`
        `!privaterollchannel disable`
        `!privaterollchannel show`
        `!privaterollchannel list`
        """
        guild_id = str(ctx.guild.id)
        user_channels = self.config.setdefault(guild_id, {}).setdefault("user_channels", {})

        if action == "list":
            if not (
                ctx.author.guild_permissions.manage_messages
                or ctx.author.guild_permissions.manage_guild
                or ctx.author.guild_permissions.administrator
            ):
                return await ctx.send("❌ You don’t have permission to view private roll channel assignments.")

            if not user_channels:
                return await ctx.send("📭 No private roll channels are set in this server.")

            embed = discord.Embed(
                title="🔒 Private Roll Channels (Mods Only)",
                color=discord.Color.purple()
            )
            for user_id, chan_id in user_channels.items():
                member = ctx.guild.get_member(int(user_id))
                channel = self.bot.get_channel(int(chan_id))
                if member and channel:
                    embed.add_field(name=member.display_name, value=f"{channel.mention}", inline=False)
            return await ctx.send(embed=embed)

        elif action == "set":
            if not channel:
                return await ctx.send("❌ Provide a channel. E.g., `!privaterollchannel set #channel`.")

            is_self = target_user is None
            target = ctx.author if is_self else target_user

            if not is_self and not (
                ctx.author.guild_permissions.manage_messages
                or ctx.author.guild_permissions.manage_guild
                or ctx.author.guild_permissions.administrator
            ):
                return await ctx.send("❌ You don’t have permission to set channels for others.")

            if not channel.permissions_for(target).send_messages:
                return await ctx.send(f"❌ {target.display_name} cannot send messages in {channel.mention}.")

            user_channels[str(target.id)] = str(channel.id)
            save_config(self.config)
            who = "Your" if is_self else f"{target.mention}'s"
            return await ctx.send(f"✅ {who} private roll channel is now {channel.mention}.")

        elif action == "disable":
            uid = str(ctx.author.id)
            if uid in user_channels:
                del user_channels[uid]
                save_config(self.config)
                return await ctx.send("✅ Your private roll channel has been disabled.")
            return await ctx.send("⚠️ You don’t have a private roll channel set.")

        elif action == "show":
            uid = str(ctx.author.id)
            chan_id = user_channels.get(uid)
            if chan_id:
                chan = self.bot.get_channel(int(chan_id))
                if chan:
                    return await ctx.send(f"🔒 Your private roll channel is {chan.mention}")
            return await ctx.send("📭 You don’t currently have a private roll channel set.")

        return await ctx.send("Usage:\n"
                              "`!privaterollchannel set #channel [@user]`\n"
                              "`!privaterollchannel disable`\n"
                              "`!privaterollchannel show`\n"
                              "`!privaterollchannel list`")

    #----------------------------
    # Die Roller Command
    #----------------------------
    @commands.command(aliases=["r"])
    async def roll(self, ctx, *, args=None):
        """
        Rolls dice using standard and advanced modifiers.

        Basic usage:
        `!roll 2d6+4`
        `!roll 1d20adv-2`
        `!roll @myattack`  ← Use an alias (case sensitive)

        Supports:
        • Advantage/Disadvantage: `adv`, `dis`
        • Keep/Drop: `k2` (keep highest 2), `l1` (drop lowest 1)
        • Exploding Dice: `ex`
        • Reroll: `r=1`, `r<2`, `r>3`
        • Repeat Rolls: `i2`
        • Flat modifiers: `+2`, `-1`
        • Aliases: Save with `@aliasname *` or call with `@aliasname`

        Special flags:
        • `-dm` → sends result privately
        • `-blind` → suppresses output

        Examples:
        `!roll 2d20+5`
        `!roll 4d6kl3+1i2`
        `!roll smite 2d8+2d6 -dm`
        `!roll @fireball big hit`
        """
        if not args:
            return await ctx.send("Provide a dice expression, e.g. 2d6+4. Support: adv, dis, k, l, ex, r<3, i2")

        is_blind = False
        is_dm = False

        # Parse and remove the tag if present
        lowered_args = args.lower()
        if lowered_args.endswith("-blind"):
            is_blind = True
            args = args[:-6].strip()
        elif lowered_args.endswith("-dm"):
            is_dm = True
            args = args[:-7].strip()

        message_deleted = False

        expressions = re.split(r'[\n,]+', args.strip())

        for expr in expressions:
            expr = expr.strip()
            if not expr:
                continue

            rollalias = None  # Initialize rollalias here
            save_alias = False
            force_overwrite = False

            if expr.endswith('!force'):
                expr = expr[:-6].strip()
                force_overwrite = True

            guild_id = str(ctx.guild.id) if ctx.guild else None
            aliases = self.config.get(guild_id, {}).get("aliases", {}) if guild_id else {}

            # Remove leading '@' if present for alias lookup
            alias_candidate = expr.lstrip('@').strip()

            if guild_id is None:
                aliases = {}  # No alias support in DMs

            # Check if the whole expr is exactly an alias name (no dice expression)
            if alias_candidate in aliases and (expr == alias_candidate or expr == '@' + alias_candidate):
                alias = alias_candidate
                rollalias = alias

                saved = aliases.get(alias)
                if not saved:
                    await ctx.send(f"❌ Alias {alias} not found.")
                    continue
                expr = saved["expression"]

            else:
                # Extract alias at start with dice expression after, for saving new alias
                # Allow optional '@' before alias name
                alias_match = re.match(r'@?(.+?)\s+(?=\d+d\d+|\d+\b)', expr, re.IGNORECASE)
                if alias_match:
                    alias_raw = alias_match.group(1).strip()
                    save_alias = alias_raw.endswith('*')
                    alias = alias_raw.rstrip('*').strip()
                    rollalias = alias
                    expr = expr[alias_match.end():].strip()

                    if alias:
                        if not re.fullmatch(r'[\w\s\-]{1,32}', alias):
                            await ctx.send("❌ Invalid alias name. Alias must be 1–32 characters and only contain letters, numbers, spaces, or hyphens.")
                            continue

            try:
                total, details = self.roll_full_expression(expr)
            except ValueError as e:
                await ctx.send(f"Error in {expr}: {e}")
                continue

            if guild_id is None and save_alias:
                await ctx.send("❌ Saving aliases is only supported in servers.")
                continue

            # Save alias if requested
            if save_alias and alias:
                try:
                    _ = self.roll_full_expression(expr)
                except ValueError as e:
                    await ctx.send(f"❌ Alias {alias} not saved: Invalid expression ({expr}).\nError: {e}")
                    continue

                if guild_id not in self.config:
                    self.config[guild_id] = {"aliases": {}}

                existing = self.config[guild_id]["aliases"].get(alias)
                if existing and not force_overwrite:
                    await ctx.send(f"⚠️ Alias {alias} already exists.\nUse !force at the end of your message to overwrite it.")
                    continue

                self.config[guild_id]["aliases"][alias] = {
                    "expression": expr,
                    "creator": str(ctx.author),
                    "created": datetime.utcnow().isoformat()
                }
                save_config(self.config)

                if existing and force_overwrite:
                    await ctx.send(f"♻️ Alias {alias} was overwritten.")
                else:
                    await ctx.send(f"✅ Alias {alias} saved for this server.")

            # Embed Structure & Formatting
            embed_color = discord.Color.blue()
            if any('d20' in part.lower() for _, _, part in details):
                max_possible, min_possible = 0, 0
                for op, part_details, part_expr in details:
                    try:
                        parsed = self.parse_dice_expression(part_expr)
                        max_val = parsed['num'] * parsed['sides'] * parsed['repeat']
                        min_val = parsed['num'] * 1 * parsed['repeat']
                        if op == '+':
                            max_possible += max_val
                            min_possible += min_val
                        else:
                            max_possible -= min_val
                            min_possible -= max_val
                    except:
                        if re.fullmatch(r'\d+', part_expr):
                            val = int(part_expr)
                            max_possible += val if op == '+' else -val
                            min_possible += val if op == '+' else -val
                if total == max_possible:
                    embed_color = discord.Color.green()
                elif total == min_possible:
                    embed_color = discord.Color.red()

            user_nick = ctx.author.nick if hasattr(ctx.author, 'nick') else ctx.author.name
            title = f"🎲 {user_nick} Rolled"
            if rollalias:
                title += f" ({rollalias})"

            embed = discord.Embed(title=title, description=f"Roll: {expr}", color=embed_color)

            for op, detail_list, part_expr in details:
                subtotal = sum(d['total'] for d in detail_list)
                field_lines = []

                if re.fullmatch(r'\d+', part_expr):
                    field_lines.append(f"{op} Modifier: **{abs(subtotal)}**")
                else:
                    for detail in detail_list:
                        if 'advantage' in detail or 'disadvantage' in detail:
                            h = max if detail['tag'] == 'ADV' else min
                            def fmt(rolls):
                                val = h(rolls)
                                return ', '.join(f"**__{r}__**" if r == val else str(r) for r in rolls)
                            field_lines.append(
                                f"{detail['tag']} Roll:\n• First: {fmt(detail['rolls_1'])}\n• Second: {fmt(detail['rolls_2'])}\n→ Chosen total: **{detail['total']}**"
                            )
                        else:
                            rolls_str = ", ".join(str(r) for r in detail['rolls'])
                            field_lines.append(f"Roll: [{rolls_str}] → **{detail['total']}**")

                value_text = "\n".join(field_lines)
                if len(details) > 1 and not re.fullmatch(r'\d+', part_expr):
                    value_text += f"\n**Subtotal: {subtotal}**"
                embed.add_field(name=f"{op} {part_expr}", value=value_text, inline=False)

            embed.set_footer(text=f"🎯 Final Total: {total}")

            if not message_deleted:
                try:
                    await ctx.message.delete()
                    message_deleted = True
                except (discord.Forbidden, discord.NotFound):
                    pass

            await ctx.send(embed=embed)

            # Handle -dm logic
            if is_dm:
                guild_id = str(ctx.guild.id)
                uid = str(ctx.author.id)
                gcfg = self.config.get(guild_id, {})
                chan_id = gcfg.get("user_channels", {}).get(uid)
                dm_role_name = gcfg.get("dm_role", "UNSET")

                # Use user private channel if available
                if chan_id:
                    dest_chan = self.bot.get_channel(int(chan_id))
                    if dest_chan:
                        await dest_chan.send(embed=embed)
                        await ctx.message.add_reaction("📩")
                        return
                    else:
                        await ctx.send("⚠️ Could not find your configured private roll channel.")

                # Otherwise fallback to DM user + DM role
                recipients = [ctx.author]
                if dm_role_name != "UNSET":
                    role = discord.utils.get(ctx.guild.roles, name=dm_role_name)
                    if role:
                        recipients += role.members

                for user in recipients:
                    try:
                        await user.send(embed=embed)
                    except discord.Forbidden:
                        pass
                try:
                    await ctx.message.add_reaction("📩")
                except (discord.Forbidden, discord.NotFound):
                    pass

            if not message_deleted:
                try:
                    await ctx.message.delete()
                    message_deleted = True
                except (discord.Forbidden, discord.NotFound):
                    pass

            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Roll(bot))
