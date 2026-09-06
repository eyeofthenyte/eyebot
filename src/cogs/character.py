"""Discord slash commands for owner-scoped imported character sheets."""

from __future__ import annotations

import html
import io
import mimetypes
import os
import re
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from services.characterService import (
    ABILITY_NAMES,
    SKILL_ABILITIES,
    CharacterError,
    CharacterService,
    ability_modifier,
    character_template_json,
    normalize_character,
    signed,
)


MODE_CHOICES = [
    app_commands.Choice(name="Normal", value="normal"),
    app_commands.Choice(name="Advantage", value="advantage"),
    app_commands.Choice(name="Disadvantage", value="disadvantage"),
]
STAT_CHOICES = [
    app_commands.Choice(name=f"{name} ({key.upper()})", value=key)
    for key, name in ABILITY_NAMES.items()
]
CATEGORY_CHOICES = [
    app_commands.Choice(name="Skill", value="skill"),
    app_commands.Choice(name="Saving Throw", value="save"),
]


def _plain(value, limit=4000):
    selected = html.unescape(re.sub(r"<[^>]+>", "", str(value or ""))).strip()
    if len(selected) <= limit:
        return selected
    return selected[: limit - 14].rstrip() + "\n…[truncated]"


def _display_name(character, *, markdown=True):
    name = str(character["name"])
    nickname = str(character.get("nickname") or "").strip()
    if not nickname:
        return name
    return f"{name} *({nickname})*" if markdown else f"{name} ({nickname})"


def _class_summary(character):
    values = []
    for item in character.get("classes", ()):
        selected = item["name"]
        if item.get("subclass"):
            selected += f" ({item['subclass']})"
        values.append(f"{selected} {item['level']}")
    return " / ".join(values) or f"Adventurer {character.get('level', 1)}"


class CharacterSectionSelect(discord.ui.Select):
    def __init__(self, cog, character):
        self.cog = cog
        self.character = character
        options = [
            discord.SelectOption(label="Summary", value="summary", emoji="📋"),
            discord.SelectOption(label="Skills & Saves", value="skills", emoji="🎯"),
            discord.SelectOption(label="Actions", value="actions", emoji="⚔️"),
            discord.SelectOption(label="Spells", value="spells", emoji="✨"),
            discord.SelectOption(label="Imported Details", value="details", emoji="📖"),
        ]
        super().__init__(
            placeholder="Select a character-sheet section",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction):
        view: CharacterView = self.view
        if interaction.user.id != view.owner_id:
            return await interaction.response.send_message(
                "Only the character owner can use this menu.", ephemeral=True
            )
        view.section = self.values[0]
        view.page = 0
        await view.render(interaction)


class CharacterView(discord.ui.View):
    def __init__(self, cog, character, owner_id):
        super().__init__(timeout=600)
        self.cog = cog
        self.character = character
        self.owner_id = int(owner_id)
        self.section = "summary"
        self.page = 0
        self.add_item(CharacterSectionSelect(cog, character))

    async def interaction_check(self, interaction):
        if interaction.user.id == self.owner_id:
            return True
        await interaction.response.send_message(
            "Only the character owner can use this menu.", ephemeral=True
        )
        return False

    async def render(self, interaction):
        pages = self.cog.section_embeds(self.character, self.section)
        self.page = max(0, min(self.page, len(pages) - 1))
        self.previous.disabled = self.page == 0
        self.next.disabled = self.page >= len(pages) - 1
        await interaction.response.edit_message(embed=pages[self.page], view=self)

    @discord.ui.button(
        label="Previous",
        style=discord.ButtonStyle.secondary,
        row=1,
        disabled=True,
    )
    async def previous(self, interaction, _button):
        self.page -= 1
        await self.render(interaction)

    @discord.ui.button(
        label="Next",
        style=discord.ButtonStyle.secondary,
        row=1,
        disabled=True,
    )
    async def next(self, interaction, _button):
        self.page += 1
        await self.render(interaction)


