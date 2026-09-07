"""Discord slash commands for owner-scoped imported character sheets."""

from __future__ import annotations

import asyncio
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

EPHEMERAL_DELETE_AFTER = 30
CHARACTER_WEBHOOK_NAME = "EyeBot Characters"


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
SECTION_CHOICES = [
    app_commands.Choice(name="Equipment", value="Equipment"),
    app_commands.Choice(name="Features and Traits", value="Features and Traits"),
    app_commands.Choice(name="Background", value="Background"),
    app_commands.Choice(name="Notes", value="Notes"),
]
SHOW_SECTION_CHOICES = [
    app_commands.Choice(name="Summary", value="summary"),
    app_commands.Choice(name="Skills (Skills & Saves)", value="skills"),
    app_commands.Choice(name="Actions", value="actions"),
    app_commands.Choice(name="Spells", value="spells"),
    app_commands.Choice(name="Equipment", value="equipment"),
    app_commands.Choice(name="Feats (Features & Traits)", value="features"),
    app_commands.Choice(name="Background", value="background"),
    app_commands.Choice(name="Notes", value="notes"),
]
SHOW_ALL_SECTION_ORDER = (
    "skills", "actions", "spells", "equipment", "features", "background", "notes"
)


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
            discord.SelectOption(label="Equipment", value="equipment", emoji="🎒"),
            discord.SelectOption(label="Features & Traits", value="features", emoji="📖"),
            discord.SelectOption(label="Background", value="background", emoji="🪶"),
            discord.SelectOption(label="Notes", value="notes", emoji="📝"),
        ]
        super().__init__(
            placeholder="Select a character-sheet section",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction):
        view: CharacterView = self.view
        if interaction.user.id != view.owner_id:
            return await interaction.response.send_message(
                "Only the character owner can use this menu.",
                ephemeral=True,
                delete_after=EPHEMERAL_DELETE_AFTER,
            )
        view.section = self.values[0]
        view.page = 0
        await view.render(interaction)


class CharacterSkillRollSelect(discord.ui.Select):
    def __init__(self, cog, character):
        self.cog = cog
        self.character = character
        options = [
            discord.SelectOption(
                label=f"{name.title()} ({signed(modifier)})"[:100],
                value=name,
            )
            for name, modifier in sorted(character.get("skills", {}).items())
        ][:25]
        super().__init__(
            placeholder="Roll a skill check",
            min_values=1,
            max_values=1,
            options=options,
            row=2,
        )

    async def callback(self, interaction):
        skill = self.values[0]
        modifier = self.character["skills"][skill]
        embed = self.cog._roll_embed(
            self.character,
            f"{skill.title()} Check",
            modifier,
            0,
            "normal",
        )
        await interaction.response.send_message(embed=embed)


class CharacterSaveRollSelect(discord.ui.Select):
    def __init__(self, cog, character):
        self.cog = cog
        self.character = character
        options = [
            discord.SelectOption(
                label=f"{ABILITY_NAMES[key]} ({signed(modifier)})"[:100],
                value=key,
            )
            for key, modifier in character.get("saving_throws", {}).items()
        ][:25]
        super().__init__(
            placeholder="Roll a saving throw",
            min_values=1,
            max_values=1,
            options=options,
            row=3,
        )

    async def callback(self, interaction):
        ability = self.values[0]
        modifier = self.character["saving_throws"][ability]
        embed = self.cog._roll_embed(
            self.character,
            f"{ABILITY_NAMES[ability]} Save",
            modifier,
            0,
            "normal",
        )
        await interaction.response.send_message(embed=embed)


