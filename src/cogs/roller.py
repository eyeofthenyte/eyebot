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
    # Remove Alias (case sensitive)
    # ---------------------------------------
    @commands.command()
    async def removealias(self, ctx, *, alias: str):
        # Remove a saved alias for this server.

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        alias = alias.strip()
        guild_id = str(ctx.guild.id)

        if guild_id in self.config and alias in self.config[guild_id].get("aliases", {}):
            del self.config[guild_id]["aliases"][alias]
            save_config(self.config)
            await ctx.send(f"✅ Removed alias @{alias}.")
        else:
            await ctx.send(f"❌ Alias @{alias} not found.")

    # ---------------------------------------
    # List Aliases
    # ---------------------------------------
    @commands.command()
    async def listaliases(self, ctx):
        """List all saved aliases for this server."""
        guild_id = str(ctx.guild.id)
        aliases = self.config.get(guild_id, {}).get("aliases", {})

        if not aliases:
            return await ctx.send("📭 No aliases saved for this server.")

        embed = discord.Embed(
            title=f"📘 Saved Aliases for {ctx.guild.name}",
            color=discord.Color.teal()
        )

        for name, data in aliases.items():
            expression = data.get("expression", "❓")
            creator = data.get("creator", "Unknown")
            created = data.get("created", "Unknown")

            embed.add_field(
                name=f"@{name}",
                value=f"**Roll**: {expression}\n👤 **By**: {creator}\n🕓 **On**: {created}",
                inline=False
            )

        await ctx.send(embed=embed)

    # ---------------------------------------
    # DM Channel
    # ---------------------------------------
    @commands.command()
    async def set_dm_channel(self, ctx, create_channel: bool = False):
        """Sets the current channel as the DM channel and selects/creates a DM role."""
        guild = ctx.guild
        guild_id = str(guild.id)

        if guild_id not in self.config:
            self.config[guild_id] = {
                "dm_channel": "UNSET",
                "dm_role": "UNSET",
                "aliases": {}
            }

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        await ctx.send("🧙 Please enter the name of the DM role you'd like to use (or type create to make a new one):")

        try:
            response = await self.bot.wait_for(
                'message',
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                timeout=60
            )
        except asyncio.TimeoutError:
            await ctx.send("⏳ No response received. DM role setup cancelled.")
            return

        role_name = response.content.strip()

        if role_name.lower() == 'create':
            new_role_name = "DM"
            dm_role = await guild.create_role(name=new_role_name, permissions=discord.Permissions(0))
            await ctx.send(f"✅ New DM role {dm_role.name} created.")
        else:
            dm_role = discord.utils.get(guild.roles, name=role_name)
            if not dm_role:
                await ctx.send(f"❌ Role {role_name} not found. Try again with a valid role name or use create to make one.")
                return

        # Save the DM role and channel to config
        self.config[guild_id]["dm_role"] = dm_role.name
        self.config[guild_id]["dm_channel"] = str(ctx.channel.id)
        save_config(self.config)

        await ctx.send(f"✅ DM channel set to <#{ctx.channel.id}> and DM role set to {dm_role.name}.")

        # Optionally create private channel
        if create_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                dm_role: discord.PermissionOverwrite(read_messages=True)
            }

            try:
                new_channel = await guild.create_text_channel("dm-rolls", overwrites=overwrites)
                await ctx.send(f"🆕 Private channel {new_channel.name} created for role {dm_role.name}.")
            except discord.Forbidden:
                await ctx.send("❌ I don't have permission to create channels.")

    #----------------------------
    # User Private Roll Channels
    #----------------------------
    @commands.command()
    async def privaterollchannel(self, ctx, action: str = None, channel: discord.TextChannel = None, target_user: discord.Member = None):
        """Manage private roll channels.

        - `set #channel` — Set your own
        - `set #channel @user` — Mods set for someone else
        - `disable` — Remove your private channel
        - `show` — Show your current private channel
        - `list` — [Mods only] Show all users with private roll channels
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
        """Roll dice with optional -dm tag for private results."""
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

            guild_id = str(ctx.guild.id)
            aliases = self.config.get(guild_id, {}).get("aliases", {})

            # Remove leading '@' if present for alias lookup
            alias_candidate = expr.lstrip('@').strip()

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

            user_nick = ctx.author.nick or ctx.author.name
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
                await ctx.message.add_reaction("📩")
                return
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

        # Default: public
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Roll(bot))
