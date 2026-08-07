"""Discord cog for category-adjusted gem generation."""

from __future__ import annotations

import math
import os
import random
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import discord
from discord.ext import commands


GEM_TIERS = (10, 50, 100, 500, 1000, 5000)
CATEGORY_MULTIPLIERS = {
    "chip": Fraction(1, 10),
    "shard": Fraction(1, 5),
    "uncut": Fraction(1, 1),
    "stone": Fraction(11, 10),
    "gem": Fraction(6, 5),
}
MAX_GEMS = 50
EMBED_DESCRIPTION_LIMIT = 3800
UPGRADE_LABELS = {
    1: "flawless",
    2: "museum",
    3: "legendary",
}
BASE_TIER_FLAWLESS_CHANCE = 0.01
DIAMOND_DUST_CHANCE = 0.25
DIAMOND_DUST_MINIMUM_VALUE = 100
MAX_HIGHER_TIER_ITEM_MULTIPLIER = Fraction(6, 5)


@dataclass(frozen=True)
class CategorizedGem:
    name: str
    description: str
    category: str
    uncut_value: int
    value: int
    tier: int


@dataclass(frozen=True)
class GeneratedGem:
    """A gem as it appears in a particular generated value tier."""

    name: str
    description: str
    label: str
    value: int
    uncut_value: int

    def display(self) -> str:
        return (
            f"- **{self.name} ({self.label}) {self.value}gp**: "
            f"{self.description}"
        )


def gem_tier_for_value(value: int) -> int:
    """Return the standard treasure tier containing an adjusted gem value."""
    eligible_tiers = [tier for tier in GEM_TIERS if tier <= value]
    return max(eligible_tiers, default=GEM_TIERS[0])


def adjusted_gem_value(uncut_value: int, category: str) -> int:
    """Calculate the exact gp value for a gem category."""
    if category not in CATEGORY_MULTIPLIERS:
        raise ValueError(f"Unknown gem category: {category}")
    return int(uncut_value * CATEGORY_MULTIPLIERS[category])