class CharacterActionAttackSelect(discord.ui.Select):
    def __init__(self, cog, character):
        self.cog = cog
        self.character = character
        options = [
            discord.SelectOption(
                label=f"{item['name']} Attack ({signed(item['attack_bonus'])})"[:100],
                value=str(index),
            )
            for index, item in enumerate(character.get("actions", ()))
            if item.get("attack_bonus") is not None
        ][:25]
        super().__init__(placeholder="Roll an action attack", options=options, row=2)

    async def callback(self, interaction):
        item = self.character["actions"][int(self.values[0])]
        embed = self.cog._roll_embed(
            self.character, f"{item['name']} Attack", item["attack_bonus"], 0, "normal"
        )
        await interaction.response.send_message(embed=embed)


class CharacterActionDamageSelect(discord.ui.Select):
    def __init__(self, cog, character):
        self.cog = cog
        self.character = character
        choices = []
        for action_index, item in enumerate(character.get("actions", ())):
            types = item.get("damage_types", ())
            for damage_index, expression in enumerate(item.get("damage_rolls", ())):
                damage_type = types[damage_index] if damage_index < len(types) else ""
                label = f"{item['name']} Damage ({expression}"
                label += f" {damage_type})" if damage_type else ")"
                choices.append((label[:100], f"{action_index}:{damage_index}"))
        options = [discord.SelectOption(label=label, value=value) for label, value in choices[:25]]
        super().__init__(placeholder="Roll action damage", options=options, row=3)

    async def callback(self, interaction):
        action_index, damage_index = map(int, self.values[0].split(":"))
        item = self.character["actions"][action_index]
        expression = item["damage_rolls"][damage_index]
        types = item.get("damage_types", ())
        damage_type = types[damage_index] if damage_index < len(types) else ""
        embed = self.cog._damage_roll_embed(
            self.character, item["name"], expression, damage_type
        )
        await interaction.response.send_message(embed=embed)


