import ast
import random
import re
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROLLER_PATH = Path(__file__).resolve().parents[1] / "src/cogs/roller.py"
SOURCE = ROLLER_PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


class FakeEmbed:
    def __init__(self, *, title, description, color):
        self.title = title
        self.description = description
        self.color = color
        self.fields = []
        self.footer = types.SimpleNamespace(text="")

    def add_field(self, *, name, value, inline):
        self.fields.append(
            types.SimpleNamespace(name=name, value=value, inline=inline)
        )

    def set_footer(self, *, text):
        self.footer = types.SimpleNamespace(text=text)


def load_roll_class():
    constants = {}
    for node in TREE.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id.startswith(
                ("MAX_", "MIN_", "SAFE_")
            ):
                constants[target.id] = ast.literal_eval(node.value)

    roll_class = next(
        node
        for node in TREE.body
        if isinstance(node, ast.ClassDef) and node.name == "Roll"
    )
    method_names = {
        "parse_dice_expression",
        "estimate_work_units",
        "validate_full_expression",
        "roll_die",
        "apply_keep_drop",
        "tokenize_expression",
        "roll_single_part",
        "roll_full_expression",
        "_truncate_text",
        "_format_roll_values",
        "_split_field_value",
        "_build_roll_embeds",
    }
    methods = [
        node
        for node in roll_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in method_names
    ]
    test_class = ast.ClassDef(
        name="TestRoll",
        bases=[],
        keywords=[],
        body=methods,
        decorator_list=[],
    )
    module = ast.Module(body=[test_class], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        **constants,
        "discord": types.SimpleNamespace(Embed=FakeEmbed),
        "random": random,
        "re": re,
    }
    exec(compile(module, str(ROLLER_PATH), "exec"), namespace)
    return namespace["TestRoll"], constants


Roll, LIMITS = load_roll_class()


class RollerValidationTests(unittest.TestCase):
    def setUp(self):
        self.roll = Roll()

    def assert_invalid(self, expression, message):
        with self.assertRaisesRegex(ValueError, message):
            self.roll.validate_full_expression(expression)

    def test_accepts_documented_upper_dice_bounds(self):
        self.assertEqual(
            self.roll.parse_dice_expression("100d10000")["sides"],
            10_000,
        )

    def test_parses_supported_modifiers(self):
        parsed = self.roll.parse_dice_expression("5d12k3r<3exadvi4")

        self.assertEqual(parsed["num"], 5)
        self.assertEqual(parsed["sides"], 12)
        self.assertEqual(parsed["keep_highest"], 3)
        self.assertEqual(parsed["reroll"], ("<", 3))
        self.assertTrue(parsed["explode"])
        self.assertTrue(parsed["advantage"])
        self.assertFalse(parsed["disadvantage"])
        self.assertEqual(parsed["repeat"], 4)

    def test_rejects_dice_count_and_side_bounds(self):
        self.assert_invalid("101d6", "Dice count")
        self.assert_invalid("1d1", "Die sides")
        self.assert_invalid("1d10001", "Die sides")

    def test_rejects_repeat_component_and_expression_bounds(self):
        self.assert_invalid("1d6i21", "Repeat count")
        self.assert_invalid("+".join(["1d6"] * 21), "at most 20 components")
        self.assert_invalid("1d6" + (" " * 200), "1-200 characters")

    def test_validates_keep_and_drop(self):
        self.assert_invalid("4d6k5", "Cannot keep")
        self.assert_invalid("4d6l4", "Cannot drop")
        self.assert_invalid("4d6k3l1", "cannot be combined")

    def test_validates_reroll_targets(self):
        self.assert_invalid("1d6r=7", "impossible")
        self.assert_invalid("1d6r<1", "must leave")
        self.assert_invalid("1d6r<7", "must leave")
        self.assert_invalid("1d6r>0", "must leave")
        self.assert_invalid("1d6r>6", "must leave")

    def test_rejects_excessive_workload_and_modifiers(self):
        self.assert_invalid("100d6exr=1", "workload")
        self.assert_invalid("1d6+1000001", "Flat modifiers")

    def test_rejects_malformed_operator_sequences(self):
        self.assert_invalid("1d6+", "operator sequence")
        self.assert_invalid("1d6++2", "operator sequence")

    def test_explosion_limit_allows_ten_bonus_rolls(self):
        original_randint = random.randint
        random.randint = lambda minimum, maximum: maximum
        try:
            rolls = self.roll.roll_die(6, explode=True)
        finally:
            random.randint = original_randint

        self.assertEqual(len(rolls), 11)


