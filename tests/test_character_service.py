import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from services.characterService import (
    CharacterError,
    CharacterService,
    ability_modifier,
    character_template_json,
    character_from_pdf,
    _flattened_pdf_payload,
    normalize_character,
    proficiency_bonus,
)


def sample_character(name="Arannis"):
    return {
        "name": name,
        "classes": [
            {"name": "Fighter", "subclass": "Battle Master", "level": 5},
            {"name": "Rogue", "subclass": "Assassin", "level": 3},
        ],
        "abilities": {
            "str": 16,
            "dex": 18,
            "con": 14,
            "int": 10,
            "wis": 12,
            "cha": 8,
        },
        "saving_throws": {"str": 6, "dex": 7},
        "skills": {"acrobatics": 7, "stealth": 10},
        "armor_class": 17,
        "initiative": 4,
        "speed": 30,
        "max_hit_points": 68,
        "actions": [
            {
                "name": "Longsword",
                "description": "A melee weapon attack.",
                "attack_bonus": 6,
                "damage_rolls": ["1d8+3"],
            }
        ],
        "spells": [
            {
                "name": "Fire Bolt",
                "level": 0,
                "description": "A mote of fire.",
                "attack_bonus": 7,
                "damage_rolls": ["1d10"],
                "damage_rolls_by_level": {"5": ["2d10"]},
            }
        ],
        "sections": {"Inventory": ["Rope", "Torch"]},
    }


class CharacterMathTests(unittest.TestCase):
    def test_ability_and_proficiency_modifiers(self):
        self.assertEqual(ability_modifier(8), -1)
        self.assertEqual(ability_modifier(10), 0)
        self.assertEqual(ability_modifier(18), 4)
        self.assertEqual(proficiency_bonus(1), 2)
        self.assertEqual(proficiency_bonus(8), 3)
        self.assertEqual(proficiency_bonus(17), 6)

    def test_documented_template_is_valid_and_importable(self):
        template = json.loads(character_template_json())
        self.assertEqual(template["schema_version"], 2)
        self.assertIn("_instructions", template)
        self.assertIn("_action_example", template)
        self.assertIn("_spell_example", template)
        imported = normalize_character(template, "123", source="json")
        self.assertEqual(imported["name"], "Example Character")
        self.assertEqual(imported["actions"], [])
        self.assertEqual(imported["spells"], [])
        self.assertEqual(imported["schema_version"], 2)
        self.assertEqual(
            list(imported["sections"]),
            ["Equipment", "Features and Traits", "Background", "Notes"],
        )
        self.assertIn("Backpack", imported["sections"]["Equipment"])
        self.assertIn(
            "Class Features", imported["sections"]["Features and Traits"]
        )

    def test_legacy_json_sections_are_migrated_to_schema_two(self):
        payload = sample_character()
        payload["sections"] = {
            "Inventory": ["Rope", "Torch"],
            "Features": ["Second Wind"],
            "Traits": ["Darkvision"],
            "Notes": "A legacy note.",
        }
        imported = normalize_character(payload, "123", source="json")
        self.assertEqual(imported["schema_version"], 2)
        self.assertEqual(
            imported["sections"]["Equipment"]["Other"], ["Rope", "Torch"]
        )
        self.assertEqual(
            imported["sections"]["Features and Traits"]["Class Features"],
            ["Second Wind"],
        )
        self.assertEqual(imported["sections"]["Notes"]["Other"], ["A legacy note."])

    def test_imported_pdf_legal_boilerplate_is_removed(self):
        from services.characterService import _strip_import_legal_boilerplate

        text = (
            "Nysari character notes\n"
            "TM & © 2018 Wizards of the Coast LLC. ©2018 D&D Beyond | "
            "All Rights Reserved. Permission is granted to photo copy this "
            "document for personal use.\n"
            "Equipment and features"
        )
        cleaned = _strip_import_legal_boilerplate(text)
        self.assertEqual(cleaned, "Nysari character notes\nEquipment and features")
        self.assertNotIn("Wizards of the Coast", cleaned)
        self.assertNotIn("All Rights Reserved", cleaned)

    def test_flattened_import_builds_requested_detail_sections(self):
        from services.characterService import (
            _flattened_biography_sections,
            _flattened_equipment_sections,
            _flattened_feature_sections,
        )

        feature_page = {"blocks": [
            {"x0": 38, "y0": 140, "text": "=== FIGHTER FEATURES ==="},
            {"x0": 38, "y0": 150, "text": "* Hit Points • PHB 71"},
            {"x0": 38, "y0": 160, "text": "* Second Wind • PHB 72 | Recover hit points."},
            {"x0": 221, "y0": 190, "text": "=== ELF SPECIES TRAITS ==="},
            {"x0": 221, "y0": 210, "text": "* Darkvision • BR 23 | See in darkness."},
            {"x0": 402, "y0": 140, "text": "=== FEATS ==="},
            {"x0": 402, "y0": 160, "text": "* Alert • PHB 165 | Initiative bonus."},
        ]}
        features = _flattened_feature_sections(feature_page)
        self.assertEqual(features["Class Features"][0]["name"], "Second Wind")
        self.assertEqual(features["Species Traits"][0]["name"], "Darkvision")
        self.assertEqual(features["Feats"][0]["name"], "Alert")
        self.assertNotIn("PHB 72", str(features))
        self.assertNotIn("Hit Points", str(features))

        empty_page = {"blocks": []}
        equipment_page = {"blocks": [
            {"x0": 114, "y0": 527, "text": "Backpack | 1 | 5 lb."},
            {"x0": 114, "y0": 542, "text": "Rope | 1 | 10 lb."},
            {"x0": 351, "y0": 706, "text": "Ring | 1 | --"},
        ]}
        equipment = _flattened_equipment_sections([empty_page, equipment_page])
        self.assertEqual(equipment["Backpack"][0]["name"], "Rope")
        self.assertEqual(equipment["Attuned Items"][0]["name"], "Ring")

        biography = {"fields": {
            "ALIGNMENT": "Chaotic Neutral",
            "GENDER": "Female",
            "AGE": "65",
            "SIZE": "Medium",
            "HEIGHT": "4'9\"",
            "WEIGHT": "95",
            "EYES": "Bright Royal Blue",
            "SKIN": "Porcelain White with light blue glittering snow pa",
            "FAITH": "Lin (Winter Warden)",
        }, "blocks": [
            {"x0": 421, "y0": 131, "text": "Always prepared."},
            {"x0": 230, "y0": 128, "text": "=== Allies ==="},
            {"x0": 230, "y0": 145, "text": "Lin"},
            {"x0": 83, "y0": 756, "text": "CHARACTER BACKSTORY | ADDITIONAL NOTES"},
            {"x0": 39, "y0": 386, "text": "A long backstory."},
        ]}
        background, notes = _flattened_biography_sections(biography, "Acolyte")
        self.assertEqual(background["Background"], "Acolyte")
        self.assertEqual(notes["Allies"], ["Lin"])
        self.assertEqual(notes["Backstory"], "A long backstory.")
        self.assertNotIn("CHARACTER BACKSTORY", notes["Backstory"])
        self.assertNotIn("ADDITIONAL NOTES", notes["Backstory"])
        self.assertEqual(background["Appearance"]["Alignment"], "Chaotic Neutral")
        self.assertEqual(background["Appearance"]["Weight"], "95 lb")
        self.assertEqual(background["Appearance"]["Eyes"], "Bright Royal Blue")
        self.assertEqual(background["Appearance"]["Faith"], "Lin (Winter Warden)")
        self.assertEqual(background["Appearance"]["Hair"], "NONE")

    def test_normalization_preserves_roll_data(self):
        value = normalize_character(sample_character(), "123", source="manual")

        self.assertEqual(value["level"], 8)
        self.assertEqual(value["proficiency_bonus"], 3)
        self.assertEqual(value["actions"][0]["damage_rolls"], ["1d8+3"])
        self.assertEqual(
            value["spells"][0]["damage_rolls_by_level"]["5"],
            ["2d10"],
        )


class CharacterServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.service = CharacterService(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_characters_are_isolated_by_discord_owner(self):
        first = self.service.save("123", sample_character())
        self.service.save("456", sample_character("Other Hero"))

        self.assertEqual(self.service.resolve("123", first["id"])["name"], "Arannis")
        with self.assertRaisesRegex(CharacterError, "not linked"):
            self.service.resolve("456", first["id"])

    def test_duplicate_names_are_rejected_for_one_owner(self):
        self.service.save("123", sample_character())
        with self.assertRaisesRegex(CharacterError, "already have"):
            self.service.save("123", sample_character())

    def test_json_round_trip_and_refresh_preserve_identity_metadata(self):
        original = self.service.save("123", sample_character())
        self.service.update("123", original["id"], nickname="Moon")
        exported = self.service.export("123", original["id"])
        payload = json.loads(exported)
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(
            list(payload["sections"]),
            ["Equipment", "Features and Traits", "Background", "Notes"],
        )
        payload["armor_class"] = 19

        refreshed = self.service.import_json(
            "123",
            json.dumps(payload).encode(),
            replace_selector=original["id"],
        )

        self.assertEqual(refreshed["id"], original["id"])
        self.assertEqual(refreshed["nickname"], "Moon")
        self.assertEqual(refreshed["armor_class"], 19)

    def test_delete_requires_the_owner(self):
        character = self.service.save("123", sample_character())
        with self.assertRaises(CharacterError):
            self.service.delete("456", character["id"])
        self.assertEqual(self.service.delete("123", character["id"])["name"], "Arannis")
        self.assertEqual(self.service.list("123"), [])

    def test_store_recovers_from_atomic_backup(self):
        character = self.service.save("123", sample_character())
        self.service.update("123", character["id"], nickname="Backup Maker")
        self.service.path("123").write_text("{broken", encoding="utf-8")

        recovered = self.service.list("123")

        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0]["name"], "Arannis")

    def test_valid_image_is_normalized_and_stored(self):
        character = self.service.save("123", sample_character())
        source = io.BytesIO()
        Image.new("RGB", (2000, 1000), "purple").save(source, format="WEBP")

        updated = self.service.store_image(
            "123", character["id"], source.getvalue(), "image/webp"
        )

        path = Path(updated["image_path"])
        self.assertTrue(path.is_file())
        with Image.open(path) as stored:
            self.assertEqual(stored.format, "PNG")
            self.assertLessEqual(max(stored.size), 1024)

    def test_invalid_json_and_image_are_rejected(self):
        character = self.service.save("123", sample_character())
        with self.assertRaises(CharacterError):
            self.service.import_json("123", b"not json")
        with self.assertRaises(CharacterError):
            self.service.store_image(
                "123", character["id"], b"not image", "image/png"
            )