class CharacterView(discord.ui.View):
    def __init__(self, cog, character, owner_id):
        super().__init__(timeout=600)
        self.cog = cog
        self.character = character
        self.owner_id = int(owner_id)
        self.section = "summary"
        self.page = 0
        self.add_item(CharacterSectionSelect(cog, character))

    def sync_section_controls(self):
        for child in tuple(self.children):
            if isinstance(child, (
                CharacterSkillRollSelect,
                CharacterSaveRollSelect,
                CharacterActionAttackSelect,
                CharacterActionDamageSelect,
            )):
                self.remove_item(child)
        if self.section == "skills":
            self.add_item(CharacterSkillRollSelect(self.cog, self.character))
            self.add_item(CharacterSaveRollSelect(self.cog, self.character))
        elif self.section == "actions":
            if any(item.get("attack_bonus") is not None for item in self.character.get("actions", ())):
                self.add_item(CharacterActionAttackSelect(self.cog, self.character))
            if any(item.get("damage_rolls") for item in self.character.get("actions", ())):
                self.add_item(CharacterActionDamageSelect(self.cog, self.character))

    async def interaction_check(self, interaction):
        if interaction.user.id == self.owner_id:
            return True
        await interaction.response.send_message(
            "Only the character owner can use this menu.",
            ephemeral=True,
            delete_after=EPHEMERAL_DELETE_AFTER,
        )
        return False

    async def render(self, interaction):
        pages = self.cog.section_embeds(self.character, self.section)
        self.page = max(0, min(self.page, len(pages) - 1))
        self.previous.disabled = self.page == 0
        self.next.disabled = self.page >= len(pages) - 1
        self.sync_section_controls()
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
            "Only the character owner can confirm this deletion.",
            ephemeral=True,
            delete_after=EPHEMERAL_DELETE_AFTER,
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
    add = app_commands.Group(
        name="add",
        description="Add containers and equipment to a character",
    )

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        settings = dict(getattr(bot, "config", {}).get("characters", {}) or {})
        root = os.getenv("EYEBOT_CHARACTER_DIR") or settings.get("storage_path")
        if not root:
            guild_root = Path(bot.platform_config_service.guild_config_dir)
            root = guild_root.parent / "characters"
        self.service = CharacterService(root, settings=settings, logger=self.logger)
        self._ephemeral_deletion_tasks = set()

    def cog_unload(self):
        for task in self._ephemeral_deletion_tasks:
            task.cancel()
        self._ephemeral_deletion_tasks.clear()

    async def _delete_followup_after(self, message, delay):
        try:
            await asyncio.sleep(delay)
            await message.delete()
        except (asyncio.CancelledError, discord.HTTPException):
            pass

    async def _send_ephemeral_followup(self, interaction, content=None, **kwargs):
        message = await interaction.followup.send(
            content,
            ephemeral=True,
            wait=True,
            **kwargs,
        )
        task = asyncio.create_task(
            self._delete_followup_after(message, EPHEMERAL_DELETE_AFTER)
        )
        self._ephemeral_deletion_tasks.add(task)
        task.add_done_callback(self._ephemeral_deletion_tasks.discard)
        return message

    async def cog_app_command_error(self, interaction, error):
        selected = getattr(error, "original", error)
        if isinstance(selected, CharacterError):
            message = f"❌ {selected}"
        else:
            self.logger.error(f"Character command failed: {selected}")
            message = "❌ EyeBot could not complete that character command."
        if interaction.response.is_done():
            await self._send_ephemeral_followup(interaction, message)
        else:
            await interaction.response.send_message(
                message,
                ephemeral=True,
                delete_after=EPHEMERAL_DELETE_AFTER,
            )

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
        # Interaction attachments are still available from Discord's original CDN.
        # The cached proxy URL can reject non-image assets such as PDFs with 415
        # "failed to get asset", so do not route imports through the media proxy.
        data = await attachment.read(use_cached=False)
        if len(data) > maximum:
            raise CharacterError(
                f"Character imports must be no larger than {maximum:,} bytes."
            )
        return data

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

    async def subsection_autocomplete(self, interaction, current):
        character = self._selected_character(interaction)
        section = getattr(getattr(interaction, "namespace", None), "section", None)
        section = getattr(section, "value", section)
        values = (character or {}).get("sections", {}).get(str(section), {})
        current = str(current or "").casefold()
        return [
            app_commands.Choice(name=str(name)[:100], value=str(name)[:100])
            for name in values
            if current in str(name).casefold()
        ][:25] if isinstance(values, dict) else []

    async def section_item_autocomplete(self, interaction, current):
        character = self._selected_character(interaction)
        section = getattr(getattr(interaction, "namespace", None), "section", None)
        section = getattr(section, "value", section)
        subsection = getattr(getattr(interaction, "namespace", None), "subsection", None)
        value = (character or {}).get("sections", {}).get(str(section), {}).get(str(subsection))
        names = value.keys() if isinstance(value, dict) else [
            item.get("name", "") if isinstance(item, dict) else str(item)
            for item in (value or [])
        ] if isinstance(value, list) else []
        current = str(current or "").casefold()
        return [
            app_commands.Choice(name=str(name)[:100], value=str(name)[:100])
            for name in names if name and current in str(name).casefold()
        ][:25]

    async def container_autocomplete(self, interaction, current):
        character = self._selected_character(interaction)
        containers = (character or {}).get("sections", {}).get("Equipment", {})
        current = str(current or "").casefold()
        return [
            app_commands.Choice(name=str(name)[:100], value=str(name)[:100])
            for name in containers
            if current in str(name).casefold()
        ][:25] if isinstance(containers, dict) else []

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
        structured_sections = {
            "equipment": "Equipment",
            "features": "Features and Traits",
            "background": "Background",
            "notes": "Notes",
        }
        if section in structured_sections:
            return self._structured_section_embeds(character, structured_sections[section])
        title = f"{_display_name(character, markdown=False)} — {section.title()}"
        page_fields = []
        if section == "skills":
            skill_lines = [
                f"**__{name.title()}:__** {signed(value)}"
                for name, value in sorted(character.get("skills", {}).items())
            ]
            save_lines = [
                f"**__{ABILITY_NAMES[key]}:__** {signed(value)}"
                for key, value in character.get("saving_throws", {}).items()
            ]
            for index, value in enumerate(self._split_lines(skill_lines), start=1):
                page_fields.append(
                    ("__Skills__" if index == 1 else "__Skills continued__", value)
                )
            page_fields.append(
                ("__Saving Throws__", "\n".join(save_lines) or "None recorded.")
            )
        elif section == "actions":
            for item in character.get("actions", ()):
                details = []
                if item.get("attack_bonus") is not None:
                    details.append(f"- **Attack:** {signed(item['attack_bonus'])}")
                damage_types = item.get("damage_types", ())
                for index, roll in enumerate(item.get("damage_rolls", ())):
                    damage_type = damage_types[index] if index < len(damage_types) else ""
                    suffix = f" {damage_type}" if damage_type else ""
                    details.append(f"  - **Damage:** `{roll}`{suffix}")
                if item.get("save_dc"):
                    details.append(
                        f"- **Save:** DC {item['save_dc']} "
                        f"{str(item.get('save_ability', '')).upper()}"
                    )
                description = _plain(item.get("description"), 700)
                if description:
                    details.extend(f"  - {line}" for line in description.splitlines() if line)
                page_fields.append(
                    (
                        item["name"][:256],
                        "\n".join(details) or "No details recorded.",
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

    def _structured_section_embeds(self, character, main_section):
        value = character.get("sections", {}).get(main_section, {})
        if not isinstance(value, dict):
            value = {"Other": value}
        pages = []
        for subsection, items in value.items():
            lines = []
            if isinstance(items, dict):
                for name, detail in items.items():
                    if main_section == "Background" and subsection == "Appearance":
                        lines.append(f"**{name}:** {_plain(detail or 'NONE', 3000)}")
                    else:
                        lines.append(f"**{name}**")
                    if isinstance(detail, list) and not (
                        main_section == "Background" and subsection == "Appearance"
                    ):
                        lines.extend(
                            f"  - {_plain(value, 2800)}" for value in detail
                        )
                    elif not (main_section == "Background" and subsection == "Appearance"):
                        lines.append(f"  - {_plain(detail, 3000)}")
            elif isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        name = _plain(item.get("name") or "Item", 200)
                        quantity = item.get("quantity")
                        quantity_text = f" x {quantity}" if quantity not in (None, "") else ""
                        lines.append(f"**{name}**{quantity_text}")
                        if main_section == "Features and Traits":
                            for detail in item.get("details") or []:
                                lines.append(f"  - {_plain(detail, 2800)}")
                        elif item.get("description"):
                            lines.append(f"  - {_plain(item['description'], 2800)}")
                    else:
                        readable = _plain(item, 3000)
                        if main_section == "Features and Traits" and " • " in readable:
                            feature_name, detail = readable.split(" • ", 1)
                            lines.append(f"**{feature_name}**")
                            lines.append(f"  - {detail}")
                        else:
                            lines.append(f"- {readable}")
            elif str(items or "").strip():
                lines.extend(_plain(items, 12000).splitlines())
            if not lines:
                lines = ["**BLANK**"]
            chunks = self._split_lines(lines, 3500)
            for index, chunk in enumerate(chunks, start=1):
                suffix = f" ({index}/{len(chunks)})" if len(chunks) > 1 else ""
                embed = discord.Embed(
                    title=_display_name(character, markdown=False)[:256],
                    description=(
                        f"# __{main_section}__\n"
                        f"## {str(subsection)[:100]}{suffix}\n"
                        f"{chunk}"
                    )[:4096],
                    color=0x7A2E8E,
                )
                pages.append(embed)
        return pages or [discord.Embed(
            title=_display_name(character, markdown=False)[:256],
            description=f"# __{main_section}__\n*None recorded.*",
            color=0x7A2E8E,
        )]

    def section_embed(self, character, section):
        return self.section_embeds(character, section)[0]

    async def _send_sheet(self, interaction, character, *, ephemeral=False, with_view=True):
        embed = self.summary_embed(character)
        kwargs = {"embed": embed, "ephemeral": ephemeral}
        if ephemeral:
            kwargs["delete_after"] = EPHEMERAL_DELETE_AFTER
        if with_view:
            kwargs["view"] = CharacterView(self, character, interaction.user.id)
        image_path = character.get("image_path")
        if image_path and Path(image_path).is_file():
            filename = f"character-{character['id']}.png"
            kwargs["file"] = discord.File(image_path, filename=filename)
            embed.set_thumbnail(url=f"attachment://{filename}")
        await interaction.response.send_message(**kwargs)

    async def _send_section_pages(self, interaction, character, section, *, ephemeral=False):
        pages = self.section_embeds(character, section)
        view = CharacterView(self, character, interaction.user.id)
        view.section = section
        view.sync_section_controls()
        kwargs = {"embed": pages[0], "view": view, "ephemeral": ephemeral}
        if ephemeral:
            kwargs["delete_after"] = EPHEMERAL_DELETE_AFTER
        await interaction.response.send_message(**kwargs)
        for embed in pages[1:]:
            if ephemeral:
                await self._send_ephemeral_followup(interaction, embed=embed)
            else:
                await interaction.followup.send(embed=embed)

    async def _character_webhook(self, interaction):
        channel = interaction.channel
        webhook_channel = channel.parent if isinstance(channel, discord.Thread) else channel
        if interaction.guild is None or webhook_channel is None or not hasattr(webhook_channel, "webhooks"):
            raise CharacterError("Character posts can only be sent in a Discord server channel.")

        bot_member = interaction.guild.me
        if bot_member is None or not webhook_channel.permissions_for(bot_member).manage_webhooks:
            raise CharacterError(
                "EyeBot needs the Manage Webhooks permission in this channel to post as a character."
            )

        bot_user_id = getattr(getattr(self.bot, "user", None), "id", None)
        webhooks = await webhook_channel.webhooks()
        webhook = next(
            (
                item
                for item in webhooks
                if item.name == CHARACTER_WEBHOOK_NAME
                and item.token
                and getattr(getattr(item, "user", None), "id", None) == bot_user_id
            ),
            None,
        )
        if webhook is None:
            webhook = await webhook_channel.create_webhook(
                name=CHARACTER_WEBHOOK_NAME,
                reason="EyeBot character posts",
            )
        return webhook, channel if isinstance(channel, discord.Thread) else None

    @app_commands.command(name="list", description="List characters linked to your Discord account")
    async def list_characters(self, interaction: discord.Interaction):
        characters = self.service.list(interaction.user.id)
        if not characters:
            return await interaction.response.send_message(
                "You have no imported characters. Use `/character import-pdf`, "
                "`/character import-json`, or `/character create`.",
                ephemeral=True,
                delete_after=EPHEMERAL_DELETE_AFTER,
            )
        lines = [
            f"• **{_display_name(item)}** — level {item['level']} {_class_summary(item)}"
            for item in characters
        ]
        await interaction.response.send_message(
            "\n".join(lines)[:4000],
            ephemeral=True,
            delete_after=EPHEMERAL_DELETE_AFTER,
        )

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
            delete_after=EPHEMERAL_DELETE_AFTER,
        )

    @app_commands.command(name="show", description="Display a section from one of your character sheets")
    @app_commands.autocomplete(character=character_autocomplete)
    @app_commands.choices(section=SHOW_SECTION_CHOICES)
    async def show(
        self,
        interaction: discord.Interaction,
        character: str,
        section: app_commands.Choice[str] | None = None,
    ):
        selected = self.service.resolve(interaction.user.id, character)
        selected_section = section.value if section else "summary"
        if selected_section == "summary":
            await self._send_sheet(interaction, selected, ephemeral=True)
        else:
            await self._send_section_pages(
                interaction, selected, selected_section, ephemeral=True
            )

    @app_commands.command(name="show-all", description="Post every section of one of your character sheets")
    @app_commands.autocomplete(character=character_autocomplete)
    async def show_all(self, interaction: discord.Interaction, character: str):
        selected = self.service.resolve(interaction.user.id, character)
        await self._send_sheet(interaction, selected, with_view=False)
        for section in SHOW_ALL_SECTION_ORDER:
            for embed in self.section_embeds(selected, section):
                await interaction.followup.send(embed=embed)

    @app_commands.command(name="import-pdf", description="Import your editable D&D character-sheet PDF")
    async def import_pdf(self, interaction: discord.Interaction, file: discord.Attachment):
        await interaction.response.defer(ephemeral=True, thinking=True)
        data = await self._read_import_attachment(file)
        character = self.service.import_pdf(interaction.user.id, data)
        await self._send_ephemeral_followup(
            interaction,
            f"✅ Imported **{character['name']}** from PDF.",
        )

    @app_commands.command(name="import-json", description="Import an EyeBot or manually supplied character JSON file")
    async def import_json(self, interaction: discord.Interaction, file: discord.Attachment):
        await interaction.response.defer(ephemeral=True, thinking=True)
        data = await self._read_import_attachment(file)
        character = self.service.import_json(interaction.user.id, data)
        await self._send_ephemeral_followup(
            interaction,
            f"✅ Imported **{character['name']}** from JSON.",
        )

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
        await interaction.response.send_message(
            f"✅ Created **{character['name']}**.",
            ephemeral=True,
            delete_after=EPHEMERAL_DELETE_AFTER,
        )

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
        await self._send_ephemeral_followup(
            interaction,
            f"✅ Refreshed **{refreshed['name']}**.",
        )

    @app_commands.command(name="nickname", description="Set or clear a character nickname")
    @app_commands.autocomplete(character=character_autocomplete)
    async def nickname(self, interaction: discord.Interaction, character: str, nickname: app_commands.Range[str, 0, 100] = ""):
        updated = self.service.update(interaction.user.id, character, nickname=nickname)
        message = f"✅ Nickname updated for **{updated['name']}**." if nickname else f"✅ Nickname cleared for **{updated['name']}**."
        await interaction.response.send_message(
            message,
            ephemeral=True,
            delete_after=EPHEMERAL_DELETE_AFTER,
        )

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
            await image.read(use_cached=False),
            content_type,
        )
        await self._send_ephemeral_followup(
            interaction,
            f"✅ Updated the portrait for **{updated['name']}**.",
        )

    @app_commands.command(name="post", description="Post in character using the character's name and portrait")
    @app_commands.autocomplete(character=character_autocomplete)
    async def post(self, interaction: discord.Interaction, character: str, text: app_commands.Range[str, 1, 1800]):
        await interaction.response.defer(ephemeral=True, thinking=True)
        selected = self.service.resolve(interaction.user.id, character)
        nickname = str(selected.get("nickname") or "").strip()
        username = str(selected["name"])
        if nickname:
            username += f" ({nickname})"
        avatar_url = str(selected.get("avatar_url") or "").strip()
        webhook, thread = await self._character_webhook(interaction)
        kwargs = {
            "content": text,
            "username": username[:80],
            "allowed_mentions": discord.AllowedMentions.none(),
            "wait": True,
        }
        if avatar_url.startswith("https://"):
            kwargs["avatar_url"] = avatar_url
        if thread is not None:
            kwargs["thread"] = thread
        await webhook.send(**kwargs)
        await self._send_ephemeral_followup(
            interaction,
            f"✅ Posted as **{discord.utils.escape_markdown(username)}**.",
        )

    @app_commands.command(name="download", description="Download one of your characters as EyeBot JSON")
    @app_commands.autocomplete(character=character_autocomplete)
    async def download(self, interaction: discord.Interaction, character: str):
        selected = self.service.resolve(interaction.user.id, character)
        file = discord.File(
            io.BytesIO(self.service.export(interaction.user.id, character)),
            filename=f"{re.sub(r'[^a-zA-Z0-9_-]+', '-', selected['name']).strip('-') or 'character'}.json",
        )
        await interaction.response.send_message(
            file=file,
            ephemeral=True,
            delete_after=EPHEMERAL_DELETE_AFTER,
        )

    @app_commands.command(name="delete", description="Delete one of your characters after confirmation")
    @app_commands.autocomplete(character=character_autocomplete)
    async def delete(self, interaction: discord.Interaction, character: str):
        selected = self.service.resolve(interaction.user.id, character)
        await interaction.response.send_message(
            f"Delete **{selected['name']}** permanently?",
            view=DeleteCharacterView(self, interaction.user.id, selected),
            ephemeral=True,
            delete_after=EPHEMERAL_DELETE_AFTER,
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

    def _damage_roll_embed(self, character, action_name, expression, damage_type=""):
        total, _ = self._roller().roll_full_expression(expression)
        type_text = f" {damage_type}" if damage_type else ""
        return discord.Embed(
            title=f"🎲 {_display_name(character, markdown=False)} — {action_name} Damage",
            description=f"**Roll:** `{expression}`{type_text}\n## Total: {total}{type_text}",
            color=0x7A2E8E,
        )

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
            damage_types = item.get("damage_types", ())
            damage_type = damage_types[index - 1] if index <= len(damage_types) else ""
            suffix = f" {damage_type}" if damage_type else ""
            embed.add_field(name=f"Damage {index}", value=f"`{expression}` → **{total}**{suffix}", inline=True)
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
        await interaction.response.send_message(
            f"✅ Set {name} to {signed(value)} for **{selected['name']}**.",
            ephemeral=True,
            delete_after=EPHEMERAL_DELETE_AFTER,
        )

    @app_commands.command(name="set", description="Edit a character section value")
    @app_commands.autocomplete(
        character=character_autocomplete,
        subsection=subsection_autocomplete,
        item=section_item_autocomplete,
    )
    @app_commands.choices(section=SECTION_CHOICES)
    async def set_section_value(
        self,
        interaction: discord.Interaction,
        character: str,
        section: app_commands.Choice[str],
        subsection: app_commands.Range[str, 1, 100],
        value: app_commands.Range[str, 1, 2000],
        item: app_commands.Range[str, 0, 100] = "",
    ):
        selected = self.service.resolve(interaction.user.id, character)
        section_data = selected.get("sections", {}).get(section.value)
        if not isinstance(section_data, dict) or subsection not in section_data:
            raise CharacterError("Select an existing subsection for that character.")
        target = section_data[subsection]
        if isinstance(target, dict):
            if not item:
                raise CharacterError("Specify the characteristic or parameter to update.")
            target[item] = value
        elif isinstance(target, list):
            if not item:
                raise CharacterError("Specify the item or feature to update.")
            match = next(
                (
                    entry for entry in target
                    if isinstance(entry, dict)
                    and str(entry.get("name", "")).casefold() == item.casefold()
                ),
                None,
            )
            if match is not None:
                if section.value == "Features and Traits":
                    match["details"] = [value]
                else:
                    match["description"] = value
            else:
                index = next(
                    (i for i, entry in enumerate(target) if str(entry).casefold() == item.casefold()),
                    None,
                )
                if index is None:
                    raise CharacterError("That item is not recorded in the selected subsection.")
                target[index] = value
        else:
            section_data[subsection] = value
        self.service.save(interaction.user.id, selected, replace_selector=character)
        await interaction.response.send_message(
            f"✅ Updated **{subsection}** for **{selected['name']}**.",
            ephemeral=True,
            delete_after=EPHEMERAL_DELETE_AFTER,
        )

    @add.command(name="container", description="Add an equipment container to a character")
    @app_commands.autocomplete(character=character_autocomplete)
    async def add_container(
        self,
        interaction: discord.Interaction,
        character: str,
        name: app_commands.Range[str, 1, 100],
    ):
        selected = self.service.resolve(interaction.user.id, character)
        equipment = selected["sections"]["Equipment"]
        if any(existing.casefold() == name.casefold() for existing in equipment):
            raise CharacterError("That equipment container already exists.")
        equipment[name] = []
        self.service.save(interaction.user.id, selected, replace_selector=character)
        await interaction.response.send_message(
            f"✅ Added equipment container **{name}**.",
            ephemeral=True,
            delete_after=EPHEMERAL_DELETE_AFTER,
        )

    @add.command(name="item", description="Add an item to a character equipment container")
    @app_commands.autocomplete(character=character_autocomplete, container=container_autocomplete)
    async def add_item(
        self,
        interaction: discord.Interaction,
        character: str,
        container: app_commands.Range[str, 1, 100],
        item_name: app_commands.Range[str, 1, 100],
        quantity: app_commands.Range[int, 1, 10000] = 1,
        description: app_commands.Range[str, 0, 1000] = "",
    ):
        selected = self.service.resolve(interaction.user.id, character)
        equipment = selected["sections"]["Equipment"]
        selected_container = next(
            (name for name in equipment if name.casefold() == container.casefold()),
            None,
        )
        if selected_container is None:
            raise CharacterError("Select an existing equipment container.")
        if not isinstance(equipment[selected_container], list):
            raise CharacterError("The selected equipment container is invalid.")
        equipment[selected_container].append({
            "name": item_name,
            "quantity": quantity,
            "description": description,
        })
        self.service.save(interaction.user.id, selected, replace_selector=character)
        await interaction.response.send_message(
            f"✅ Added **{item_name} x {quantity}** to **{selected_container}**.",
            ephemeral=True,
            delete_after=EPHEMERAL_DELETE_AFTER,
        )

    @app_commands.command(name="action-add", description="Add or replace a character action")
    @app_commands.autocomplete(character=character_autocomplete)
    async def action_add(self, interaction: discord.Interaction, character: str, name: app_commands.Range[str, 1, 100], description: app_commands.Range[str, 0, 1000] = "", attack_bonus: app_commands.Range[int, -100, 100] | None = None, damage_rolls: app_commands.Range[str, 0, 200] = "", damage_type: app_commands.Range[str, 0, 50] = ""):
        selected = self.service.resolve(interaction.user.id, character)
        self._validate_damage_rolls(damage_rolls)
        selected["actions"] = [item for item in selected["actions"] if item["name"].casefold() != name.casefold()]
        rolls = [value for value in re.split(r"\s*(?:,|;)\s*", damage_rolls) if value]
        selected["actions"].append({"name": name, "description": description, "attack_bonus": attack_bonus, "damage_rolls": rolls, "damage_types": [damage_type] * len(rolls)})
        self.service.save(interaction.user.id, selected, replace_selector=character)
        await interaction.response.send_message(
            f"✅ Saved action **{name}**.",
            ephemeral=True,
            delete_after=EPHEMERAL_DELETE_AFTER,
        )

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
        await interaction.response.send_message(
            f"✅ Saved spell **{name}**.",
            ephemeral=True,
            delete_after=EPHEMERAL_DELETE_AFTER,
        )


async def setup(bot):
    settings = dict(getattr(bot, "config", {}).get("characters", {}) or {})
    if settings.get("enabled", True):
        await bot.add_cog(Character(bot))
