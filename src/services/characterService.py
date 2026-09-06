"""Owner-scoped character imports, validation, and atomic persistence."""

from __future__ import annotations

import io
import json
import math
import os
import re
import shutil
import tempfile
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
import pymupdf
from pypdf import PdfReader


ABILITY_NAMES = {
    "str": "Strength",
    "dex": "Dexterity",
    "con": "Constitution",
    "int": "Intelligence",
    "wis": "Wisdom",
    "cha": "Charisma",
}
SKILL_ABILITIES = {
    "acrobatics": "dex",
    "animal handling": "wis",
    "arcana": "int",
    "athletics": "str",
    "deception": "cha",
    "history": "int",
    "insight": "wis",
    "intimidation": "cha",
    "investigation": "int",
    "medicine": "wis",
    "nature": "int",
    "perception": "wis",
    "performance": "cha",
    "persuasion": "cha",
    "religion": "int",
    "sleight of hand": "dex",
    "stealth": "dex",
    "survival": "wis",
}
MAX_CHARACTERS_PER_USER = 50
MAX_IMPORT_BYTES = 10 * 1024 * 1024
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
MAX_TEXT = 20_000
MAX_LIST_ITEMS = 500
DICE_PATTERN = re.compile(r"^[0-9dD+\- ]{1,100}$")