class DeleteCharacterView(discord.ui.View):
    def __init__(self, cog, owner_id, character):
        super().__init__(timeout=120)
        self.cog = cog
        self.owner_id = int(owner_id)
        self.character = character

    async def interaction_check(self, interaction):
        if interaction.user.id == self.owner_id:
            return True
        await interaction.response.send_message(
            "Only the character owner can confirm this deletion.", ephemeral=True
        )
        return False

    @discord.ui.button(label="Delete character", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, _button):
        removed = self.cog.service.delete(self.owner_id, self.character["id"])
        self.stop()
        await interaction.response.edit_message(
            content=f"🗑️ Deleted **{removed['name']}**.", embed=None, view=None
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, _button):
        self.stop()
        await interaction.response.edit_message(
            content="Character deletion canceled.", embed=None, view=None
        )


class Character(commands.GroupCog, group_name="character", group_description="Import and use your characters"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        settings = dict(getattr(bot, "config", {}).get("characters", {}) or {})
        root = os.getenv("EYEBOT_CHARACTER_DIR") or settings.get("storage_path")
        if not root:
            guild_root = Path(bot.platform_config_service.guild_config_dir)
            root = guild_root.parent / "characters"
        self.service = CharacterService(root, settings=settings, logger=self.logger)

    async def cog_app_command_error(self, interaction, error):
        selected = getattr(error, "original", error)
        if isinstance(selected, CharacterError):
            message = f"❌ {selected}"
        else:
            self.logger.error(f"Character command failed: {selected}")
            message = "❌ EyeBot could not complete that character command."
        sender = (
            interaction.followup.send
            if interaction.response.is_done()
            else interaction.response.send_message
        )
        await sender(message, ephemeral=True)

    async def character_autocomplete(self, interaction, current):
        current = str(current or "").casefold()
        choices = []
        for character in self.service.list(interaction.user.id):
            label = _display_name(character, markdown=False)
            if current in label.casefold():
                choices.append(app_commands.Choice(name=label[:100], value=character["id"]))
        return choices[:25]

    def _selected_character(self, interaction):
        selected = getattr(getattr(interaction, "namespace", None), "character", None)
        if not selected:
            return None
        try:
            return self.service.resolve(interaction.user.id, selected)
        except CharacterError:
            return None

    async def _read_import_attachment(self, attachment):
        maximum = int(self.service.settings.get("max_import_bytes", 10 * 1024 * 1024))
        if int(getattr(attachment, "size", 0) or 0) > maximum:
            raise CharacterError(
                f"Character imports must be no larger than {maximum:,} bytes."
            )
        return await attachment.read(use_cached=True)

    async def skill_autocomplete(self, interaction, current):
        character = self._selected_character(interaction)
        values = (character or {}).get("skills", SKILL_ABILITIES)
        current = str(current or "").casefold()
        return [
            app_commands.Choice(name=name.title(), value=name)
            for name in values
            if current in name.casefold()
        ][:25]

    async def action_autocomplete(self, interaction, current):
        character = self._selected_character(interaction)
        current = str(current or "").casefold()
        return [
            app_commands.Choice(name=item["name"][:100], value=item["name"][:100])
            for item in (character or {}).get("actions", ())
            if current in item["name"].casefold()
        ][:25]

    async def spell_autocomplete(self, interaction, current):
        character = self._selected_character(interaction)
        current = str(current or "").casefold()
        seen = set()
        choices = []
        for item in (character or {}).get("spells", ()):
            name = item["name"]
            if name.casefold() in seen or current not in name.casefold():
                continue
            seen.add(name.casefold())
            choices.append(app_commands.Choice(name=name[:100], value=name[:100]))
        return choices[:25]

    @staticmethod
    def _split_lines(lines, limit=1000):
        fields = []
        current = ""
        expanded = []
        for line in (str(item) for item in lines):
            while len(line) > limit:
                expanded.append(line[:limit])
                line = line[limit:]
            expanded.append(line)
        for line in expanded:
            candidate = f"{current}\n{line}" if current else line
            if len(candidate) > limit and current:
                fields.append(current)
                current = line
            else:
                current = candidate
        if current:
            fields.append(current)
        return fields or ["None recorded."]

    def summary_embed(self, character):
        embed = discord.Embed(
            title=character["name"][:256],
            description=(
                (f"*({character['nickname']})*\n" if character.get("nickname") else "")
                + f"**Level {character['level']} — {_class_summary(character)}**"
            ),
            color=0x7A2E8E,
        )
        if str(character.get("avatar_url", "")).startswith("https://"):
            embed.set_thumbnail(url=character["avatar_url"])
        for key, name in ABILITY_NAMES.items():
            score = character["abilities"][key]
            embed.add_field(
                name=f"{name} ({key.upper()})",
                value=f"**{score}** ({signed(ability_modifier(score))})",
                inline=True,
            )
        embed.add_field(
            name="Combat",
            value=(
                f"**Proficiency:** {signed(character['proficiency_bonus'])}\n"
                f"**Armor Class:** {character['armor_class']}\n"
                f"**Initiative:** {signed(character['initiative'])}\n"
                f"**Speed:** {character['speed']} ft.\n"
                f"**Maximum HP:** {character['max_hit_points']}"
            ),
            inline=False,
        )
        embed.set_footer(
            text=f"Source: {character.get('source', 'manual')} • ID: {character['id']}"
        )
        return embed

    def section_embeds(self, character, section):
        if section == "summary":
            return [self.summary_embed(character)]
        title = f"{_display_name(character, markdown=False)} — {section.title()}"
        page_fields = []
        if section == "skills":
            skill_lines = [
                f"**{name.title()}:** {signed(value)}"
                for name, value in sorted(character.get("skills", {}).items())
            ]
            save_lines = [
                f"**{ABILITY_NAMES[key]}:** {signed(value)}"
                for key, value in character.get("saving_throws", {}).items()
            ]
            for index, value in enumerate(self._split_lines(skill_lines), start=1):
                page_fields.append(
                    ("Skills" if index == 1 else "Skills continued", value)
                )
            page_fields.append(
                ("Saving Throws", "\n".join(save_lines) or "None recorded.")
            )
        elif section == "actions":
            for item in character.get("actions", ()):
                details = []
                if item.get("attack_bonus") is not None:
                    details.append(f"**Attack:** {signed(item['attack_bonus'])}")
                if item.get("damage_rolls"):
                    details.append(
                        "**Damage:** "
                        + ", ".join(f"`{roll}`" for roll in item["damage_rolls"])
                    )
                if item.get("save_dc"):
                    details.append(
                        f"**Save:** DC {item['save_dc']} "
                        f"{str(item.get('save_ability', '')).upper()}"
                    )
                description = _plain(item.get("description"), 700)
                page_fields.append(
                    (
                        item["name"][:256],
                        "\n".join(details + ([description] if description else []))
                        or "No details recorded.",
                    )
                )
        elif section == "spells":
            for item in character.get("spells", ()):
                details = [f"**Level:** {item['level']}"]
                if item.get("attack_bonus") is not None:
                    details.append(f"**Spell attack:** {signed(item['attack_bonus'])}")
                if item.get("save_dc"):
                    details.append(
                        f"**Save:** DC {item['save_dc']} "
                        f"{str(item.get('save_ability', '')).upper()}"
                    )
                if item.get("damage_rolls"):
                    details.append(
                        "**Damage:** "
                        + ", ".join(f"`{roll}`" for roll in item["damage_rolls"])
                    )
                description = _plain(item.get("description"), 700)
                page_fields.append(
                    (
                        item["name"][:256],
                        "\n".join(details + ([description] if description else [])),
                    )
                )
        else:
            import json

            for name, value in list(character.get("sections", {}).items())[:25]:
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False, indent=2)
                chunks = self._split_lines(str(value).splitlines() or ["None"], 1000)
                for index, chunk in enumerate(chunks[:20], start=1):
                    field_name = str(name)[:256]
                    if index > 1:
                        field_name = f"{field_name[:235]} — continued {index}"
                    page_fields.append((field_name, _plain(chunk, 1000) or "None"))

        if not page_fields:
            return [
                discord.Embed(
                    title=title,
                    description="None recorded.",
                    color=0x7A2E8E,
                )
            ]
        pages = []
        current = []
        current_size = len(title)
        for name, value in page_fields:
            field_size = len(name) + len(value)
            if current and (
                len(current) >= 5 or current_size + field_size > 5500
            ):
                pages.append(current)
                current = []
                current_size = len(title)
            current.append((name, value))
            current_size += field_size
        if current:
            pages.append(current)

        embeds = []
        for page_number, fields in enumerate(pages, start=1):
            page_title = title
            if len(pages) > 1:
                page_title = f"{title[:225]} — {page_number}/{len(pages)}"
            embed = discord.Embed(title=page_title, color=0x7A2E8E)
            for name, value in fields:
                embed.add_field(name=name, value=value, inline=False)
            embeds.append(embed)
        return embeds

    def section_embed(self, character, section):
        return self.section_embeds(character, section)[0]

    async def _send_sheet(self, interaction, character):
        embed = self.summary_embed(character)
        view = CharacterView(self, character, interaction.user.id)
        kwargs = {"embed": embed, "view": view}
        image_path = character.get("image_path")
        if image_path and Path(image_path).is_file():
            filename = f"character-{character['id']}.png"
            kwargs["file"] = discord.File(image_path, filename=filename)
            embed.set_thumbnail(url=f"attachment://{filename}")
        await interaction.response.send_message(**kwargs)

    @app_commands.command(name="list", description="List characters linked to your Discord account")
    async def list_characters(self, interaction: discord.Interaction):
        characters = self.service.list(interaction.user.id)
        if not characters:
            return await interaction.response.send_message(
                "You have no imported characters. Use `/character import-pdf`, "
                "`/character import-json`, or `/character create`.",
                ephemeral=True,
            )
        lines = [
            f"• **{_display_name(item)}** — level {item['level']} {_class_summary(item)}"
            for item in characters
        ]
        await interaction.response.send_message("\n".join(lines)[:4000], ephemeral=True)

    @app_commands.command(name="template", description="Download a documented character JSON template")
    async def template(self, interaction: discord.Interaction):
        attachment = discord.File(
            io.BytesIO(character_template_json()),
            filename="eyebot-character-template.json",
        )
        await interaction.response.send_message(
            "Fill in this template, preserve valid JSON syntax, then upload it with "
            "`/character import-json`. Instruction keys beginning with `_` are ignored.",
            file=attachment,
            ephemeral=True,
        )

    @app_commands.command(name="show", description="Display one of your character sheets")
    @app_commands.autocomplete(character=character_autocomplete)
    async def show(self, interaction: discord.Interaction, character: str):
        await self._send_sheet(interaction, self.service.resolve(interaction.user.id, character))

    @app_commands.command(name="import-pdf", description="Import your editable D&D character-sheet PDF")
    async def import_pdf(self, interaction: discord.Interaction, file: discord.Attachment):
        await interaction.response.defer(ephemeral=True, thinking=True)
        data = await self._read_import_attachment(file)
        character = self.service.import_pdf(interaction.user.id, data)
        await interaction.followup.send(f"✅ Imported **{character['name']}** from PDF.", ephemeral=True)

    @app_commands.command(name="import-json", description="Import an EyeBot or manually supplied character JSON file")
    async def import_json(self, interaction: discord.Interaction, file: discord.Attachment):
        await interaction.response.defer(ephemeral=True, thinking=True)
        data = await self._read_import_attachment(file)
        character = self.service.import_json(interaction.user.id, data)
        await interaction.followup.send(f"✅ Imported **{character['name']}** from JSON.", ephemeral=True)

    @app_commands.command(name="create", description="Create a character manually")
    async def create(
        self,
        interaction: discord.Interaction,
        name: app_commands.Range[str, 1, 100],
        class_name: app_commands.Range[str, 1, 100],
        level: app_commands.Range[int, 1, 20],
        strength: app_commands.Range[int, 1, 30],
        dexterity: app_commands.Range[int, 1, 30],
        constitution: app_commands.Range[int, 1, 30],
        intelligence: app_commands.Range[int, 1, 30],
        wisdom: app_commands.Range[int, 1, 30],
        charisma: app_commands.Range[int, 1, 30],
        armor_class: app_commands.Range[int, 0, 100],
        max_hit_points: app_commands.Range[int, 1, 100000],
        subclass: app_commands.Range[str, 0, 100] = "",
        speed: app_commands.Range[int, 0, 1000] = 30,
        initiative: app_commands.Range[int, -100, 100] | None = None,
    ):
        payload = {
            "name": name,
            "classes": [{"name": class_name, "subclass": subclass, "level": level}],
            "abilities": {
                "str": strength, "dex": dexterity, "con": constitution,
                "int": intelligence, "wis": wisdom, "cha": charisma,
            },
            "armor_class": armor_class,
            "max_hit_points": max_hit_points,
            "speed": speed,
            "initiative": initiative if initiative is not None else ability_modifier(dexterity),
            "source": "manual",
        }
        character = self.service.save(interaction.user.id, normalize_character(payload, str(interaction.user.id), source="manual"))
        await interaction.response.send_message(f"✅ Created **{character['name']}**.", ephemeral=True)

    @app_commands.command(name="refresh", description="Replace a character from a new PDF or JSON file")
    @app_commands.autocomplete(character=character_autocomplete)
    async def refresh(self, interaction: discord.Interaction, character: str, file: discord.Attachment):
        await interaction.response.defer(ephemeral=True, thinking=True)
        data = await self._read_import_attachment(file)
        filename = str(file.filename or "").casefold()
        if filename.endswith(".pdf"):
            refreshed = self.service.import_pdf(interaction.user.id, data, replace_selector=character)
        elif filename.endswith(".json"):
            refreshed = self.service.import_json(interaction.user.id, data, replace_selector=character)
        else:
            raise CharacterError("Refresh files must use the `.pdf` or `.json` extension.")
        await interaction.followup.send(f"✅ Refreshed **{refreshed['name']}**.", ephemeral=True)

    @app_commands.command(name="nickname", description="Set or clear a character nickname")
    @app_commands.autocomplete(character=character_autocomplete)
    async def nickname(self, interaction: discord.Interaction, character: str, nickname: app_commands.Range[str, 0, 100] = ""):
        updated = self.service.update(interaction.user.id, character, nickname=nickname)
        message = f"✅ Nickname updated for **{updated['name']}**." if nickname else f"✅ Nickname cleared for **{updated['name']}**."
        await interaction.response.send_message(message, ephemeral=True)

    @app_commands.command(name="image", description="Replace a character portrait")
    @app_commands.autocomplete(character=character_autocomplete)
    async def image(self, interaction: discord.Interaction, character: str, image: discord.Attachment):
        await interaction.response.defer(ephemeral=True, thinking=True)
        content_type = image.content_type or mimetypes.guess_type(image.filename)[0] or ""
        maximum = int(self.service.settings.get("max_image_bytes", 5 * 1024 * 1024))
        if int(getattr(image, "size", 0) or 0) > maximum:
            raise CharacterError(
                f"Character images must be no larger than {maximum:,} bytes."
            )
        updated = self.service.store_image(
            interaction.user.id,
            character,
            await image.read(use_cached=True),
            content_type,
        )
        await interaction.followup.send(f"✅ Updated the portrait for **{updated['name']}**.", ephemeral=True)

    @app_commands.command(name="post", description="Post in character using the character's name and portrait")
    @app_commands.autocomplete(character=character_autocomplete)
    async def post(self, interaction: discord.Interaction, character: str, text: app_commands.Range[str, 1, 1800]):
        selected = self.service.resolve(interaction.user.id, character)
        display = discord.utils.escape_markdown(_display_name(selected, markdown=False))
        nickname = str(selected.get("nickname") or "").strip()
        heading = f"**{discord.utils.escape_markdown(selected['name'])}**"
        if nickname:
            heading += f" *({discord.utils.escape_markdown(nickname)})*"
        embed = discord.Embed(description=text, color=0x7A2E8E)
        embed.set_author(name=display[:256])
        kwargs = {"content": heading, "embed": embed, "allowed_mentions": discord.AllowedMentions.none()}
        image_path = selected.get("image_path")
        if image_path and Path(image_path).is_file():
            filename = f"character-{selected['id']}.png"
            kwargs["file"] = discord.File(image_path, filename=filename)
            embed.set_thumbnail(url=f"attachment://{filename}")
        elif str(selected.get("avatar_url", "")).startswith("https://"):
            embed.set_thumbnail(url=selected["avatar_url"])
        await interaction.response.send_message(**kwargs)

    @app_commands.command(name="download", description="Download one of your characters as EyeBot JSON")
    @app_commands.autocomplete(character=character_autocomplete)
    async def download(self, interaction: discord.Interaction, character: str):
        selected = self.service.resolve(interaction.user.id, character)
        file = discord.File(
            io.BytesIO(self.service.export(interaction.user.id, character)),
            filename=f"{re.sub(r'[^a-zA-Z0-9_-]+', '-', selected['name']).strip('-') or 'character'}.json",
        )
        await interaction.response.send_message(file=file, ephemeral=True)

    @app_commands.command(name="delete", description="Delete one of your characters after confirmation")
    @app_commands.autocomplete(character=character_autocomplete)
    async def delete(self, interaction: discord.Interaction, character: str):
        selected = self.service.resolve(interaction.user.id, character)
        await interaction.response.send_message(
            f"Delete **{selected['name']}** permanently?",
            view=DeleteCharacterView(self, interaction.user.id, selected),
            ephemeral=True,
        )

    def _roller(self):
        roller = self.bot.get_cog("Roll")
        if roller is None:
            raise CharacterError("The bounded dice roller is not currently available.")
        return roller

    def _validate_damage_rolls(self, value):
        for expression in re.split(r"\s*(?:,|;)\s*", value):
            if not expression:
                continue
            try:
                self._roller().validate_full_expression(expression)
            except ValueError as error:
                raise CharacterError(f"Invalid damage expression `{expression}`: {error}") from error

    @staticmethod
    def _roll_expression(modifier, mode):
        suffix = "adv" if mode == "advantage" else "dis" if mode == "disadvantage" else ""
        return f"1d20{suffix}{modifier:+d}" if modifier else f"1d20{suffix}"

    def _roll_embed(self, character, label, modifier, extra_modifier, mode):
        combined = int(modifier) + int(extra_modifier)
        expression = self._roll_expression(combined, mode)
        total, details = self._roller().roll_full_expression(expression)
        first = details[0][1][0]
        if first.get("tag"):
            rolls = f"{first['rolls_1']} and {first['rolls_2']} → {first['tag']} selected {first['total']}"
        else:
            rolls = f"{first['rolls']}"
        embed = discord.Embed(
            title=f"🎲 {_display_name(character, markdown=False)} — {label}",
            description=(
                f"**Roll:** `{expression}`\n"
                f"**Dice:** {rolls}\n"
                f"**Character modifier:** {signed(modifier)}\n"
                f"**Additional modifier:** {signed(extra_modifier)}\n"
                f"## Total: {total}"
            ),
            color=0x7A2E8E,
        )
        return embed

    @app_commands.command(name="check", description="Roll an ability check for one of your characters")
    @app_commands.autocomplete(character=character_autocomplete)
    @app_commands.choices(stat=STAT_CHOICES, mode=MODE_CHOICES)
    async def check(self, interaction: discord.Interaction, character: str, stat: app_commands.Choice[str], modifier: app_commands.Range[int, -100, 100] = 0, mode: app_commands.Choice[str] | None = None):
        selected = self.service.resolve(interaction.user.id, character)
        base = ability_modifier(selected["abilities"][stat.value])
        await interaction.response.send_message(embed=self._roll_embed(selected, f"{ABILITY_NAMES[stat.value]} Check", base, modifier, mode.value if mode else "normal"))

    @app_commands.command(name="skill", description="Roll a skill check for one of your characters")
    @app_commands.autocomplete(character=character_autocomplete, skill=skill_autocomplete)
    @app_commands.choices(mode=MODE_CHOICES)
    async def skill(self, interaction: discord.Interaction, character: str, skill: str, modifier: app_commands.Range[int, -100, 100] = 0, mode: app_commands.Choice[str] | None = None):
        selected = self.service.resolve(interaction.user.id, character)
        key = skill.casefold()
        if key not in selected["skills"]:
            raise CharacterError("That skill is not recorded for this character.")
        await interaction.response.send_message(embed=self._roll_embed(selected, f"{key.title()} Check", selected["skills"][key], modifier, mode.value if mode else "normal"))

    @app_commands.command(name="save", description="Roll a saving throw for one of your characters")
    @app_commands.autocomplete(character=character_autocomplete)
    @app_commands.choices(stat=STAT_CHOICES, mode=MODE_CHOICES)
    async def save(self, interaction: discord.Interaction, character: str, stat: app_commands.Choice[str], modifier: app_commands.Range[int, -100, 100] = 0, mode: app_commands.Choice[str] | None = None):
        selected = self.service.resolve(interaction.user.id, character)
        await interaction.response.send_message(embed=self._roll_embed(selected, f"{ABILITY_NAMES[stat.value]} Save", selected["saving_throws"][stat.value], modifier, mode.value if mode else "normal"))

    @app_commands.command(name="action", description="Use one of a character's imported actions")
    @app_commands.autocomplete(character=character_autocomplete, action=action_autocomplete)
    @app_commands.choices(mode=MODE_CHOICES)
    async def action(self, interaction: discord.Interaction, character: str, action: str, modifier: app_commands.Range[int, -100, 100] = 0, mode: app_commands.Choice[str] | None = None):
        selected = self.service.resolve(interaction.user.id, character)
        item = next((value for value in selected["actions"] if value["name"].casefold() == action.casefold()), None)
        if item is None:
            raise CharacterError("That action is not recorded for this character.")
        embed = discord.Embed(title=f"⚔️ {_display_name(selected, markdown=False)} — {item['name']}", description=_plain(item.get("description")) or "No description recorded.", color=0x7A2E8E)
        if item.get("attack_bonus") is not None:
            total, _ = self._roller().roll_full_expression(self._roll_expression(item["attack_bonus"] + modifier, mode.value if mode else "normal"))
            embed.add_field(name="Attack roll", value=f"**{total}** ({signed(item['attack_bonus'] + modifier)})", inline=False)
        for index, expression in enumerate(item.get("damage_rolls", ()), start=1):
            total, _ = self._roller().roll_full_expression(expression)
            embed.add_field(name=f"Damage {index}", value=f"`{expression}` → **{total}**", inline=True)
        if item.get("save_dc"):
            embed.add_field(name="Saving throw", value=f"DC {item['save_dc']} {str(item.get('save_ability', '')).upper()}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="spell", description="Display an imported spell at an applicable level")
    @app_commands.autocomplete(character=character_autocomplete, spell=spell_autocomplete)
    async def spell(self, interaction: discord.Interaction, character: str, spell: str, level: app_commands.Range[int, 0, 9] | None = None):
        selected = self.service.resolve(interaction.user.id, character)
        candidates = [item for item in selected["spells"] if item["name"].casefold() == spell.casefold()]
        if not candidates:
            raise CharacterError("That spell is not recorded for this character.")
        item = candidates[0]
        cast_level = item["level"] if level is None else level
        if item["level"] and cast_level < item["level"]:
            raise CharacterError(f"{item['name']} must be cast at level {item['level']} or higher.")
        embed = discord.Embed(title=f"✨ {_display_name(selected, markdown=False)} — {item['name']}", description=_plain(item.get("description")) or "No description recorded.", color=0x7A2E8E)
        embed.add_field(name="Level", value=str(cast_level), inline=True)
        if item.get("attack_bonus") is not None:
            embed.add_field(name="Spell attack", value=signed(item["attack_bonus"]), inline=True)
        if item.get("save_dc"):
            embed.add_field(name="Saving throw", value=f"DC {item['save_dc']} {str(item.get('save_ability', '')).upper()}", inline=True)
        rolls = item.get("damage_rolls", [])
        by_level = item.get("damage_rolls_by_level", {})
        if str(cast_level) in by_level:
            rolls = by_level[str(cast_level)]
        elif item["level"] == 0:
            eligible = [int(key) for key in by_level if int(key) <= selected["level"]]
            if eligible:
                rolls = by_level[str(max(eligible))]
        if rolls:
            embed.add_field(name="Damage", value="\n".join(f"`{roll}`" for roll in rolls), inline=False)
        if item.get("higher_levels"):
            embed.add_field(name="At higher levels", value=_plain(item["higher_levels"], 1000), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="modifier", description="Set an imported skill or saving-throw modifier")
    @app_commands.autocomplete(character=character_autocomplete)
    @app_commands.choices(category=CATEGORY_CHOICES)
    async def modifier(self, interaction: discord.Interaction, character: str, category: app_commands.Choice[str], name: str, value: app_commands.Range[int, -100, 100]):
        selected = self.service.resolve(interaction.user.id, character)
        payload = selected
        if category.value == "skill":
            key = name.casefold()
            if key not in SKILL_ABILITIES:
                raise CharacterError("Use a standard D&D skill name.")
            payload["skills"][key] = value
        else:
            key = name.casefold()[:3]
            if key not in ABILITY_NAMES:
                raise CharacterError("Saving throws must use STR, DEX, CON, INT, WIS, or CHA.")
            payload["saving_throws"][key] = value
        self.service.save(interaction.user.id, payload, replace_selector=character)
        await interaction.response.send_message(f"✅ Set {name} to {signed(value)} for **{selected['name']}**.", ephemeral=True)

    @app_commands.command(name="action-add", description="Add or replace a character action")
    @app_commands.autocomplete(character=character_autocomplete)
    async def action_add(self, interaction: discord.Interaction, character: str, name: app_commands.Range[str, 1, 100], description: app_commands.Range[str, 0, 1000] = "", attack_bonus: app_commands.Range[int, -100, 100] | None = None, damage_rolls: app_commands.Range[str, 0, 200] = ""):
        selected = self.service.resolve(interaction.user.id, character)
        self._validate_damage_rolls(damage_rolls)
        selected["actions"] = [item for item in selected["actions"] if item["name"].casefold() != name.casefold()]
        selected["actions"].append({"name": name, "description": description, "attack_bonus": attack_bonus, "damage_rolls": damage_rolls})
        self.service.save(interaction.user.id, selected, replace_selector=character)
        await interaction.response.send_message(f"✅ Saved action **{name}**.", ephemeral=True)

    @app_commands.command(name="spell-add", description="Add or replace a character spell")
    @app_commands.autocomplete(character=character_autocomplete)
    async def spell_add(self, interaction: discord.Interaction, character: str, name: app_commands.Range[str, 1, 100], level: app_commands.Range[int, 0, 9], description: app_commands.Range[str, 0, 1000] = "", attack_bonus: app_commands.Range[int, -100, 100] | None = None, save_ability: app_commands.Range[str, 0, 3] = "", save_dc: app_commands.Range[int, 1, 100] | None = None, damage_rolls: app_commands.Range[str, 0, 200] = ""):
        selected = self.service.resolve(interaction.user.id, character)
        if save_ability and save_ability.casefold() not in ABILITY_NAMES:
            raise CharacterError(
                "Spell saves must use STR, DEX, CON, INT, WIS, or CHA."
            )
        self._validate_damage_rolls(damage_rolls)
        selected["spells"] = [item for item in selected["spells"] if item["name"].casefold() != name.casefold()]
        selected["spells"].append({"name": name, "level": level, "description": description, "attack_bonus": attack_bonus, "save_ability": save_ability, "save_dc": save_dc, "damage_rolls": damage_rolls})
        self.service.save(interaction.user.id, selected, replace_selector=character)
        await interaction.response.send_message(f"✅ Saved spell **{name}**.", ephemeral=True)


async def setup(bot):
    settings = dict(getattr(bot, "config", {}).get("characters", {}) or {})
    if settings.get("enabled", True):
        await bot.add_cog(Character(bot))
