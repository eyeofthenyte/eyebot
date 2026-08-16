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

MAX_DICE_PER_TERM = 100
MIN_DIE_SIDES = 2
MAX_DIE_SIDES = 10_000
MAX_REPEAT = 20
MAX_EXPRESSION_LENGTH = 200
MAX_EXPRESSIONS_PER_COMMAND = 10
MAX_COMPONENTS_PER_EXPRESSION = 20
MAX_MODIFIER_ABS = 1_000_000
MAX_EXPLOSIONS_PER_DIE = 10
MAX_REROLLS_PER_DIE = 10
MAX_WORK_UNITS = 10_000

SAFE_TITLE_LENGTH = 240
SAFE_DESCRIPTION_LENGTH = 4_000
SAFE_FIELD_NAME_LENGTH = 240
SAFE_FIELD_VALUE_LENGTH = 1_000
SAFE_FIELDS_PER_EMBED = 24
SAFE_TOTAL_EMBED_LENGTH = 5_600
MAX_EMBEDS_PER_ROLL = 10
MAX_DISPLAYED_DICE_PER_COMPONENT = 50
MAX_DISPLAYED_REPEATS = 10


def configured_dm_channel_id(guild_config):
    """Return a valid configured GM roll-channel ID, otherwise ``None``."""
    value = guild_config.get("dm_channel") if isinstance(guild_config, dict) else None
    if value in (None, "", "UNSET"):
        return None
    try:
        channel_id = int(value)
    except (TypeError, ValueError):
        return None
    return channel_id if channel_id > 0 else None

# load Roller Config
def load_config(bot=None):
    platform_service = getattr(bot, "platform_config_service", None) if bot else None
    if platform_service is not None:
        data = platform_service.discord_guilds()
        updated = False
        for guild in getattr(bot, "guilds", []):
            if ensure_guild_defaults(
                data,
                str(guild.id),
                guild.name,
                bot.config.get("prefix", "!"),
            ):
                updated = True
        if updated:
            platform_service.save_discord_guilds()
        return data

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
            if ensure_guild_defaults(
                data,
                str(guild.id),
                guild.name,
                getattr(bot, "config", {}).get("prefix", "!"),
            ):
                updated = True
        if updated:
            save_config(data)

    return data

# Save Config Changes
def save_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)

# Check Config file data is present or generate it if not
def ensure_guild_defaults(
    config,
    guild_id,
    guild_name,
    default_prefix="!",
):
    changed = False
    if guild_id not in config:
        config[guild_id] = {}
        changed = True

    gcfg = config[guild_id]
    if "guild_name" not in gcfg or gcfg["guild_name"] != guild_name:
        gcfg["guild_name"] = guild_name
        changed = True
    if "prefix" not in gcfg:
        gcfg["prefix"] = default_prefix
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
    if "mod_channel" not in gcfg:
        gcfg["mod_channel"] = "UNSET"
        changed = True
    if "timers" not in gcfg:
        gcfg["timers"] = {}
        changed = True
    return changed