class CharacterError(ValueError):
    """Safe character validation or persistence failure."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ability_modifier(score: int) -> int:
    return math.floor((int(score) - 10) / 2)


def proficiency_bonus(level: int) -> int:
    return 2 + (max(1, int(level)) - 1) // 4


def signed(value: int) -> str:
    return f"{int(value):+d}"


def character_template_json() -> bytes:
    """Return an importable, self-documenting character JSON template."""
    template = {
        "_instructions": {
            "general": (
                "Replace the example values, retain valid JSON syntax, and import this "
                "file with /character import-json. Fields beginning with an underscore "
                "are notes and are ignored by EyeBot."
            ),
            "classes": "Add one object per class. Each class level must be from 1 through 20.",
            "abilities": "Enter the six ability scores, each from 1 through 30.",
            "saving_throws": "Enter each complete saving-throw modifier, including proficiency.",
            "skills": "Enter each complete skill modifier. Unlisted skills default from their ability.",
            "combat": "speed is in feet; initiative is the total bonus; armor_class and max_hit_points are totals.",
            "actions": (
                "Each action may include description, attack_bonus, damage_rolls, save_ability, "
                "and save_dc. Damage rolls use bounded expressions such as 1d8+3."
            ),
            "spells": (
                "Spell level is 0 through 9. damage_rolls_by_level maps a character or slot "
                "level to a list of bounded dice expressions."
            ),
            "sections": "Add free-form JSON sections such as Inventory, Features, Traits, Notes, or Currencies.",
            "avatar_url": "Optional direct HTTPS portrait URL. You may instead use /character image after import.",
        },
        "name": "Example Character",
        "nickname": "",
        "classes": [{"name": "Fighter", "subclass": "Champion", "level": 1}],
        "abilities": {key: 10 for key in ABILITY_NAMES},
        "saving_throws": {key: 0 for key in ABILITY_NAMES},
        "skills": {key: 0 for key in SKILL_ABILITIES},
        "proficiency_bonus": 2,
        "speed": 30,
        "initiative": 0,
        "armor_class": 10,
        "max_hit_points": 10,
        "avatar_url": "",
        "actions": [],
        "spells": [],
        "sections": {
            "Inventory": [],
            "Features": [],
            "Traits": [],
            "Notes": "",
            "Currencies": {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0},
        },
        "_action_example": {
            "name": "Longsword",
            "description": "Melee weapon attack.",
            "attack_bonus": 5,
            "damage_rolls": ["1d8+3"],
            "save_ability": "",
            "save_dc": None,
        },
        "_spell_example": {
            "name": "Fire Bolt",
            "level": 0,
            "description": "A ranged spell attack.",
            "attack_bonus": 5,
            "save_ability": "",
            "save_dc": None,
            "damage_rolls": ["1d10"],
            "damage_rolls_by_level": {"5": ["2d10"], "11": ["3d10"], "17": ["4d10"]},
            "higher_levels": "The damage increases at the listed character levels.",
        },
    }
    return json.dumps(template, indent=2, ensure_ascii=False).encode("utf-8")


def _text(value, *, maximum=MAX_TEXT) -> str:
    selected = str(value or "").strip()
    return selected[:maximum]


def _integer(value, default=0, *, minimum=-1000, maximum=1000) -> int:
    try:
        selected = int(str(value).strip().replace("+", ""))
    except (TypeError, ValueError):
        selected = int(default)
    return max(minimum, min(maximum, selected))


def _slug(value: str) -> str:
    selected = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return (selected or "character")[:40]


def _classes(value, total_level=1) -> list[dict]:
    result = []
    if isinstance(value, list):
        for item in value[:20]:
            if not isinstance(item, dict):
                continue
            definition = item.get("definition") or {}
            subclass = item.get("subclassDefinition") or item.get("subclass") or {}
            result.append(
                {
                    "name": _text(item.get("name") or definition.get("name") or "Class", maximum=100),
                    "subclass": _text(
                        subclass.get("name") if isinstance(subclass, dict) else subclass,
                        maximum=100,
                    ),
                    "level": _integer(item.get("level"), 1, minimum=1, maximum=20),
                }
            )
    elif isinstance(value, str):
        for selected in re.split(r"\s*(?:/|,|\|)\s*", value):
            match = re.match(r"(.+?)\s+(\d{1,2})$", selected.strip())
            if match:
                result.append(
                    {
                        "name": _text(match.group(1), maximum=100),
                        "subclass": "",
                        "level": _integer(match.group(2), 1, minimum=1, maximum=20),
                    }
                )
            elif selected.strip():
                result.append(
                    {
                        "name": _text(selected, maximum=100),
                        "subclass": "",
                        "level": _integer(total_level, 1, minimum=1, maximum=20),
                    }
                )
    return result or [{"name": "Adventurer", "subclass": "", "level": max(1, total_level)}]


def _normalize_rolls(value) -> list[str]:
    if isinstance(value, str):
        values = re.split(r"\s*(?:,|;)\s*", value)
    elif isinstance(value, list):
        values = value
    else:
        values = []
    result = []
    for item in values[:10]:
        selected = _text(item, maximum=100).replace(" ", "")
        if selected and _valid_damage_expression(selected):
            result.append(selected.casefold())
    return result


def _valid_damage_expression(value: str) -> bool:
    if not DICE_PATTERN.fullmatch(value):
        return False
    tokens = re.findall(r"[+-]?[^+-]+", value)
    if not tokens or len(tokens) > 20:
        return False
    reconstructed = "".join(tokens)
    if reconstructed != value:
        return False
    for token in tokens:
        part = token.lstrip("+-")
        if part.isdecimal():
            if int(part) > 1_000_000:
                return False
            continue
        match = re.fullmatch(r"(\d*)[dD](\d+)", part)
        if not match:
            return False
        count = int(match.group(1) or 1)
        sides = int(match.group(2))
        if not 1 <= count <= 100 or not 2 <= sides <= 10_000:
            return False
    return True


def _normalize_actions(value) -> list[dict]:
    result = []
    for item in value if isinstance(value, list) else ():
        if not isinstance(item, dict) or not _text(item.get("name"), maximum=100):
            continue
        result.append(
            {
                "name": _text(item.get("name"), maximum=100),
                "description": _text(item.get("description") or item.get("snippet")),
                "attack_bonus": (
                    _integer(item.get("attack_bonus"), minimum=-100, maximum=100)
                    if item.get("attack_bonus") not in (None, "")
                    else None
                ),
                "damage_rolls": _normalize_rolls(
                    item.get("damage_rolls") or item.get("damage")
                ),
                "save_ability": _text(item.get("save_ability"), maximum=3).casefold(),
                "save_dc": (
                    _integer(item.get("save_dc"), minimum=1, maximum=100)
                    if item.get("save_dc") not in (None, "")
                    else None
                ),
            }
        )
        if len(result) >= MAX_LIST_ITEMS:
            break
    return result


def _normalize_spells(value) -> list[dict]:
    result = []
    for item in value if isinstance(value, list) else ():
        if not isinstance(item, dict):
            continue
        definition = item.get("definition") or item
        name = _text(definition.get("name"), maximum=100)
        if not name:
            continue
        raw_damage_by_level = (
            item.get("damage_rolls_by_level")
            or definition.get("damage_rolls_by_level")
            or {}
        )
        if not isinstance(raw_damage_by_level, dict):
            raw_damage_by_level = {}
        result.append(
            {
                "name": name,
                "level": _integer(definition.get("level"), 0, minimum=0, maximum=9),
                "description": _text(
                    definition.get("description") or definition.get("snippet")
                ),
                "attack_bonus": (
                    _integer(item.get("attack_bonus"), minimum=-100, maximum=100)
                    if item.get("attack_bonus") not in (None, "")
                    else None
                ),
                "save_ability": _text(
                    item.get("save_ability") or definition.get("save_ability"),
                    maximum=3,
                ).casefold(),
                "save_dc": (
                    _integer(item.get("save_dc"), minimum=1, maximum=100)
                    if item.get("save_dc") not in (None, "")
                    else None
                ),
                "damage_rolls": _normalize_rolls(
                    item.get("damage_rolls") or definition.get("damage_rolls")
                ),
                "damage_rolls_by_level": {
                    str(_integer(key, minimum=0, maximum=20)): _normalize_rolls(rolls)
                    for key, rolls in list(raw_damage_by_level.items())[:20]
                    if str(key).isdigit()
                },
                "higher_levels": _text(
                    definition.get("atHigherLevels")
                    or definition.get("higher_levels")
                ),
            }
        )
        if len(result) >= MAX_LIST_ITEMS:
            break
    return result


def _section_value(value, depth=0):
    """Bound imported supplementary data without discarding its structure."""
    if depth >= 4:
        return _text(value)
    if isinstance(value, dict):
        return {
            _text(key, maximum=100): _section_value(item, depth + 1)
            for key, item in list(value.items())[:100]
            if _text(key, maximum=100)
        }
    if isinstance(value, list):
        return [_section_value(item, depth + 1) for item in value[:200]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return _text(value) if isinstance(value, str) else value
    return _text(value)


def normalize_character(value: dict, owner_id: str, *, source="json") -> dict:
    """Normalize EyeBot or manually supplied D&D-like JSON."""
    if not isinstance(value, dict):
        raise CharacterError("The character JSON must contain an object.")
    payload = value.get("data") if isinstance(value.get("data"), dict) else value
    name = _text(payload.get("name") or payload.get("character_name"), maximum=100)
    if not name:
        raise CharacterError("The imported character does not contain a name.")

    raw_classes = payload.get("classes") or payload.get("class") or payload.get("class_name")
    stated_level = _integer(payload.get("level"), 1, minimum=1, maximum=20)
    classes = _classes(raw_classes, stated_level)
    level = max(1, min(20, sum(item["level"] for item in classes)))

    raw_abilities = payload.get("abilities") or payload.get("stats") or {}
    abilities = {}
    for index, abbreviation in enumerate(ABILITY_NAMES, start=1):
        selected = None
        if isinstance(raw_abilities, dict):
            selected = (
                raw_abilities.get(abbreviation)
                or raw_abilities.get(ABILITY_NAMES[abbreviation])
                or raw_abilities.get(ABILITY_NAMES[abbreviation].casefold())
            )
        elif isinstance(raw_abilities, list):
            match = next(
                (
                    item for item in raw_abilities
                    if isinstance(item, dict)
                    and (_integer(item.get("id"), -1) == index)
                ),
                None,
            )
            selected = match.get("value") if match else None
        if isinstance(selected, dict):
            selected = selected.get("score") or selected.get("value")
        abilities[abbreviation] = _integer(selected, 10, minimum=1, maximum=30)

    proficiency = _integer(
        payload.get("proficiency_bonus"),
        proficiency_bonus(level),
        minimum=0,
        maximum=20,
    )
    saving_throws = {}
    raw_saves = payload.get("saving_throws") or payload.get("saves") or {}
    for abbreviation in ABILITY_NAMES:
        saving_throws[abbreviation] = _integer(
            raw_saves.get(abbreviation) if isinstance(raw_saves, dict) else None,
            ability_modifier(abilities[abbreviation]),
            minimum=-100,
            maximum=100,
        )
    skills = {}
    raw_skills = payload.get("skills") or {}
    for skill, ability in SKILL_ABILITIES.items():
        selected = raw_skills.get(skill) if isinstance(raw_skills, dict) else None
        skills[skill] = _integer(
            selected,
            ability_modifier(abilities[ability]),
            minimum=-100,
            maximum=100,
        )

    actions = payload.get("actions") or []
    if isinstance(actions, dict):
        actions = [item for items in actions.values() if isinstance(items, list) for item in items]
    actions = list(actions) + list(payload.get("customActions") or [])
    spells = payload.get("spells") or []
    if isinstance(spells, dict):
        spells = [item for items in spells.values() if isinstance(items, list) for item in items]
    for class_spell in payload.get("classSpells") or []:
        if isinstance(class_spell, dict):
            spells.extend(class_spell.get("spells") or [])

    now = utc_now()
    identifier = _text(payload.get("id"), maximum=80)
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", identifier):
        identifier = f"{_slug(name)}-{uuid.uuid4().hex[:8]}"
    sections = (
        deepcopy(payload.get("sections"))
        if isinstance(payload.get("sections"), dict)
        else {}
    )
    supplementary = {
        "Overview": {
            "species": payload.get("species") or payload.get("race"),
            "background": payload.get("background"),
            "alignment": payload.get("alignment"),
            "experience": payload.get("experience") or payload.get("currentXp"),
            "inspiration": payload.get("inspiration"),
        },
        "Inventory": payload.get("inventory"),
        "Features": payload.get("features") or payload.get("feats"),
        "Traits": payload.get("traits"),
        "Notes": payload.get("notes") or payload.get("backstory"),
        "Currencies": payload.get("currencies"),
    }
    for section_name, section_value in supplementary.items():
        if section_name not in sections and section_value not in (None, {}, [], ""):
            if isinstance(section_value, dict):
                section_value = {
                    key: item for key, item in section_value.items()
                    if item not in (None, {}, [], "")
                }
            if section_value not in (None, {}, [], ""):
                sections[section_name] = section_value
    return {
        "schema_version": 1,
        "id": identifier,
        "owner_id": str(owner_id),
        "name": name,
        "nickname": _text(payload.get("nickname"), maximum=100),
        "source": _text(payload.get("source") or source, maximum=50),
        "source_reference": _text(payload.get("source_reference"), maximum=200),
        "avatar_url": _text(payload.get("avatar_url") or payload.get("avatarUrl"), maximum=1000),
        "image_path": "",
        "classes": classes,
        "level": level,
        "abilities": abilities,
        "saving_throws": saving_throws,
        "skills": skills,
        "proficiency_bonus": proficiency,
        "speed": _integer(payload.get("speed"), 30, minimum=0, maximum=1000),
        "initiative": _integer(
            payload.get("initiative"),
            ability_modifier(abilities["dex"]),
            minimum=-100,
            maximum=100,
        ),
        "armor_class": _integer(
            payload.get("armor_class") or payload.get("armorClass"),
            10 + ability_modifier(abilities["dex"]),
            minimum=0,
            maximum=100,
        ),
        "max_hit_points": _integer(
            payload.get("max_hit_points") or payload.get("maxHitPoints") or payload.get("baseHitPoints"),
            max(1, level * (6 + ability_modifier(abilities["con"]))),
            minimum=1,
            maximum=100_000,
        ),
        "actions": _normalize_actions(actions),
        "spells": _normalize_spells(spells),
        "sections": {
            _text(key, maximum=100): _section_value(item)
            for key, item in list(sections.items())[:25]
            if _text(key, maximum=100)
        },
        "created_at": _text(payload.get("created_at"), maximum=50) or now,
        "updated_at": now,
    }


PDF_ALIASES = {
    "name": ("CharacterName", "Character Name", "character_name"),
    "class": ("ClassLevel", "Class & Level", "ClassLevel1", "class"),
    "level": ("Level", "CharacterLevel", "level"),
    "str": ("STR", "Strength", "strength"),
    "dex": ("DEX", "Dexterity", "dexterity"),
    "con": ("CON", "Constitution", "constitution"),
    "int": ("INT", "Intelligence", "intelligence"),
    "wis": ("WIS", "Wisdom", "wisdom"),
    "cha": ("CHA", "Charisma", "charisma"),
    "proficiency_bonus": ("ProfBonus", "Proficiency Bonus", "proficiency"),
    "speed": ("Speed", "speed"),
    "initiative": ("Initiative", "initiative"),
    "armor_class": ("AC", "Armor Class", "armor_class"),
    "max_hit_points": ("HPMax", "Max HP", "Hit Point Maximum", "max_hp"),
}

LEGAL_BOILERPLATE_PATTERNS = (
    re.compile(
        r"(?:™|\bTM\b|©|\(c\)|\bcopyright\b).*?"
        r"(?:Wizards of the Coast|D&D Beyond)",
        re.I,
    ),
    re.compile(
        r"(?:Wizards of the Coast|D&D Beyond).*?"
        r"(?:™|\bTM\b|©|\(c\)|\bcopyright\b|all rights reserved)",
        re.I,
    ),
    re.compile(r"\ball rights reserved\b", re.I),
    re.compile(
        r"\bpermission is granted to photo\s*copy this document for personal use\b",
        re.I,
    ),
)


def _strip_import_legal_boilerplate(value):
    """Remove publisher legal footer lines without altering character content."""
    retained = []
    for line in str(value or "").splitlines():
        normalized = " ".join(line.split())
        if normalized and any(pattern.search(normalized) for pattern in LEGAL_BOILERPLATE_PATTERNS):
            continue
        retained.append(line)
    return "\n".join(retained).strip()


def _pdf_field_value(fields, aliases):
    folded = {str(key).casefold(): value for key, value in fields.items()}
    for alias in aliases:
        value = folded.get(alias.casefold())
        if isinstance(value, dict):
            value = value.get("/V") or value.get("value")
        if value not in (None, ""):
            return str(value).lstrip("/").strip()
    return ""


def _flat_block(block):
    return {
        "x0": float(block[0]),
        "y0": float(block[1]),
        "x1": float(block[2]),
        "y1": float(block[3]),
        "text": " | ".join(str(block[4]).strip().splitlines()),
    }


def _flat_value_left_of(blocks, label):
    anchors = [
        item for item in blocks
        if item["x0"] >= 100 and item["text"].casefold() == label.casefold()
    ]
    if not anchors:
        return ""
    anchor = anchors[0]
    candidates = [
        item for item in blocks
        if 90 <= item["x0"] < anchor["x0"]
        and abs(item["y0"] - anchor["y0"]) <= 3
        and re.search(r"[+-]?\d+", item["text"])
    ]
    if not candidates:
        return ""
    return max(candidates, key=lambda item: item["x0"])["text"]


def _first_flat_block(blocks, *, x0=None, x1=None, y0=None, y1=None, pattern=None):
    for item in blocks:
        if x0 is not None and item["x0"] < x0:
            continue
        if x1 is not None and item["x0"] > x1:
            continue
        if y0 is not None and item["y0"] < y0:
            continue
        if y1 is not None and item["y0"] > y1:
            continue
        if pattern and not re.search(pattern, item["text"], re.I):
            continue
        return item["text"]
    return ""


def _flat_number(value, default=""):
    match = re.search(r"[+-]?\d+", str(value or ""))
    return match.group(0) if match else default


def _flattened_pdf_payload(pages):
    """Map positioned text from a flattened D&D Beyond PDF to EyeBot data."""
    if not pages:
        return None
    first = pages[0]
    blocks = first["blocks"]
    name = _first_flat_block(blocks, x1=220, y0=40, y1=90)
    class_line = _first_flat_block(blocks, x0=220, y0=40, y1=76, pattern=r"\d")
    if not name or not class_line:
        return None

    class_parts = [part.strip() for part in class_line.split("|") if part.strip()]
    class_value = class_parts[0]
    class_match = re.match(r"(.+?)\s+(\d{1,2})$", class_value)
    if not class_match:
        return None
    class_name, level = class_match.group(1).strip(), int(class_match.group(2))

    identity = _first_flat_block(blocks, x0=220, y0=76, y1=100)
    identity_parts = [part.strip() for part in identity.split("|") if part.strip()]
    species = identity_parts[0] if identity_parts else ""
    background = identity_parts[1] if len(identity_parts) > 1 else ""

    ability_labels = list(ABILITY_NAMES)
    score_blocks = [
        item for item in blocks
        if item["x0"] < 85 and 145 <= item["y0"] <= 575
        and re.fullmatch(r"\d{1,2}", item["text"])
    ]
    score_blocks.sort(key=lambda item: item["y0"])
    abilities = {
        ability: _flat_number(score_blocks[index]["text"], "10")
        if index < len(score_blocks) else 10
        for index, ability in enumerate(ability_labels)
    }
    saving_throws = {
        ability: _flat_number(_flat_value_left_of(blocks, full_name), "")
        for ability, full_name in ABILITY_NAMES.items()
    }
    skills = {
        skill: _flat_number(_flat_value_left_of(blocks, skill.title()), "")
        for skill in SKILL_ABILITIES
    }

    combat = _first_flat_block(
        blocks, x0=200, x1=400, y0=140, y1=180, pattern=r"[+-]?\d"
    )
    combat_values = re.findall(r"[+-]?\d+", combat)
    hit_points = _first_flat_block(blocks, x0=420, y0=145, y1=185)
    proficiency = _first_flat_block(blocks, x0=200, x1=280, y0=300, y1=335)
    speed = _first_flat_block(blocks, x0=200, x1=340, y0=375, y1=415)

    actions = []
    for item in blocks:
        if item["x0"] < 200 or item["y0"] < 620:
            continue
        parts = [part.strip() for part in item["text"].split("|") if part.strip()]
        if len(parts) < 2 or not re.fullmatch(r"[+-]\d+", parts[1]):
            continue
        description = " | ".join(parts[2:])
        rolls = [roll.lstrip("+") for roll in re.findall(
            r"(?<![\w])\+?\d*d\d+(?:[+-]\d+)?", description, re.I
        )]
        actions.append({
            "name": parts[0],
            "description": description,
            "attack_bonus": parts[1],
            "damage_rolls": rolls,
        })

    spells = []
    spell_level = 0
    seen_spells = set()
    for page in pages[4:]:
        for item in sorted(page["blocks"], key=lambda value: (value["y0"], value["x0"])):
            text = item["text"]
            heading = re.search(r"===\s*(CANTRIPS|\d+(?:st|nd|rd|th) LEVEL)\s*===", text, re.I)
            if heading:
                spell_level = 0 if heading.group(1).casefold() == "cantrips" else int(
                    re.search(r"\d+", heading.group(1)).group(0)
                )
                continue
            match = re.match(r"([OP])\s+(.+?)\s+\|\s+([^|]+)", text)
            if not match:
                continue
            prepared, spell_name, source = match.groups()
            spell_name = re.sub(r"\s+\[R\]$", "", spell_name).strip()
            identity_key = (spell_name.casefold(), spell_level)
            if identity_key in seen_spells:
                continue
            seen_spells.add(identity_key)
            save = re.search(r"\b(STR|DEX|CON|INT|WIS|CHA)\s+(\d{1,2})\b", text)
            attack = re.search(r"(?<![\w/])\+(\d{1,2})(?!\w)", text)
            spells.append({
                "name": spell_name,
                "level": spell_level,
                "description": (
                    f"Flattened PDF listing. Source: {source.strip()}. "
                    f"Prepared on export: {'yes' if prepared == 'P' else 'no'}. "
                    f"Details: {text}"
                ),
                "attack_bonus": attack.group(1) if attack else None,
                "save_ability": save.group(1).casefold() if save else "",
                "save_dc": save.group(2) if save else None,
                "damage_rolls": [],
            })

    subclass = ""
    if len(pages) > 1:
        subclass_matches = re.findall(
            r"\b([A-Za-z][A-Za-z '-]+ Domain)\b", pages[1]["text"]
        )
        subclass = next(
            (value.strip() for value in subclass_matches if value.casefold() != "divine domain"),
            "",
        )
    section_names = [
        "Character Summary", "Features and Equipment", "Additional Equipment",
        "Background and Notes", "Spells - Cantrips and Level 1",
        "Spells - Level 2", "Spells - Levels 2 and 3", "Spells - Levels 3 and 4",
        "Spells - Levels 4 and 5", "Spells - Level 5",
    ]
    sections = {
        section_names[index] if index < len(section_names) else f"PDF Page {index + 1}": _strip_import_legal_boilerplate(page["text"])
        for index, page in enumerate(pages)
        if _strip_import_legal_boilerplate(page["text"])
    }
    return {
        "name": name,
        "classes": [{"name": class_name, "subclass": subclass, "level": level}],
        "abilities": abilities,
        "saving_throws": saving_throws,
        "skills": skills,
        "proficiency_bonus": _flat_number(proficiency, proficiency_bonus(level)),
        "speed": _flat_number(speed, 30),
        "initiative": combat_values[0] if combat_values else ability_modifier(int(abilities["dex"])),
        "armor_class": combat_values[1] if len(combat_values) > 1 else 10,
        "max_hit_points": _flat_number(hit_points, 1),
        "species": species,
        "background": background,
        "actions": actions,
        "spells": spells,
        "sections": sections,
        "source": "pdf-flat",
    }


def _extract_flattened_pdf(data):
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
        pages = []
        for page in document:
            page_text = _strip_import_legal_boilerplate(page.get_text("text") or "")
            pages.append({
                "text": page_text,
                "blocks": [
                    _flat_block((*block[:4], cleaned, *block[5:]))
                    for block in page.get_text("blocks")
                    if (cleaned := _strip_import_legal_boilerplate(block[4]))
                ],
            })
        document.close()
        return _flattened_pdf_payload(pages)
    except Exception:
        return None


def character_from_pdf(data: bytes, owner_id: str) -> dict:
    if not data.startswith(b"%PDF"):
        raise CharacterError("The uploaded file is not a valid PDF document.")
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        if reader.is_encrypted and reader.decrypt("") == 0:
            raise CharacterError("Encrypted character PDFs are not supported.")
        fields = reader.get_fields() or {}
        page_text = _strip_import_legal_boilerplate(
            "\n".join((page.extract_text() or "") for page in reader.pages)
        )
    except CharacterError:
        raise
    except Exception as error:
        raise CharacterError("EyeBot could not read the uploaded character PDF.") from error

    extracted = {
        key: _pdf_field_value(fields, aliases)
        for key, aliases in PDF_ALIASES.items()
    }
    if not fields:
        flattened = _extract_flattened_pdf(data)
        if flattened:
            return normalize_character(flattened, owner_id, source="pdf-flat")
    if not extracted["name"]:
        match = re.search(r"(?:Character Name|Name)\s*[:\n]\s*([^\n]{1,100})", page_text, re.I)
        if match:
            extracted["name"] = match.group(1).strip()
    if not extracted["name"]:
        raise CharacterError(
            "EyeBot could not locate the character name in this PDF. Use an "
            "editable D&D character-sheet PDF or import EyeBot JSON instead."
        )

    extracted["classes"] = extracted.pop("class") or "Adventurer 1"
    extracted["abilities"] = {
        ability: extracted.pop(ability) or 10 for ability in ABILITY_NAMES
    }
    extracted["source"] = "pdf"
    extracted["sections"] = {
        "PDF character sheet": page_text[:MAX_TEXT]
    }
    character = normalize_character(extracted, owner_id, source="pdf")

    for skill in SKILL_ABILITIES:
        selected = _pdf_field_value(fields, (skill, skill.title(), skill.replace(" ", "")))
        if selected:
            character["skills"][skill] = _integer(
                selected,
                character["skills"][skill],
                minimum=-100,
                maximum=100,
            )
    for ability, full_name in ABILITY_NAMES.items():
        selected = _pdf_field_value(
            fields,
            (f"{ability.upper()}save", f"{full_name} Save", f"{full_name}Save"),
        )
        if selected:
            character["saving_throws"][ability] = _integer(
                selected,
                character["saving_throws"][ability],
                minimum=-100,
                maximum=100,
            )

    actions = []
    for index in range(1, 6):
        name = _pdf_field_value(fields, (f"Wpn Name {index}", f"WpnName{index}", f"Attack {index}"))
        if not name:
            continue
        actions.append(
            {
                "name": name,
                "description": "Imported from the character-sheet attack table.",
                "attack_bonus": _pdf_field_value(fields, (f"Wpn{index} AtkBonus", f"WpnAtkBonus{index}")),
                "damage_rolls": _pdf_field_value(fields, (f"Wpn{index} Damage", f"WpnDamage{index}")),
            }
        )
    character["actions"] = _normalize_actions(actions)
    return character


class CharacterService:
    """Store validated character records in private per-owner JSON files."""

    def __init__(self, root, settings=None, logger=None):
        self.root = Path(root)
        self.settings = dict(settings or {})
        self.logger = logger
        self._lock = threading.RLock()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "images").mkdir(exist_ok=True)
        for path in (self.root, self.root / "images"):
            try:
                path.chmod(0o700)
            except OSError:
                pass

    @staticmethod
    def validate_owner(owner_id) -> str:
        selected = str(owner_id)
        if not selected.isdecimal() or not 1 <= len(selected) <= 20:
            raise CharacterError("The Discord user ID is invalid.")
        return selected

    def path(self, owner_id) -> Path:
        return self.root / f"{self.validate_owner(owner_id)}.json"

    def _read(self, owner_id) -> dict:
        path = self.path(owner_id)
        if not path.exists():
            return {"schema_version": 1, "characters": {}}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or not isinstance(value.get("characters"), dict):
                raise ValueError("invalid character store")
            return value
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            backup = path.with_suffix(".json.bak")
            try:
                value = json.loads(backup.read_text(encoding="utf-8"))
                if not isinstance(value.get("characters"), dict):
                    raise ValueError("invalid backup")
                self._write(owner_id, value, create_backup=False)
                return value
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError, AttributeError):
                raise CharacterError("Your character store could not be loaded.") from error

    def _write(self, owner_id, value, *, create_backup=True):
        path = self.path(owner_id)
        if create_backup and path.is_file():
            shutil.copy2(path, path.with_suffix(".json.bak"))
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.root,
            prefix=f".{path.stem}-",
            suffix=".tmp",
            text=True,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as destination:
                json.dump(value, destination, indent=2, sort_keys=True)
                destination.write("\n")
                destination.flush()
                os.fsync(destination.fileno())
            temporary.chmod(0o600)
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def list(self, owner_id) -> list[dict]:
        with self._lock:
            return sorted(
                (deepcopy(item) for item in self._read(owner_id)["characters"].values()),
                key=lambda item: item["name"].casefold(),
            )

    def resolve(self, owner_id, selector) -> dict:
        selected = _text(selector, maximum=100).casefold()
        if not selected:
            raise CharacterError("Select one of your imported characters.")
        matches = [
            item for item in self.list(owner_id)
            if selected in {
                str(item.get("id", "")).casefold(),
                str(item.get("name", "")).casefold(),
                str(item.get("nickname", "")).casefold(),
            }
        ]
        if not matches:
            raise CharacterError("That character is not linked to your Discord account.")
        if len(matches) > 1:
            raise CharacterError("That character name or nickname is ambiguous.")
        return matches[0]

    def save(self, owner_id, character, *, replace_selector=None) -> dict:
        owner = self.validate_owner(owner_id)
        normalized = normalize_character(character, owner, source=character.get("source", "manual"))
        with self._lock:
            store = self._read(owner)
            if replace_selector:
                previous = self.resolve(owner, replace_selector)
                normalized["id"] = previous["id"]
                normalized["created_at"] = previous.get("created_at", normalized["created_at"])
                normalized["nickname"] = previous.get("nickname", "")
                normalized["image_path"] = previous.get("image_path", "")
                store["characters"].pop(previous["id"], None)
            elif len(store["characters"]) >= int(
                self.settings.get("max_characters_per_user", MAX_CHARACTERS_PER_USER)
            ):
                raise CharacterError("You have reached the character storage limit.")
            duplicate = next(
                (
                    item for item in store["characters"].values()
                    if item["name"].casefold() == normalized["name"].casefold()
                    and item["id"] != normalized["id"]
                ),
                None,
            )
            if duplicate:
                raise CharacterError("You already have a character with that name.")
            store["characters"][normalized["id"]] = normalized
            self._write(owner, store)
            return deepcopy(normalized)

    def import_json(self, owner_id, data: bytes, *, replace_selector=None) -> dict:
        if len(data) > int(self.settings.get("max_import_bytes", MAX_IMPORT_BYTES)):
            raise CharacterError("The character JSON exceeds the import size limit.")
        try:
            value = json.loads(data.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CharacterError("The uploaded character JSON is invalid.") from error
        character = normalize_character(value, str(owner_id), source="json")
        return self.save(owner_id, character, replace_selector=replace_selector)

    def import_pdf(self, owner_id, data: bytes, *, replace_selector=None) -> dict:
        if len(data) > int(self.settings.get("max_import_bytes", MAX_IMPORT_BYTES)):
            raise CharacterError("The character PDF exceeds the import size limit.")
        character = character_from_pdf(data, str(owner_id))
        return self.save(owner_id, character, replace_selector=replace_selector)

    def update(self, owner_id, selector, **changes) -> dict:
        owner = self.validate_owner(owner_id)
        with self._lock:
            store = self._read(owner)
            character = self.resolve(owner, selector)
            stored = store["characters"][character["id"]]
            for key, value in changes.items():
                if key == "nickname":
                    stored[key] = _text(value, maximum=100)
                elif key == "image_path":
                    stored[key] = _text(value, maximum=1000)
            stored["updated_at"] = utc_now()
            self._write(owner, store)
            return deepcopy(stored)

    def delete(self, owner_id, selector) -> dict:
        owner = self.validate_owner(owner_id)
        with self._lock:
            store = self._read(owner)
            character = self.resolve(owner, selector)
            removed = store["characters"].pop(character["id"])
            self._write(owner, store)
        image_path = removed.get("image_path")
        if image_path:
            try:
                Path(image_path).unlink(missing_ok=True)
            except OSError:
                pass
        return deepcopy(removed)

    def export(self, owner_id, selector) -> bytes:
        character = self.resolve(owner_id, selector)
        exported = deepcopy(character)
        exported["image_path"] = ""
        return (json.dumps(exported, indent=2, sort_keys=True) + "\n").encode("utf-8")

    def store_image(self, owner_id, selector, data: bytes, content_type: str) -> dict:
        maximum = int(self.settings.get("max_image_bytes", MAX_IMAGE_BYTES))
        if not data or len(data) > maximum:
            raise CharacterError(f"Character images must be no larger than {maximum:,} bytes.")
        allowed = {"image/png", "image/jpeg", "image/webp"}
        if str(content_type or "").split(";", 1)[0].casefold() not in allowed:
            raise CharacterError("Character images must be PNG, JPEG, or WebP files.")
        try:
            image = Image.open(io.BytesIO(data))
            image.load()
        except (UnidentifiedImageError, OSError) as error:
            raise CharacterError("The uploaded character image is invalid.") from error
        if image.width * image.height > int(
            self.settings.get("max_image_pixels", MAX_IMAGE_PIXELS)
        ):
            raise CharacterError("The character image contains too many pixels.")
        image = ImageOps.exif_transpose(image).convert("RGBA")
        maximum_dimension = int(self.settings.get("image_max_dimension", 1024))
        image.thumbnail((maximum_dimension, maximum_dimension), Image.Resampling.LANCZOS)
        character = self.resolve(owner_id, selector)
        directory = self.root / "images" / self.validate_owner(owner_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{character['id']}.png"
        image.save(path, format="PNG", optimize=True)
        try:
            path.chmod(0o600)
        except OSError:
            pass
        return self.update(owner_id, selector, image_path=str(path))