class RollerExecutionTests(unittest.TestCase):
    def setUp(self):
        self.roll = Roll()

    def roll_with(self, values, expression):
        with patch.object(random, "randint", side_effect=values):
            return self.roll.roll_full_expression(expression)

    def test_compound_roll_and_flat_modifier(self):
        total, details = self.roll_with([2, 5], "2d6+3")

        self.assertEqual(total, 10)
        self.assertEqual(details[0][1][0]["rolls"], [2, 5])
        self.assertEqual(details[1][1][0]["total"], 3)

    def test_keep_highest_and_drop_lowest(self):
        kept_total, _ = self.roll_with([1, 6, 4, 3], "4d6k3")
        dropped_total, _ = self.roll_with([1, 6, 4, 3], "4d6l1")

        self.assertEqual(kept_total, 13)
        self.assertEqual(dropped_total, 13)

    def test_advantage_and_disadvantage(self):
        advantage_total, advantage = self.roll_with([5, 15], "1d20adv")
        disadvantage_total, disadvantage = self.roll_with([5, 15], "1d20dis")

        self.assertEqual(advantage_total, 15)
        self.assertEqual(advantage[0][1][0]["tag"], "ADV")
        self.assertEqual(disadvantage_total, 5)
        self.assertEqual(disadvantage[0][1][0]["tag"], "DIS")

    def test_reroll_and_explosion(self):
        reroll_total, _ = self.roll_with([1, 4], "1d6r=1")
        explosion_total, explosion = self.roll_with([6, 6, 2], "1d6ex")

        self.assertEqual(reroll_total, 4)
        self.assertEqual(explosion_total, 14)
        self.assertEqual(explosion[0][1][0]["rolls"], [14])

    def test_repeat_rolls(self):
        total, details = self.roll_with([1, 2, 3], "1d6i3")

        self.assertEqual(total, 6)
        self.assertEqual(
            [detail["total"] for detail in details[0][1]],
            [1, 2, 3],
        )


class RollerEmbedSafetyTests(unittest.TestCase):
    def setUp(self):
        self.roll = Roll()
        self.context = types.SimpleNamespace(
            author=types.SimpleNamespace(name="Tester", nick=None)
        )

    def test_large_breakdown_is_paginated_within_safe_limits(self):
        details = []
        for index in range(20):
            repeats = [
                {"rolls": list(range(1, 101)), "total": 5_050}
                for _ in range(20)
            ]
            details.append(("+", repeats, f"100d100+{index}"))

        embeds = self.roll._build_roll_embeds(
            self.context,
            "+".join(["100d100"] * 20),
            2_020_000,
            details,
            0,
        )

        self.assertLessEqual(len(embeds), LIMITS["MAX_EMBEDS_PER_ROLL"])
        for embed in embeds:
            self.assertLessEqual(len(embed.title), LIMITS["SAFE_TITLE_LENGTH"])
            self.assertLessEqual(
                len(embed.description), LIMITS["SAFE_DESCRIPTION_LENGTH"]
            )
            self.assertLessEqual(
                len(embed.fields), LIMITS["SAFE_FIELDS_PER_EMBED"]
            )
            total_size = (
                len(embed.title)
                + len(embed.description)
                + len(embed.footer.text)
            )
            for field in embed.fields:
                self.assertLessEqual(
                    len(field.name), LIMITS["SAFE_FIELD_NAME_LENGTH"]
                )
                self.assertLessEqual(
                    len(field.value), LIMITS["SAFE_FIELD_VALUE_LENGTH"]
                )
                total_size += len(field.name) + len(field.value)
            self.assertLessEqual(
                total_size, LIMITS["SAFE_TOTAL_EMBED_LENGTH"]
            )
            self.assertIn("Final Total", embed.footer.text)

        rendered = "\n".join(
            field.value for embed in embeds for field in embed.fields
        )
        self.assertIn("dice omitted", rendered)
        self.assertIn("repeated rolls omitted", rendered)


if __name__ == "__main__":
    unittest.main()