def load_categorized_gems(gem_dir: Path) -> tuple[CategorizedGem, ...]:
    """Load every base gem and expand it into its five value categories."""
    gems: list[CategorizedGem] = []
    for uncut_value in GEM_TIERS:
        table_path = gem_dir / f"{uncut_value}gp.txt"
        if not table_path.is_file():
            raise FileNotFoundError(f"Missing gem table: {table_path.name}")

        for line_number, raw_line in enumerate(
            table_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not raw_line.strip():
                continue
            try:
                raw_name, description = raw_line.split(";", 1)
            except ValueError as error:
                raise ValueError(
                    f"Invalid entry in {table_path.name} line {line_number}"
                ) from error

            name = raw_name.strip().strip("*")
            for category in CATEGORY_MULTIPLIERS:
                value = adjusted_gem_value(uncut_value, category)
                gems.append(
                    CategorizedGem(
                        name=name,
                        description=description.strip(),
                        category=category,
                        uncut_value=uncut_value,
                        value=value,
                        tier=gem_tier_for_value(value),
                    )
                )
    return tuple(gems)


def generated_from_category(gem: CategorizedGem) -> GeneratedGem:
    """Convert a category-expanded source gem into an output result."""
    return GeneratedGem(
        name=gem.name,
        description=gem.description,
        label=gem.category,
        value=gem.value,
        uncut_value=gem.uncut_value,
    )


def higher_tier_item_within_ceiling(
    gem: CategorizedGem | GeneratedGem,
    target_tier: int,
) -> bool:
    """Return whether a generated item fits the target tier's ceiling."""
    label = gem.category if isinstance(gem, CategorizedGem) else gem.label
    if gem.uncut_value == target_tier and label == "flawless":
        return True
    return not (
        gem.uncut_value > target_tier
        and gem.value
        > target_tier * MAX_HIGHER_TIER_ITEM_MULTIPLIER
    )


def gems_for_tier(
    gems: tuple[CategorizedGem, ...], target_tier: int
) -> tuple[GeneratedGem, ...]:
    """Return normal and eligible upgraded gems for a treasure tier."""
    if target_tier not in GEM_TIERS:
        raise ValueError(
            "Gem value must be one of: "
            + ", ".join(str(tier) for tier in GEM_TIERS)
            + " gp."
        )
    generated: list[GeneratedGem] = []

    # Category-adjusted entries appear in the tier containing their actual
    # value. Only chips and shards can move below their original base tier.
    for gem in gems:
        if gem.tier != target_tier:
            continue
        if not higher_tier_item_within_ceiling(gem, target_tier):
            continue
        generated.append(generated_from_category(gem))

    # Add each lower-tier stone once, using the upgrade label instead of its
    # normal category. The generated tier becomes its adjusted gp value.
    target_index = GEM_TIERS.index(target_tier)
    for gem in gems:
        if gem.category != "uncut":
            continue
        tier_difference = target_index - GEM_TIERS.index(gem.uncut_value)
        if tier_difference not in UPGRADE_LABELS:
            continue
        generated.append(
            GeneratedGem(
                name=gem.name,
                description=gem.description,
                label=UPGRADE_LABELS[tier_difference],
                value=target_tier,
                uncut_value=gem.uncut_value,
            )
        )

    return tuple(generated)


def apply_base_tier_flawless_chance(
    gem: GeneratedGem,
    *,
    random_value: float | None = None,
) -> GeneratedGem:
    """Replace a base-tier category with flawless on a one-percent roll."""
    base_categories = {"uncut", "stone", "gem"}
    if gem.label in base_categories:
        roll = random.random() if random_value is None else random_value
        if roll < BASE_TIER_FLAWLESS_CHANCE:
            return GeneratedGem(
                name=gem.name,
                description=gem.description,
                label="flawless",
                value=gem.value,
                uncut_value=gem.uncut_value,
            )
    return gem


def apply_diamond_dust_chance(
    gem: GeneratedGem,
    target_tier: int,
    *,
    random_value: float | None = None,
) -> GeneratedGem:
    """Replace an eligible generated Diamond with Diamond Dust."""
    eligible_tiers = {100, 500, 1000}
    if target_tier not in eligible_tiers or gem.name.casefold() != "diamond":
        return gem

    roll = random.random() if random_value is None else random_value
    if roll >= DIAMOND_DUST_CHANCE:
        return gem

    return GeneratedGem(
        name="Diamond Dust",
        description=gem.description,
        label="dust",
        value=max(gem.value, DIAMOND_DUST_MINIMUM_VALUE),
        uncut_value=gem.uncut_value,
    )


def enforce_final_item_ceiling(
    results: list[GeneratedGem],
    gems: tuple[CategorizedGem, ...],
    target_tier: int,
    *,
    choose=random.choice,
) -> list[GeneratedGem]:
    """Replace any fragment that violates the final requested-tier ceiling."""
    safe_replacements = tuple(
        gem
        for gem in gems_for_tier(gems, target_tier)
        if higher_tier_item_within_ceiling(gem, target_tier)
    )
    if not safe_replacements:
        raise ValueError(f"No safe gem results exist for {target_tier}gp.")

    return [
        gem
        if higher_tier_item_within_ceiling(gem, target_tier)
        else choose(safe_replacements)
        for gem in results
    ]


def generate_gem_results(
    gems: tuple[CategorizedGem, ...],
    target_tier: int,
    count: int,
    *,
    choose=random.choice,
    shuffle=random.shuffle,
) -> list[GeneratedGem]:
    """Generate results while enforcing the distribution for large requests."""
    if target_tier not in GEM_TIERS:
        raise ValueError(
            "Gem value must be one of: "
            + ", ".join(str(tier) for tier in GEM_TIERS)
            + " gp."
        )
    if count < 1 or count > MAX_GEMS:
        raise ValueError(f"Amount must be between 1 and {MAX_GEMS}.")

    if count < 10:
        pool = gems_for_tier(gems, target_tier)
        return [choose(pool) for _ in range(count)]

    target_count = math.ceil(count / 2)
    uncut_or_greater_count = math.ceil(target_count / 2)
    below_uncut_count = target_count - uncut_or_greater_count

    target_sources = tuple(
        gem for gem in gems if gem.uncut_value == target_tier
    )
    uncut_or_greater = tuple(
        generated_from_category(gem)
        for gem in target_sources
        if gem.category in {"uncut", "stone", "gem"}
    )
    below_uncut = tuple(
        generated_from_category(gem)
        for gem in target_sources
        if gem.category in {"chip", "shard"}
    )
    all_values = tuple(
        generated
        for tier in GEM_TIERS
        for generated in gems_for_tier(gems, tier)
        if higher_tier_item_within_ceiling(generated, target_tier)
    )

    results = [
        choose(uncut_or_greater) for _ in range(uncut_or_greater_count)
    ]
    results.extend(choose(below_uncut) for _ in range(below_uncut_count))
    results.extend(
        choose(all_values) for _ in range(count - target_count)
    )
    shuffle(results)
    return results


def split_result_lines(
    lines: list[str], limit: int = EMBED_DESCRIPTION_LIMIT
) -> list[str]:
    """Split result lines without exceeding Discord's description limit."""
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0

    for line in lines:
        safe_line = line if len(line) <= limit else line[: limit - 1] + "…"
        added_length = len(safe_line) + (1 if current else 0)
        if current and current_length + added_length > limit:
            chunks.append("\n".join(current))
            current = []
            current_length = 0
        current.append(safe_line)
        current_length += len(safe_line) + (1 if len(current) > 1 else 0)

    if current:
        chunks.append("\n".join(current))
    return chunks


class GemGrades(commands.Cog):
    """Generate gems whose quality changes their monetary tier."""

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.gem_dir = Path(__file__).resolve().parent / "gems"
        self.gems = load_categorized_gems(self.gem_dir)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.log("Sorting the shinies by size and quality.")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await self.send_error_embed(
                ctx,
                "Use `!gemgrades <value> <amount>` "
                "(for example, `!gemgrades 50 3`).",
            )

    @commands.command(
        name="gemgrades",
        aliases=("gradedgems", "qualitygems"),
    )
    async def gemgrades(self, ctx, *, gemstring):
        """Generate category-adjusted gems: chip, shard, uncut, stone, or gem."""
        parts = gemstring.strip().lower().replace("gp", "").split()
        if len(parts) != 2:
            await self.send_error_embed(
                ctx,
                "Use `!gemgrades <value> <amount>` "
                "(for example, `!gemgrades 50 3`).",
            )
            return

        try:
            target_tier = int(parts[0])
            count = int(parts[1])
        except ValueError:
            await self.send_error_embed(ctx, "Value and amount must be numbers.")
            return

        if target_tier not in GEM_TIERS:
            tiers = ", ".join(f"{tier}gp" for tier in GEM_TIERS)
            await self.send_error_embed(
                ctx, f"Gem value must be one of: {tiers}."
            )
            return
        if not 1 <= count <= MAX_GEMS:
            await self.send_error_embed(
                ctx, f"Amount must be between 1 and {MAX_GEMS}."
            )
            return

        results = [
            apply_diamond_dust_chance(
                apply_base_tier_flawless_chance(gem),
                target_tier,
            )
            for gem in generate_gem_results(
                self.gems, target_tier, count
            )
        ]
        results = enforce_final_item_ceiling(
            results,
            self.gems,
            target_tier,
        )
        chunks = split_result_lines(
            [gem.display() for gem in results]
        )
        self.logger.log(
            f"{ctx.message.author} found {count} categorized "
            f"gems from the {target_tier}gp tier."
        )

        icon_path = os.path.join(
            os.path.dirname(__file__), "../../images/commands/gem-stone.png"
        )
        for index, chunk in enumerate(chunks):
            embed = discord.Embed(
                color=0x019CD0,
                description=chunk,
            )
            title = f"{target_tier}GP CATEGORY-ADJUSTED GEMS"
            if len(chunks) > 1:
                title += f" ({index + 1}/{len(chunks)})"
            embed.set_author(name=title)

            if index == 0:
                icon = discord.File(icon_path, filename="gem-stone.png")
                embed.set_thumbnail(url="attachment://gem-stone.png")
                await self.send_response(ctx, embed=embed, file=icon)
            else:
                await self.send_response(ctx, embed=embed)

    async def send_response(self, ctx, *, embed, file=None):
        kwargs = {"embed": embed}
        if file is not None:
            kwargs["file"] = file
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.message.author.send(**kwargs)
        else:
            await ctx.send(**kwargs)

    async def send_error_embed(self, ctx, message):
        icon_path = os.path.join(
            os.path.dirname(__file__), "../../images/system/prohibited.png"
        )
        icon = discord.File(icon_path, filename="prohibited.png")
        embed = discord.Embed(color=0x019CD0)
        embed.set_author(
            name="GEM GRADES - ERROR",
            icon_url="attachment://prohibited.png",
        )
        embed.add_field(name="Error", value=message, inline=False)
        await self.send_response(ctx, embed=embed, file=icon)


async def setup(bot):
    await bot.add_cog(GemGrades(bot))