class Roll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.platform_config_service = getattr(
            bot, "platform_config_service", None
        )
        self.config = load_config(bot)
        self.bot.loop.create_task(self.ensure_all_guild_defaults())

    def save_config(self):
        if self.platform_config_service is not None:
            self.platform_config_service.save_discord_guilds()
        else:
            save_config(self.config)

    async def ensure_all_guild_defaults(self):
        await self.bot.wait_until_ready()
        updated = False
        for guild in self.bot.guilds:
            if ensure_guild_defaults(
                self.config,
                str(guild.id),
                guild.name,
                self.bot.config.get("prefix", "!"),
            ):
                updated = True
        if updated:
            self.save_config()

    def parse_dice_expression(self, expression):
        if not expression or len(expression) > MAX_EXPRESSION_LENGTH:
            raise ValueError(
                f"Dice expressions must be 1-{MAX_EXPRESSION_LENGTH} characters."
            )

        expr = expression.replace(' ', '')
        dice_match = re.match(r'^(\d*)d(\d+)', expr)
        if not dice_match:
            raise ValueError(f"Invalid dice expression: {expression}")

        num = int(dice_match.group(1)) if dice_match.group(1) else 1
        sides = int(dice_match.group(2))
        if not 1 <= num <= MAX_DICE_PER_TERM:
            raise ValueError(
                f"Dice count must be between 1 and {MAX_DICE_PER_TERM}."
            )
        if not MIN_DIE_SIDES <= sides <= MAX_DIE_SIDES:
            raise ValueError(
                f"Die sides must be between {MIN_DIE_SIDES} and "
                f"{MAX_DIE_SIDES:,}."
            )

        mods_str = expr[dice_match.end():]

        keep_highest = drop_lowest = reroll = None
        explode = advantage = disadvantage = False
        repeat = 1

        if match := re.search(r'i(\d+)$', mods_str):
            repeat = int(match.group(1))
            mods_str = mods_str[:match.start()]
            if not 1 <= repeat <= MAX_REPEAT:
                raise ValueError(
                    f"Repeat count must be between 1 and {MAX_REPEAT}."
                )

        if match := re.search(r'k(\d+)', mods_str):
            keep_highest = int(match.group(1))
            mods_str = mods_str.replace(match.group(0), '')

        if match := re.search(r'l(\d+)', mods_str):
            drop_lowest = int(match.group(1))
            mods_str = mods_str.replace(match.group(0), '')

        if keep_highest is not None and drop_lowest is not None:
            raise ValueError("Keep (kN) and drop (lN) cannot be combined.")
        if keep_highest is not None and not 1 <= keep_highest <= num:
            raise ValueError(f"Cannot keep {keep_highest} of {num} dice.")
        if drop_lowest is not None and not 0 <= drop_lowest < num:
            raise ValueError(f"Cannot drop {drop_lowest} of {num} dice.")

        if match := re.search(r'r([=<>]?)(\d+)', mods_str):
            comparator = match.group(1) or '='
            target = int(match.group(2))
            if comparator == '=' and not 1 <= target <= sides:
                raise ValueError(
                    f"Reroll target {target} is impossible on a d{sides}."
                )
            if comparator == '<' and not 2 <= target <= sides:
                raise ValueError(
                    f"r<{target} must leave at least one possible d{sides} result."
                )
            if comparator == '>' and not 1 <= target < sides:
                raise ValueError(
                    f"r>{target} must leave at least one possible d{sides} result."
                )
            reroll = (comparator, target)
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

    def estimate_work_units(self, parsed):
        advantage_factor = 2 if parsed['advantage'] or parsed['disadvantage'] else 1
        explosion_factor = (
            MAX_EXPLOSIONS_PER_DIE + 1 if parsed['explode'] else 1
        )
        reroll_factor = MAX_REROLLS_PER_DIE + 1 if parsed['reroll'] else 1
        return (
            parsed['num']
            * parsed['repeat']
            * advantage_factor
            * explosion_factor
            * reroll_factor
        )

    def validate_full_expression(self, full_expr):
        if not full_expr or len(full_expr) > MAX_EXPRESSION_LENGTH:
            raise ValueError(
                f"Expressions must be 1-{MAX_EXPRESSION_LENGTH} characters."
            )

        tokens = self.tokenize_expression(full_expr)
        if not tokens:
            raise ValueError("The expression is empty.")
        normalized = full_expr.replace(' ', '')
        reconstructed = "".join(
            (
                operator
                if index > 0 or operator == '-' or normalized.startswith('+')
                else ""
            )
            + part
            for index, (operator, part) in enumerate(tokens)
        )
        if reconstructed != normalized:
            raise ValueError("The expression contains an invalid operator sequence.")
        if len(tokens) > MAX_COMPONENTS_PER_EXPRESSION:
            raise ValueError(
                f"Expressions may contain at most "
                f"{MAX_COMPONENTS_PER_EXPRESSION} components."
            )

        work_units = 0
        for _, part in tokens:
            if re.fullmatch(r'\d+', part):
                modifier = int(part)
                if modifier > MAX_MODIFIER_ABS:
                    raise ValueError(
                        f"Flat modifiers cannot exceed {MAX_MODIFIER_ABS:,}."
                    )
                continue
            parsed = self.parse_dice_expression(part)
            work_units += self.estimate_work_units(parsed)
            if work_units > MAX_WORK_UNITS:
                raise ValueError(
                    f"Expression workload exceeds the {MAX_WORK_UNITS:,}-unit limit."
                )
        return work_units


    # Rolls a die with optional reroll and explode logic.
    def roll_die(
        self,
        sides,
        reroll=None,
        explode=False,
        max_explode=MAX_EXPLOSIONS_PER_DIE,
    ):
        def should_reroll(value):
            if not reroll: return False
            comp, val = reroll
            return (comp == '=' and value == val or
                    comp == '<' and value < val or
                    comp == '>' and value > val)

        def roll_once():
            roll = random.randint(1, sides)
            for _ in range(MAX_REROLLS_PER_DIE):
                if not should_reroll(roll): break
                roll = random.randint(1, sides)
            return roll

        rolls = [roll_once()]
        while explode and rolls[-1] == sides and len(rolls) <= max_explode:
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
        self.validate_full_expression(full_expr)
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
            self.validate_full_expression(expression)
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

        self.save_config()
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
            self.save_config()
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

    #----------------------------
    # Die Roller Command
    #----------------------------
    async def _delete_roll_command(self, ctx):
        """Delete the invoking message without failing the roll."""
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

    async def _send_private_roll(self, ctx, embed):
        """Send a -dm roll to the configured GM channel."""
        if ctx.guild is None:
            try:
                await ctx.author.send(embed=embed)
                return True
            except discord.Forbidden:
                return False

        guild_config = self.config.get(str(ctx.guild.id), {})
        channel_id = configured_dm_channel_id(guild_config)
        destination = self.bot.get_channel(channel_id) if channel_id else None
        if destination is None:
            return False
        await destination.send(embed=embed)
        return True

    async def _send_blind_roll(self, ctx, embed):
        """Send a -blind roll to the configured DM destination only."""
        if ctx.guild is None:
            return False

        guild_config = self.config.get(str(ctx.guild.id), {})
        channel_id = configured_dm_channel_id(guild_config)
        destination = self.bot.get_channel(channel_id) if channel_id else None
        if destination is None:
            return False
        await destination.send(embed=embed)
        return True

    @staticmethod
    def _truncate_text(value, limit):
        if len(value) <= limit:
            return value
        suffix = "\n… output truncated"
        return value[:limit - len(suffix)].rstrip() + suffix

    @staticmethod
    def _format_roll_values(rolls, highlight=None):
        omitted = max(0, len(rolls) - MAX_DISPLAYED_DICE_PER_COMPONENT)
        if omitted:
            half = MAX_DISPLAYED_DICE_PER_COMPONENT // 2
            displayed = rolls[:half] + rolls[-half:]
        else:
            displayed = rolls

        rendered = ", ".join(
            f"**__{roll}__**" if highlight is not None and roll == highlight
            else str(roll)
            for roll in displayed
        )
        if omitted:
            rendered += f", … ({omitted} dice omitted)"
        return rendered

    @staticmethod
    def _split_field_value(value):
        chunks = []
        remaining = value
        while len(remaining) > SAFE_FIELD_VALUE_LENGTH:
            split_at = remaining.rfind("\n", 0, SAFE_FIELD_VALUE_LENGTH + 1)
            if split_at <= 0:
                split_at = SAFE_FIELD_VALUE_LENGTH
            chunks.append(remaining[:split_at].rstrip())
            remaining = remaining[split_at:].lstrip("\n")
        if remaining or not chunks:
            chunks.append(remaining)
        return chunks

    def _build_roll_embeds(
        self,
        ctx,
        expression,
        total,
        details,
        color,
        roll_alias=None,
    ):
        user_name = (
            ctx.author.nick
            if getattr(ctx.author, "nick", None)
            else ctx.author.name
        )
        base_title = f"🎲 {user_name} Rolled"
        if roll_alias:
            base_title += f" ({roll_alias})"
        base_title = self._truncate_text(base_title, SAFE_TITLE_LENGTH)
        description = self._truncate_text(
            f"Roll: {expression}", SAFE_DESCRIPTION_LENGTH
        )
        footer = self._truncate_text(
            f"🎯 Final Total: {total}", 2_048
        )

        field_items = []
        for operator, detail_list, part_expression in details:
            lines = []
            subtotal = sum(item['total'] for item in detail_list)
            if re.fullmatch(r'\d+', part_expression):
                lines.append(f"{operator} Modifier: **{abs(subtotal)}**")
            else:
                displayed_details = detail_list[:MAX_DISPLAYED_REPEATS]
                for detail in displayed_details:
                    if detail.get('advantage') or detail.get('disadvantage'):
                        chooser = max if detail['tag'] == 'ADV' else min
                        first = self._format_roll_values(
                            detail['rolls_1'], chooser(detail['rolls_1'])
                        )
                        second = self._format_roll_values(
                            detail['rolls_2'], chooser(detail['rolls_2'])
                        )
                        lines.append(
                            f"{detail['tag']} Roll:\n"
                            f"• First: {first}\n"
                            f"• Second: {second}\n"
                            f"→ Chosen total: **{detail['total']}**"
                        )
                    else:
                        rolls = self._format_roll_values(detail['rolls'])
                        lines.append(f"Roll: [{rolls}] → **{detail['total']}**")

                omitted_repeats = len(detail_list) - len(displayed_details)
                if omitted_repeats:
                    lines.append(f"… {omitted_repeats} repeated rolls omitted")
                if len(details) > 1:
                    lines.append(f"**Subtotal: {subtotal}**")

            field_name = self._truncate_text(
                f"{operator} {part_expression}", SAFE_FIELD_NAME_LENGTH
            )
            for index, chunk in enumerate(
                self._split_field_value("\n".join(lines))
            ):
                chunk_name = field_name
                if index:
                    chunk_name = self._truncate_text(
                        f"{field_name} (continued {index + 1})",
                        SAFE_FIELD_NAME_LENGTH,
                    )
                field_items.append((chunk_name, chunk or "No roll details."))

        pages = []
        current_page = []
        # Reserve space for the largest practical " — page/total" title suffix.
        fixed_size = len(base_title) + 20 + len(description) + len(footer)
        current_size = fixed_size

        for name, value in field_items:
            field_size = len(name) + len(value)
            if current_page and (
                len(current_page) >= SAFE_FIELDS_PER_EMBED
                or current_size + field_size > SAFE_TOTAL_EMBED_LENGTH
            ):
                pages.append(current_page)
                current_page = []
                current_size = fixed_size
            current_page.append((name, value))
            current_size += field_size
        if current_page or not pages:
            pages.append(current_page)

        if len(pages) > MAX_EMBEDS_PER_ROLL:
            omitted_pages = len(pages) - MAX_EMBEDS_PER_ROLL
            pages = pages[:MAX_EMBEDS_PER_ROLL]
            notice = (
                "Additional detail pages were omitted to keep the response "
                f"within safety limits. Omitted pages: {omitted_pages}."
            )
            last_page = pages[-1]
            while last_page and (
                len(last_page) >= SAFE_FIELDS_PER_EMBED
                or fixed_size
                + sum(len(name) + len(value) for name, value in last_page)
                + len("Output truncated")
                + len(notice)
                > SAFE_TOTAL_EMBED_LENGTH
            ):
                last_page.pop()
            last_page.append(("Output truncated", notice))

        page_count = len(pages)
        embeds = []
        for page_number, fields in enumerate(pages, start=1):
            title = base_title
            if page_count > 1:
                title = self._truncate_text(
                    f"{base_title} — {page_number}/{page_count}",
                    SAFE_TITLE_LENGTH,
                )
            embed = discord.Embed(
                title=title,
                description=description,
                color=color,
            )
            for name, value in fields:
                embed.add_field(name=name, value=value, inline=False)
            embed.set_footer(text=footer)
            embeds.append(embed)
        return embeds

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
        • `-blind` → sends the result only to the configured DM destination

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
            args = args[:-3].strip()

        message_deleted = False

        expressions = [
            expression.strip()
            for expression in re.split(r'[\n,]+', args.strip())
            if expression.strip()
        ]
        if len(expressions) > MAX_EXPRESSIONS_PER_COMMAND:
            return await ctx.send(
                f"❌ A command may contain at most "
                f"{MAX_EXPRESSIONS_PER_COMMAND} expressions."
            )

        if (is_dm or is_blind) and ctx.guild is not None:
            guild_config = self.config.get(str(ctx.guild.id), {})
            channel_id = configured_dm_channel_id(guild_config)
            if channel_id is None or self.bot.get_channel(channel_id) is None:
                await self._delete_roll_command(ctx)
                return await ctx.send(
                    "⚠️ No GM roll channel is configured for this server. "
                    "Please contact a moderator or administrator to set up the GM channels."
                )

        command_work_units = 0
        for expr in expressions:
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
                work_units = self.validate_full_expression(expr)
                if command_work_units + work_units > MAX_WORK_UNITS:
                    raise ValueError(
                        f"Command workload exceeds the "
                        f"{MAX_WORK_UNITS:,}-unit limit."
                    )
                total, details = self.roll_full_expression(expr)
                command_work_units += work_units
            except ValueError as e:
                await ctx.send(f"Error in {expr}: {e}")
                continue

            if guild_id is None and save_alias:
                await ctx.send("❌ Saving aliases is only supported in servers.")
                continue

            # Save alias if requested
            if save_alias and alias:
                try:
                    self.validate_full_expression(expr)
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
                self.save_config()

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

            embeds = self._build_roll_embeds(
                ctx,
                expr,
                total,
                details,
                embed_color,
                rollalias,
            )

            if not message_deleted:
                await self._delete_roll_command(ctx)
                message_deleted = True

            if is_blind:
                delivered = True
                for embed in embeds:
                    delivered = (
                        await self._send_blind_roll(ctx, embed)
                        and delivered
                    )
                if not delivered:
                    await ctx.send(
                        "⚠️ The blind roll could not be delivered to the configured GM channel. "
                        "Please contact a moderator or administrator."
                    )
            elif is_dm:
                delivered = True
                for embed in embeds:
                    delivered = (
                        await self._send_private_roll(ctx, embed)
                        and delivered
                    )
                if not delivered:
                    await ctx.send(
                        "⚠️ The private roll could not be delivered to the configured GM channel. "
                        "Please contact a moderator or administrator."
                    )
            else:
                for embed in embeds:
                    await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Roll(bot))
