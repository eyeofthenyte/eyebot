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
        "schema_version": 2,
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
            "spellcasting": "ability uses STR, DEX, CON, INT, WIS, or CHA; save_dc and attack_bonus are totals.",
            "proficiencies": "Add each proficiency with a name and type, such as Armor, Weapons, Language, or Tool.",
            "actions": (
                "Each action may include description, attack_bonus, damage_rolls, damage_types, "
                "save_ability, and save_dc. Damage rolls use bounded expressions such as "
                "1d8+3. damage_types is a parallel list such as ['Slashing']."
            ),
            "spells": (
                "Spell level is 0 through 9. damage_rolls_by_level maps a character or slot "
                "level to a list of bounded dice expressions."
            ),
            "sections": (
                "Keep the four named sections and their documented subsections. "
                "Equipment containers may be added as new keys alongside Personal "
                "Belongings, Attuned Items, and Other."
            ),
            "editing": (
                "Use /character set to edit section values, /character add container "
                "to create an equipment container, and /character add item to add equipment."
            ),
            "avatar_url": "Optional direct HTTPS avatar URL. You may instead use /character add avatar after import.",
            "images": "Gallery image paths are managed by /character add, edit, and remove image and are not portable in JSON exports.",
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
        "spellcasting": {"ability": "cha", "save_dc": 10, "attack_bonus": 2},
        "proficiencies": [
            {"name": "Light", "type": "Armor"},
            {"name": "Common", "type": "Language"},
        ],
        "avatar_url": "",
        "images": [],
        "actions": [],
        "spells": [],
        "sections": {
            "Equipment": {
                "Backpack": [{
                    "name": "Rope, Hempen (50 feet)",
                    "quantity": 1,
                    "gp_value": 1,
                    "description": "Optional item details.",
                }],
                "Personal Belongings": [],
                "Attuned Items": [],
                "Other": [],
            },
            "Features and Traits": {
                "Class Features": [
                    {"name": "Second Wind", "details": ["Source: PHB 72", "Recover hit points as a bonus action."]}
                ],
                "Species Traits": [],
                "Feats": [],
            },
            "Background": {
                "Background": "Soldier",
                "Characteristics": {
                    "Personality Traits": "",
                    "Ideals": "",
                    "Bonds": "",
                    "Flaws": "",
                },
                "Appearance": {
                    "Alignment": "",
                    "Gender": "",
                    "Age": "",
                    "Size": "",
                    "Height": "",
                    "Weight": "",
                    "Eyes": "",
                    "Skin": "",
                    "Faith": "",
                    "Hair": "",
                },
            },
            "Notes": {
                "Backstory": "",
                "Organizations": [],
                "Allies": [],
                "Enemies": [],
                "Other": [],
            },
        },
        "_action_example": {
            "name": "Longsword",
            "description": "Melee weapon attack.",
            "attack_bonus": 5,
            "damage_rolls": ["1d8+3"],
            "damage_types": ["Slashing"],
            "save_ability": "",
            "save_dc": None,
        },
        "_spell_example": {
            "name": "Fire Bolt",
            "level": 0,
            "description": "A ranged spell attack.",
            "casting_time": "1 Action",
            "range": "120 feet",
            "effect": "Fire damage",
            "duration": "Instantaneous",
            "components": "V/S",
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


def _normalize_image_paths(value):
    paths = value if isinstance(value, list) else []
    return [
        _text(paths[index], maximum=1000) if index < len(paths) else ""
        for index in range(4)
    ]


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
        damage_rolls = _normalize_rolls(item.get("damage_rolls") or item.get("damage"))
        raw_types = item.get("damage_types") or item.get("damage_type") or []
        if isinstance(raw_types, str):
            raw_types = [raw_types]
        damage_types = [
            _text(damage_type, maximum=50)
            for damage_type in raw_types[:len(damage_rolls)]
        ] if isinstance(raw_types, list) else []
        damage_types.extend([""] * (len(damage_rolls) - len(damage_types)))
        description = _text(item.get("description") or item.get("snippet"))
        description_parts = re.split(r"\s*\|\s*", description) if description else []
        while description_parts and damage_rolls:
            parsed_rolls, parsed_types, parsed_details = _split_action_damage(
                [description_parts[0]]
            )
            if (
                len(parsed_rolls) != 1
                or parsed_rolls[0] not in damage_rolls
                or not parsed_types[0]
            ):
                break
            damage_index = damage_rolls.index(parsed_rolls[0])
            if not damage_types[damage_index]:
                damage_types[damage_index] = parsed_types[0]
            description_parts.pop(0)
            description_parts[0:0] = parsed_details
        description = " | ".join(description_parts)
        result.append(
            {
                "name": _text(item.get("name"), maximum=100),
                "description": description,
                "attack_bonus": (
                    _integer(item.get("attack_bonus"), minimum=-100, maximum=100)
                    if item.get("attack_bonus") not in (None, "")
                    else None
                ),
                "damage_rolls": damage_rolls,
                "damage_types": damage_types,
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


DAMAGE_TYPES = (
    "acid", "bludgeoning", "cold", "fire", "force", "lightning", "necrotic",
    "piercing", "poison", "psychic", "radiant", "slashing", "thunder",
)


def _split_action_damage(parts):
    rolls, damage_types, details = [], [], []
    damage_pattern = re.compile(
        r"^(\+?(?:\d*d\d+(?:[+-]\d+)?|\d+))(?:\s+(" + "|".join(DAMAGE_TYPES) + r")\b)?(.*)$",
        re.I,
    )
    for part in parts:
        match = damage_pattern.match(str(part).strip())
        if match:
            rolls.append(match.group(1).lstrip("+"))
            damage_types.append((match.group(2) or "").title())
            remainder = match.group(3).strip(" ,;|-")
            if remainder:
                details.append(remainder)
        else:
            details.append(str(part).strip())
    return rolls, damage_types, [value for value in details if value]


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
                "casting_time": _text(
                    item.get("casting_time") or definition.get("casting_time"),
                    maximum=100,
                ),
                "range": _text(
                    item.get("range") or definition.get("range"), maximum=100
                ),
                "effect": _text(
                    item.get("effect") or definition.get("effect"), maximum=300
                ),
                "duration": _text(
                    item.get("duration") or definition.get("duration"), maximum=100
                ),
                "components": _text(
                    item.get("components") or definition.get("components"), maximum=100
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


def _expanded_casting_time(value):
    selected = _text(value, maximum=100)
    match = re.fullmatch(r"(\d+)\s*(BA|A|R|M|H)", selected, re.I)
    if not match:
        return selected
    amount = int(match.group(1))
    unit = {
        "BA": "Bonus Action",
        "A": "Action",
        "R": "Reaction",
        "M": "Minute",
        "H": "Hour",
    }[match.group(2).upper()]
    return f"{amount} {unit}{'' if amount == 1 else 's'}"


def _flattened_spell_details(parts):
    result = {
        "casting_time": "",
        "range": "",
        "effect": "",
        "duration": "",
        "components": "",
    }
    leftovers = []
    for value in (part.strip() for part in parts if part.strip()):
        if re.fullmatch(r"(?:[+-]\d{1,2}|(?:STR|DEX|CON|INT|WIS|CHA)\s+\d{1,2})", value, re.I):
            continue
        if not result["casting_time"] and re.fullmatch(
            r"(?:\d+\s*(?:BA|A|R|M|H)|\d+\s+(?:bonus action|action|reaction|minute|hour)s?)",
            value,
            re.I,
        ):
            result["casting_time"] = _expanded_casting_time(value)
        elif not result["range"] and re.search(
            r"\b(?:self|touch|sight|unlimited|\d+\s*(?:ft\.?|feet|mile|miles))\b",
            value,
            re.I,
        ):
            result["range"] = value
        elif re.fullmatch(r"[VSM](?:\s*[,/]\s*[VSM]){0,2}", value, re.I):
            if not result["components"]:
                result["components"] = "/".join(re.findall(r"[VSM]", value.upper()))
        elif not result["duration"] and re.search(
            r"\b(?:instantaneous|concentration|until dispelled|round|minute|hour|day|week|year)s?\b",
            value,
            re.I,
        ):
            result["duration"] = value
        elif re.fullmatch(r"[A-Z][A-Z0-9&' -]{1,20}\s+\d+", value):
            continue
        else:
            leftovers.append(value)
    result["effect"] = " | ".join(leftovers)
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


def _as_section_list(value):
    if value in (None, "", {}, []):
        return []
    return value if isinstance(value, list) else [value]


def _normalize_proficiencies(value):
    result = []
    seen = set()
    if isinstance(value, dict):
        value = [
            {"name": name, "type": proficiency_type}
            for proficiency_type, names in value.items()
            for name in (names if isinstance(names, list) else [names])
        ]
    for item in value if isinstance(value, list) else []:
        if isinstance(item, dict):
            name = _text(item.get("name"), maximum=100)
            proficiency_type = _text(item.get("type"), maximum=40)
        else:
            match = re.match(r"(.+?)\s*\(([^()]+)\)\s*$", str(item or ""))
            name = _text(match.group(1) if match else item, maximum=100)
            proficiency_type = _text(match.group(2) if match else "Other", maximum=40)
        identity = (name.casefold(), proficiency_type.casefold())
        if name and identity not in seen:
            seen.add(identity)
            result.append({"name": name, "type": proficiency_type or "Other"})
    return result[:200]


def _clean_feature_summaries(features):
    """Remove information now rendered in the character Summary."""
    proficiency_titles = {
        "proficiencies", "proficiencies and training", "proficiencies & training"
    }
    casting_line = re.compile(r"\bspell\s*casting\s+(?:ability|modifier)\b", re.I)
    for category in ("Class Features", "Species Traits", "Feats"):
        cleaned = []
        for item in _as_section_list(features.get(category)):
            if isinstance(item, dict):
                if str(item.get("name", "")).strip().casefold() in proficiency_titles:
                    continue
                item = deepcopy(item)
                item["details"] = [
                    detail for detail in _as_section_list(item.get("details"))
                    if not casting_line.search(str(detail))
                ]
            elif (
                str(item).strip().casefold() in proficiency_titles
                or casting_line.search(str(item))
            ):
                continue
            cleaned.append(item)
        features[category] = cleaned
    return features


def _feature_summary_proficiencies(supplied):
    if not isinstance(supplied, dict):
        return []
    features = supplied.get("Features and Traits")
    if not isinstance(features, dict):
        return []
    titles = {"proficiencies", "proficiencies and training", "proficiencies & training"}
    extracted = []
    for category in features.values():
        for item in _as_section_list(category):
            if not isinstance(item, dict) or str(item.get("name", "")).strip().casefold() not in titles:
                continue
            for detail in _as_section_list(item.get("details")):
                text = str(detail).strip()
                match = re.match(
                    r"^(Armor|Armour|Weapons?|Languages?|Tools?)\s*:?\s*(.+)$", text, re.I
                )
                if match:
                    proficiency_type = _proficiency_type(match.group(1))
                    names = re.split(r"\s*,\s*|\s*;\s*", match.group(2))
                else:
                    suffix = re.match(r"^(.+?)\s+(Armor|Weapons?|Languages?|Tools?)$", text, re.I)
                    if not suffix:
                        continue
                    proficiency_type = _proficiency_type(suffix.group(2))
                    names = [suffix.group(1)]
                extracted.extend(
                    {"name": name.strip(), "type": proficiency_type}
                    for name in names if name.strip()
                )
    return _normalize_proficiencies(extracted)


def _section_text(value):
    if isinstance(value, dict):
        return "\n".join(_section_text(item) for item in value.values())
    if isinstance(value, list):
        return "\n".join(_section_text(item) for item in value)
    return str(value or "")


def _canonical_character_sections(payload, supplied):
    """Return schema-v2 sections while accepting legacy JSON exports."""
    sections = deepcopy(supplied) if isinstance(supplied, dict) else {}

    equipment = sections.get("Equipment")
    if not isinstance(equipment, dict):
        legacy_inventory = sections.pop("Inventory", None)
        if legacy_inventory in (None, "", {}, []):
            legacy_inventory = payload.get("inventory")
        equipment = {
            "Personal Belongings": [],
            "Attuned Items": [],
            "Other": _as_section_list(legacy_inventory),
        }
    equipment.setdefault("Personal Belongings", [])
    equipment.setdefault("Attuned Items", [])
    equipment.setdefault("Other", [])

    features = sections.get("Features and Traits")
    if not isinstance(features, dict):
        features = {
            "Class Features": _as_section_list(
                sections.pop("Features", None) or payload.get("features")
            ),
            "Species Traits": _as_section_list(
                sections.pop("Traits", None) or payload.get("traits")
            ),
            "Feats": _as_section_list(payload.get("feats")),
        }
    for key in ("Class Features", "Species Traits", "Feats"):
        features.setdefault(key, [])
    features = _clean_feature_summaries(features)

    background = sections.get("Background")
    if not isinstance(background, dict):
        background = {
            "Background": background or payload.get("background") or "",
            "Characteristics": payload.get("characteristics") or {},
            "Appearance": payload.get("appearance") or "",
        }
    background.setdefault("Background", "")
    background.setdefault("Characteristics", {})
    background.setdefault("Appearance", "")

    notes = sections.get("Notes")
    if not isinstance(notes, dict):
        legacy_notes = notes or payload.get("notes")
        notes = {
            "Organizations": _as_section_list(payload.get("organizations")),
            "Allies": _as_section_list(payload.get("allies")),
            "Enemies": _as_section_list(payload.get("enemies")),
            "Backstory": payload.get("backstory") or "",
            "Other": _as_section_list(legacy_notes),
        }
    for key, default in (
        ("Backstory", ""), ("Organizations", []), ("Allies", []),
        ("Enemies", []), ("Other", []),
    ):
        notes.setdefault(key, default)
    notes = {
        key: notes[key]
        for key in ("Backstory", "Organizations", "Allies", "Enemies", "Other")
    }

    return {
        "Equipment": equipment,
        "Features and Traits": features,
        "Background": background,
        "Notes": notes,
    }


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
    supplied_sections = payload.get("sections")
    migrated_proficiencies = _feature_summary_proficiencies(supplied_sections)
    raw_spellcasting = payload.get("spellcasting") or _flattened_spellcasting(
        [{"text": _section_text(supplied_sections)}], abilities, proficiency, spells
    )
    casting_ability = _text(raw_spellcasting.get("ability"), maximum=3).casefold()
    if casting_ability not in ABILITY_NAMES:
        casting_ability = ""
    sections = _canonical_character_sections(payload, supplied_sections)
    return {
        "schema_version": 2,
        "id": identifier,
        "owner_id": str(owner_id),
        "name": name,
        "nickname": _text(payload.get("nickname"), maximum=100),
        "source": _text(payload.get("source") or source, maximum=50),
        "source_reference": _text(payload.get("source_reference"), maximum=200),
        "avatar_url": _text(payload.get("avatar_url") or payload.get("avatarUrl"), maximum=1000),
        "image_path": "",
        "image_paths": _normalize_image_paths(
            payload.get("image_paths") or payload.get("images")
        ),
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
        "spellcasting": {
            "ability": casting_ability,
            "save_dc": _integer(
                raw_spellcasting.get("save_dc"), 0, minimum=0, maximum=100
            ),
            "attack_bonus": _integer(
                raw_spellcasting.get("attack_bonus"), 0, minimum=-100, maximum=100
            ),
        },
        "proficiencies": _normalize_proficiencies(
            payload.get("proficiencies") or migrated_proficiencies
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


def _flat_readable(value):
    return " ".join(part.strip() for part in str(value or "").split("|") if part.strip())


def _strip_book_references(value):
    selected = re.sub(
        r"\s*•\s*[A-Za-z][A-Za-z0-9]{1,9}\s+\d{1,4}\b",
        "",
        str(value or ""),
    )
    return re.sub(r"\s{2,}", " ", selected).strip(" •")


def _strip_biography_section_titles(value):
    selected = re.sub(
        r"\b(?:CHARACTER BACKSTORY|ADDITIONAL NOTES)\b",
        "",
        str(value or ""),
        flags=re.I,
    )
    return re.sub(r"\s{2,}", " ", selected).strip()


def _proficiency_type(value):
    selected = str(value or "").strip().casefold().rstrip(":")
    return {
        "armor": "Armor",
        "armour": "Armor",
        "weapon": "Weapons",
        "weapons": "Weapons",
        "language": "Language",
        "languages": "Language",
        "tool": "Tool",
        "tools": "Tool",
    }.get(selected, "")


def _flattened_proficiencies(page):
    """Extract typed entries from a flattened Proficiencies and Training area."""
    result = []
    current_type = ""
    for item in sorted(page.get("blocks", []), key=lambda value: (value.get("y0", 0), value.get("x0", 0))):
        text = str(item.get("text", "")).strip()
        if not text or re.search(r"===\s*PROFICIENCIES", text, re.I):
            continue
        if _proficiency_type(text):
            current_type = _proficiency_type(text)
            continue
        parts = [part.strip(" •*") for part in text.split("|") if part.strip(" •*")]
        pairs = []
        if len(parts) >= 2 and _proficiency_type(parts[0]):
            pairs.extend((name, _proficiency_type(parts[0])) for name in parts[1:])
        elif len(parts) >= 2 and _proficiency_type(parts[-1]):
            pairs.append((" | ".join(parts[:-1]), _proficiency_type(parts[-1])))
        else:
            match = re.match(
                r"^(Armor|Armour|Weapons?|Languages?|Tools?)\s*:\s*(.+)$", text, re.I
            )
            if match:
                pairs.extend(
                    (name.strip(), _proficiency_type(match.group(1)))
                    for name in re.split(r"\s*,\s*|\s*;\s*", match.group(2))
                )
            elif current_type and len(parts) == 1 and text.lstrip().startswith(("*", "•")):
                pairs.append((parts[0], current_type))
        for name, proficiency_type in pairs:
            name = re.sub(
                rf"\s+{re.escape(proficiency_type)}$", "", name, flags=re.I
            ).strip()
            if name:
                result.append({"name": name, "type": proficiency_type})
    return _normalize_proficiencies(result)


def _flattened_spellcasting(pages, abilities, proficiency, spells):
    text = "\n".join(page.get("text", "") for page in pages)
    ability_match = re.search(
        r"spell\s*casting\s+(?:ability|modifier)\s*[:|]?\s*(STR|DEX|CON|INT|WIS|CHA)\b",
        text,
        re.I,
    )
    dc_match = re.search(r"spell\s*(?:save\s*)?dc\s*[:|]?\s*(\d{1,2})\b", text, re.I)
    attack_match = re.search(
        r"spell\s*attack(?:\s+bonus)?\s*[:|]?\s*([+-]?\d{1,2})\b", text, re.I
    )
    save_dc = int(dc_match.group(1)) if dc_match else next(
        (int(item["save_dc"]) for item in spells if item.get("save_dc")), 0
    )
    attack_bonus = int(attack_match.group(1)) if attack_match else next(
        (int(item["attack_bonus"]) for item in spells if item.get("attack_bonus") is not None),
        0,
    )
    ability = ability_match.group(1).casefold() if ability_match else ""
    if not ability and attack_bonus:
        expected_modifier = attack_bonus - int(proficiency)
        ability = next(
            (
                key for key, score in abilities.items()
                if ability_modifier(int(score)) == expected_modifier
            ),
            "",
        )
    return {"ability": ability, "save_dc": save_dc, "attack_bonus": attack_bonus}


def _flattened_feature_sections(page):
    result = {"Class Features": [], "Species Traits": [], "Feats": []}
    for section_name in result:
        current_index = None
        candidates = []
        for item in page["blocks"]:
            if not 125 <= item["y0"] < 480:
                continue
            if section_name == "Class Features" and (
                item["x0"] < 200
                or (200 <= item["x0"] < 390 and item["y0"] < 185)
            ):
                candidates.append(item)
            elif (
                section_name == "Species Traits"
                and 200 <= item["x0"] < 390
                and item["y0"] >= 185
            ):
                candidates.append(item)
            elif section_name == "Feats" and item["x0"] >= 390:
                candidates.append(item)
        for item in sorted(candidates, key=lambda value: value["y0"]):
            text = item["text"].strip()
            if re.search(r"===\s*(.+?)\s*===", text):
                current_index = None
                continue
            parts = [part.strip() for part in text.split("|") if part.strip()]
            readable = _strip_book_references(parts[0].lstrip("* ")) if parts else ""
            details = [
                _strip_book_references(part) for part in parts[1:]
                if _strip_book_references(part)
            ]
            if not readable:
                continue
            if text.lstrip().startswith("*"):
                result[section_name].append({"name": readable, "details": details})
                current_index = len(result[section_name]) - 1
            elif current_index is not None:
                result[section_name][current_index]["details"].append(
                    _strip_book_references(_flat_readable(text).lstrip("| "))
                )
        if section_name == "Class Features":
            removable = {
                "additional warlock spells", "ability score improvement", "hit points"
            }
            result[section_name] = [
                item for item in result[section_name]
                if item["name"].casefold() not in removable or item["details"]
            ]
    return result


def _looks_like_container(name):
    selected = str(name or "").casefold()
    return selected == "personal belongings" or any(
        word in selected
        for word in ("bag of holding", "backpack", "quiver", "pouch", "sack", "chest", "case,")
    )


def _flattened_equipment_sections(pages):
    result = {"Personal Belongings": [], "Attuned Items": [], "Other": []}
    seen = set()
    inventory_pages = pages[1:4]
    for page_index, page in enumerate(inventory_pages):
        columns = {}
        for item in page["blocks"]:
            if item["y0"] < 510:
                continue
            parts = [part.strip() for part in item["text"].split("|") if part.strip()]
            if len(parts) < 3 or not re.fullmatch(r"\d+", parts[-2]):
                continue
            column = int(item["x0"] // 180)
            columns.setdefault(column, []).append((item, parts))
        for column, values in columns.items():
            current = "Other"
            for item, parts in sorted(values, key=lambda value: value[0]["y0"]):
                name, quantity, weight = parts[0], parts[-2], parts[-1]
                gp_value = next(
                    (
                        match.group(1)
                        for value in parts[1:-2]
                        if (match := re.search(r"\b(\d+(?:\.\d+)?)\s*gp\b", value, re.I))
                    ),
                    None,
                )
                if page_index == 0 and column >= 1 and item["y0"] >= 695:
                    current = "Attuned Items"
                if _looks_like_container(name):
                    current = "Personal Belongings" if name.casefold() == "personal belongings" else name
                    result.setdefault(current, [])
                    continue
                key = (current.casefold(), name.casefold(), quantity, weight.casefold())
                if key in seen:
                    continue
                seen.add(key)
                result.setdefault(current, []).append({
                    "name": name,
                    "quantity": quantity,
                    "weight": weight,
                    "gp_value": gp_value,
                })
    attuned_names = {
        item["name"].casefold() for item in result.get("Attuned Items", [])
    }
    containers = {
        key: value for key, value in result.items()
        if key not in {"Personal Belongings", "Attuned Items", "Other"}
    }
    ordered = {
        **containers,
        "Personal Belongings": result.get("Personal Belongings", []),
        "Attuned Items": result.get("Attuned Items", []),
        "Other": result.get("Other", []),
    }
    claimed = set()
    final = {}
    for section in [*containers, "Personal Belongings", "Attuned Items", "Other"]:
        items = []
        for item in ordered.get(section, []):
            identity = (
                item["name"].casefold(), item["quantity"], item["weight"].casefold()
            )
            if identity in claimed or (
                section != "Attuned Items" and item["name"].casefold() in attuned_names
            ):
                continue
            if section != "Attuned Items":
                claimed.add(identity)
            items.append(item)
        if items:
            final[section] = items
    return final


def _flattened_biography_sections(page, background):
    blocks = page["blocks"]
    fields = page.get("fields", {})
    characteristics = {}
    characteristic_labels = (
        ("Personality Traits", 120, 190),
        ("Ideals", 190, 245),
        ("Bonds", 245, 300),
        ("Flaws", 300, 370),
    )
    for label, y0, y1 in characteristic_labels:
        values = [
            _flat_readable(item["text"])
            for item in blocks
            if item["x0"] >= 400 and y0 <= item["y0"] < y1
            and _flat_readable(item["text"]).casefold() != label.casefold()
        ]
        if values:
            characteristics[label] = " ".join(values)

    appearance = {
        "Alignment": fields.get("ALIGNMENT") or "NONE",
        "Gender": fields.get("GENDER") or "NONE",
        "Age": fields.get("AGE") or "NONE",
        "Size": fields.get("SIZE") or "NONE",
        "Height": fields.get("HEIGHT") or "NONE",
        "Weight": (f"{fields['WEIGHT']} lb" if fields.get("WEIGHT") else "NONE"),
        "Eyes": fields.get("EYES") or "NONE",
        "Skin": fields.get("SKIN") or "NONE",
        "Faith": fields.get("FAITH") or "NONE",
        "Hair": fields.get("HAIR") or "NONE",
    }
    backstory = " ".join(
        _strip_biography_section_titles(_flat_readable(item["text"]))
        for item in blocks
        if item["x0"] < 220 and item["y0"] >= 380
        and _strip_biography_section_titles(_flat_readable(item["text"]))
    )
    right_notes = [
        _flat_readable(item["text"])
        for item in blocks
        if 220 <= item["x0"] < 400 and 120 <= item["y0"] < 370
    ]
    organizations, allies, enemies, other = [], [], [], []
    destination = other
    for value in right_notes:
        heading = re.fullmatch(r"===\s*(.+?)\s*===", value)
        if heading:
            label = heading.group(1).casefold()
            destination = (
                organizations if "organization" in label else
                allies if "allies" in label else
                enemies if "enem" in label else other
            )
        elif value:
            destination.append(value)
    other.extend(
        _flat_readable(item["text"])
        for item in blocks
        if 220 <= item["x0"] < 400 and item["y0"] >= 370
        and _flat_readable(item["text"])
    )
    background_sections = {
        "Background": background or "None recorded.",
        "Characteristics": characteristics,
        "Appearance": appearance,
    }
    note_sections = {
        "Organizations": organizations,
        "Allies": allies,
        "Enemies": enemies,
        "Backstory": backstory,
        "Other": other,
    }
    return background_sections, note_sections


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

    identity = next(
        (
            item["text"] for item in blocks
            if item["x0"] >= 220 and 65 <= item["y0"] < 90
            and "|" in item["text"]
            and "class & level" not in item["text"].casefold()
        ),
        "",
    )
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
        rolls, damage_types, description_parts = _split_action_damage(parts[2:])
        actions.append({
            "name": parts[0],
            "description": " | ".join(description_parts),
            "attack_bonus": parts[1],
            "damage_rolls": rolls,
            "damage_types": damage_types,
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
            _prepared, spell_name, _source = match.groups()
            spell_name = re.sub(r"\s+\[R\]$", "", spell_name).strip()
            identity_key = (spell_name.casefold(), spell_level)
            if identity_key in seen_spells:
                continue
            seen_spells.add(identity_key)
            save = re.search(r"\b(STR|DEX|CON|INT|WIS|CHA)\s+(\d{1,2})\b", text)
            attack = re.search(r"(?<![\w/])\+(\d{1,2})(?!\w)", text)
            columns = [part.strip() for part in text.split("|")]
            display = _flattened_spell_details(columns[3:])
            spells.append({
                "name": spell_name,
                "level": spell_level,
                "description": "",
                **display,
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
    feature_sections = _flattened_feature_sections(pages[1]) if len(pages) > 1 else {}
    equipment_sections = _flattened_equipment_sections(pages)
    background_sections, note_sections = (
        _flattened_biography_sections(pages[4], background)
        if len(pages) > 4 else
        ({"Background": background}, {})
    )
    sections = {
        "Equipment": equipment_sections,
        "Features and Traits": feature_sections,
        "Background": background_sections,
        "Notes": note_sections,
    }
    proficiency_value = _flat_number(proficiency, proficiency_bonus(level))
    proficiencies = _flattened_proficiencies(pages[1]) if len(pages) > 1 else []
    spellcasting = _flattened_spellcasting(
        pages, abilities, proficiency_value, spells
    )
    return {
        "name": name,
        "classes": [{"name": class_name, "subclass": subclass, "level": level}],
        "abilities": abilities,
        "saving_throws": saving_throws,
        "skills": skills,
        "proficiency_bonus": proficiency_value,
        "speed": _flat_number(speed, 30),
        "initiative": combat_values[0] if combat_values else ability_modifier(int(abilities["dex"])),
        "armor_class": combat_values[1] if len(combat_values) > 1 else 10,
        "max_hit_points": _flat_number(hit_points, 1),
        "spellcasting": spellcasting,
        "proficiencies": proficiencies,
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
            fields = {
                str(widget.field_name or "").strip().upper(): str(widget.field_value or "").strip()
                for widget in (page.widgets() or [])
                if str(widget.field_name or "").strip()
            }
            pages.append({
                "text": page_text,
                "fields": fields,
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
        damage_value = _pdf_field_value(fields, (f"Wpn{index} Damage", f"WpnDamage{index}"))
        rolls, damage_types, damage_details = _split_action_damage([damage_value])
        actions.append(
            {
                "name": name,
                "description": " | ".join(damage_details),
                "attack_bonus": _pdf_field_value(fields, (f"Wpn{index} AtkBonus", f"WpnAtkBonus{index}")),
                "damage_rolls": rolls,
                "damage_types": damage_types,
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
                normalized["image_paths"] = previous.get("image_paths", ["", "", "", ""])
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

    def import_dndbeyond_json(
        self, owner_id, data: bytes, source_url: str, *, replace_selector=None
    ) -> dict:
        if len(data) > int(self.settings.get("max_import_bytes", MAX_IMPORT_BYTES)):
            raise CharacterError("The D&D Beyond character data exceeds the import limit.")
        try:
            response = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CharacterError("D&D Beyond returned invalid character data.") from error
        payload = response.get("data") if isinstance(response, dict) else None
        if not isinstance(payload, dict):
            message = _text(response.get("message"), maximum=300) if isinstance(response, dict) else ""
            raise CharacterError(
                message or "D&D Beyond did not return a public character sheet."
            )
        payload = deepcopy(payload)
        payload["source"] = "dndbeyond"
        payload["source_reference"] = source_url
        character = normalize_character(payload, str(owner_id), source="dndbeyond")
        return self.save(owner_id, character, replace_selector=replace_selector)

    @staticmethod
    def _dndbeyond_payload(data: bytes) -> dict:
        try:
            response = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CharacterError("D&D Beyond returned invalid character data.") from error
        payload = response.get("data") if isinstance(response, dict) else None
        if not isinstance(payload, dict):
            raise CharacterError("D&D Beyond did not return a public character sheet.")
        return payload

    @staticmethod
    def _merge_spell_details(character: dict, payload: dict, owner_id) -> None:
        reference = normalize_character(payload, str(owner_id), source="dndbeyond")
        available = {
            (spell["name"].casefold(), spell["level"]): spell
            for spell in reference.get("spells", ())
        }
        for spell in character.get("spells", ()):
            detail = available.get((spell["name"].casefold(), spell["level"]))
            if detail is None:
                detail = next(
                    (
                        value for (name, _level), value in available.items()
                        if name == spell["name"].casefold()
                    ),
                    None,
                )
            if detail is None:
                continue
            for key in (
                "description", "higher_levels", "damage_rolls",
                "damage_rolls_by_level", "casting_time", "range", "effect",
                "duration", "components",
            ):
                if detail.get(key) and not spell.get(key):
                    spell[key] = deepcopy(detail[key])

    @staticmethod
    def _item_gp_value(definition: dict):
        raw_value = definition.get("cost")
        if raw_value is None:
            raw_value = definition.get("value")
        unit = "gp"
        if isinstance(raw_value, dict):
            unit = str(
                raw_value.get("unit") or raw_value.get("currency") or "gp"
            ).casefold()
            raw_value = next(
                (
                    raw_value.get(key)
                    for key in ("quantity", "amount", "value")
                    if raw_value.get(key) is not None
                ),
                None,
            )
        if isinstance(raw_value, str):
            match = re.fullmatch(
                r"\s*(\d+(?:\.\d+)?)\s*(cp|sp|ep|gp|pp)?\s*",
                raw_value,
                re.I,
            )
            if not match:
                return None
            raw_value = match.group(1)
            unit = (match.group(2) or unit).casefold()
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            return None
        value *= {"cp": 0.01, "sp": 0.1, "ep": 0.5, "gp": 1, "pp": 10}.get(
            unit, 1
        )
        return int(value) if value.is_integer() else value

    @staticmethod
    def _merge_equipment_details(character: dict, payload: dict) -> None:
        available = {}
        for entry in payload.get("inventory") or ():
            if not isinstance(entry, dict):
                continue
            definition = entry.get("definition") or entry
            if not isinstance(definition, dict):
                continue
            name = _text(
                entry.get("name") or definition.get("name"), maximum=200
            )
            if not name:
                continue
            key = re.sub(r"[^a-z0-9]+", " ", name.casefold()).strip()
            available.setdefault(key, []).append({
                "description": _text(
                    definition.get("description") or definition.get("snippet")
                ),
                "gp_value": CharacterService._item_gp_value(definition),
            })

        equipment = character.get("sections", {}).get("Equipment", {})
        if not isinstance(equipment, dict):
            return
        matched = {}
        for items in equipment.values():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                key = re.sub(
                    r"[^a-z0-9]+", " ", str(item.get("name", "")).casefold()
                ).strip()
                candidates = available.get(key, ())
                if not candidates:
                    continue
                index = min(matched.get(key, 0), len(candidates) - 1)
                detail = candidates[index]
                matched[key] = index + 1
                if detail.get("description") and not item.get("description"):
                    item["description"] = detail["description"]
                if detail.get("gp_value") is not None and item.get("gp_value") in (
                    None,
                    "",
                ):
                    item["gp_value"] = detail["gp_value"]

    def import_pdf(
        self,
        owner_id,
        data: bytes,
        *,
        dndbeyond_data: bytes | None = None,
        source_url: str = "",
        replace_selector=None,
    ) -> dict:
        if len(data) > int(self.settings.get("max_import_bytes", MAX_IMPORT_BYTES)):
            raise CharacterError("The character PDF exceeds the import size limit.")
        character = character_from_pdf(data, str(owner_id))
        if dndbeyond_data is not None:
            if len(dndbeyond_data) > int(
                self.settings.get("max_import_bytes", MAX_IMPORT_BYTES)
            ):
                raise CharacterError("The D&D Beyond character data exceeds the import limit.")
            payload = self._dndbeyond_payload(dndbeyond_data)
            self._merge_spell_details(character, payload, owner_id)
            self._merge_equipment_details(character, payload)
            character["source_reference"] = _text(source_url, maximum=200)
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
                elif key == "avatar_url":
                    stored[key] = _text(value, maximum=1000)
                elif key == "image_path":
                    stored[key] = _text(value, maximum=1000)
                elif key == "image_paths":
                    stored[key] = _normalize_image_paths(value)
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
        image_paths = [image_path, *removed.get("image_paths", [])]
        for stored_path in image_paths:
            if not stored_path:
                continue
            try:
                Path(stored_path).unlink(missing_ok=True)
            except OSError:
                pass
        return deepcopy(removed)

    def export(self, owner_id, selector) -> bytes:
        character = self.resolve(owner_id, selector)
        exported = deepcopy(character)
        exported["image_path"] = ""
        exported["image_paths"] = ["", "", "", ""]
        exported["schema_version"] = 2
        exported["sections"] = _canonical_character_sections(
            exported, exported.get("sections")
        )
        return (json.dumps(exported, indent=2) + "\n").encode("utf-8")

    def _normalized_image(self, data: bytes, content_type: str):
        if not data:
            raise CharacterError("The uploaded character image is empty.")
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
        return image

    def store_avatar(self, owner_id, selector, data: bytes, content_type: str) -> dict:
        image = self._normalized_image(data, content_type)
        character = self.resolve(owner_id, selector)
        directory = self.root / "images" / self.validate_owner(owner_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{character['id']}-avatar.png"
        image.save(path, format="PNG", optimize=True)
        try:
            path.chmod(0o600)
        except OSError:
            pass
        updated = self.update(
            owner_id, selector, image_path=str(path), avatar_url=""
        )
        previous_path = character.get("image_path")
        if previous_path and Path(previous_path) != path:
            try:
                Path(previous_path).unlink(missing_ok=True)
            except OSError:
                pass
        return updated

    def store_image(self, owner_id, selector, data: bytes, content_type: str) -> dict:
        """Backward-compatible alias for avatar storage."""
        return self.store_avatar(owner_id, selector, data, content_type)

    def remove_avatar(self, owner_id, selector) -> dict:
        character = self.resolve(owner_id, selector)
        path = character.get("image_path")
        updated = self.update(owner_id, selector, image_path="", avatar_url="")
        if path:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass
        return updated

    def store_gallery_image(
        self, owner_id, selector, slot: int, data: bytes, content_type: str
    ) -> dict:
        if slot not in range(1, 5):
            raise CharacterError("Character image slots must be from 1 through 4.")
        image = self._normalized_image(data, content_type)
        character = self.resolve(owner_id, selector)
        directory = self.root / "images" / self.validate_owner(owner_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{character['id']}-gallery-{slot}.png"
        image.save(path, format="PNG", optimize=True)
        try:
            path.chmod(0o600)
        except OSError:
            pass
        paths = _normalize_image_paths(character.get("image_paths"))
        paths[slot - 1] = str(path)
        return self.update(owner_id, selector, image_paths=paths)

    def remove_gallery_image(self, owner_id, selector, slot: int) -> dict:
        if slot not in range(1, 5):
            raise CharacterError("Character image slots must be from 1 through 4.")
        character = self.resolve(owner_id, selector)
        paths = _normalize_image_paths(character.get("image_paths"))
        path = paths[slot - 1]
        paths[slot - 1] = ""
        updated = self.update(owner_id, selector, image_paths=paths)
        if path:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass
        return updated