class CharacterPdfTests(unittest.TestCase):
    def test_flattened_dnd_beyond_layout_is_structured(self):
        def block(x0, y0, text, x1=None, y1=None):
            return {
                "x0": x0, "y0": y0, "x1": x1 or x0 + 20,
                "y1": y1 or y0 + 8, "text": text,
            }

        first = [
            block(50, 60, "Flattened Hero"),
            block(270, 51, "Cleric 9 | Player"),
            block(270, 77, "Half-Elf | Acolyte | Milestone"),
            block(40, 149, "STRENGTH"), block(47, 157, "19"),
            block(47, 234, "14"), block(47, 310, "18"),
            block(47, 387, "14"), block(47, 464, "18"),
            block(47, 540, "12"),
            block(131, 134, "Strength"), block(117, 133, "+4"),
            block(131, 188, "Wisdom"), block(103, 187, "• | +8"),
            block(131, 304, "Acrobatics"), block(116, 303, "+2 | DEX"),
            block(247, 152, "+2 | 18"), block(433, 151, "91 | --"),
            block(234, 313, "+4"), block(238, 391, "30 ft. (Walking)"),
            block(227, 632, "Lightbringer | +9 | 1d8+5 Bludgeoning | +1d6 Radiant"),
        ]
        empty = {"text": "", "blocks": []}
        pages = [
            {"text": "summary", "blocks": first},
            {"text": "Divine Domain\nTempest Domain", "blocks": []},
            empty, empty,
            {"text": "spells", "blocks": [
                block(44, 153, "=== CANTRIPS === | At Will"),
                block(31, 164, "O Sacred Flame | Cleric | DEX 16 1A | 60 ft."),
            ]},
        ]

        payload = _flattened_pdf_payload(pages)

        self.assertEqual(payload["name"], "Flattened Hero")
        self.assertEqual(payload["classes"][0]["subclass"], "Tempest Domain")
        self.assertEqual(payload["saving_throws"]["wis"], "+8")
        self.assertEqual(payload["armor_class"], "18")
        self.assertEqual(payload["actions"][0]["damage_rolls"], ["1d8+5", "1d6"])
        self.assertEqual(payload["spells"][0]["save_ability"], "dex")

    def test_editable_pdf_fields_are_imported(self):
        fields = {
            "CharacterName": {"/V": "PDF Hero"},
            "ClassLevel": {"/V": "Wizard 5"},
            "STR": {"/V": "8"},
            "DEX": {"/V": "14"},
            "CON": {"/V": "12"},
            "INT": {"/V": "18"},
            "WIS": {"/V": "13"},
            "CHA": {"/V": "10"},
            "ProfBonus": {"/V": "+3"},
            "AC": {"/V": "15"},
            "HPMax": {"/V": "32"},
            "Arcana": {"/V": "+7"},
            "INTsave": {"/V": "+7"},
            "Wpn Name 1": {"/V": "Quarterstaff"},
            "Wpn1 AtkBonus": {"/V": "+2"},
            "Wpn1 Damage": {"/V": "1d6-1"},
        }
        reader = SimpleNamespace(
            is_encrypted=False,
            get_fields=lambda: fields,
            pages=[SimpleNamespace(extract_text=lambda: "Features and inventory")],
        )

        with patch("services.characterService.PdfReader", return_value=reader):
            character = character_from_pdf(b"%PDF-fake", "123")

        self.assertEqual(character["name"], "PDF Hero")
        self.assertEqual(character["abilities"]["int"], 18)
        self.assertEqual(character["skills"]["arcana"], 7)
        self.assertEqual(character["saving_throws"]["int"], 7)
        self.assertEqual(character["actions"][0]["name"], "Quarterstaff")
        self.assertEqual(character["actions"][0]["damage_rolls"], ["1d6-1"])

    def test_pdf_without_character_name_is_rejected(self):
        reader = SimpleNamespace(
            is_encrypted=False,
            get_fields=lambda: {},
            pages=[SimpleNamespace(extract_text=lambda: "Blank sheet")],
        )
        with patch("services.characterService.PdfReader", return_value=reader):
            with self.assertRaisesRegex(CharacterError, "character name"):
                character_from_pdf(b"%PDF-fake", "123")


if __name__ == "__main__":
    unittest.main()
