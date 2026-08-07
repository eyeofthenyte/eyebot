import ast
import random
import unittest
from pathlib import Path


LOOT_PATH = Path(__file__).resolve().parents[1] / "src/cogs/loot.py"
TREE = ast.parse(LOOT_PATH.read_text(encoding="utf-8"))
GENERATOR = next(
    node
    for node in TREE.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "generate_individual_loot"
)
MODULE = ast.Module(body=[GENERATOR], type_ignores=[])
ast.fix_missing_locations(MODULE)
NAMESPACE = {"random": random}
exec(compile(MODULE, str(LOOT_PATH), "exec"), NAMESPACE)
generate_individual_loot = NAMESPACE["generate_individual_loot"]


def lowest_value(start, stop):
    return start


class IndividualLootTableTests(unittest.TestCase):
    def assert_bucket(self, table, d100_values, currencies):
        for d100_roll in d100_values:
            with self.subTest(table=table, d100_roll=d100_roll):
                result = generate_individual_loot(
                    table,
                    d100_roll=d100_roll,
                    randrange=lowest_value,
                )
                self.assertEqual(result["d100_roll"], d100_roll)
                self.assertEqual(
                    tuple(value.split()[-1] for value in result["coins"]),
                    currencies,
                )
                self.assertIn("At the end of your job", result["response"])

    def test_table_one_boundaries(self):
        self.assert_bucket("1", (1, 30), ("CP",))
        self.assert_bucket("1", (31, 60), ("SP",))
        self.assert_bucket("1", (61, 70), ("EP",))
        self.assert_bucket("1", (71, 95), ("GP",))
        self.assert_bucket("1", (96, 100), ("PP",))

    def test_table_two_boundaries(self):
        self.assert_bucket("2", (1, 30), ("CP", "EP"))
        self.assert_bucket("2", (31, 60), ("SP", "GP"))
        self.assert_bucket("2", (61, 70), ("EP", "GP"))
        self.assert_bucket("2", (71, 95), ("GP",))
        self.assert_bucket("2", (96, 100), ("GP", "PP"))

    def test_table_three_boundaries(self):
        self.assert_bucket("3", (1, 20), ("SP", "GP"))
        self.assert_bucket("3", (21, 35), ("EP", "GP"))
        self.assert_bucket("3", (36, 75), ("GP", "PP"))
        self.assert_bucket("3", (76, 100), ("GP", "PP"))

    def test_table_four_boundaries(self):
        self.assert_bucket("4", (1, 15), ("EP", "GP"))
        self.assert_bucket("4", (16, 55), ("GP", "PP"))
        self.assert_bucket("4", (56, 100), ("GP", "PP"))

    def test_generated_values_use_expected_multipliers(self):
        self.assertEqual(
            generate_individual_loot(
                "2", d100_roll=1, randrange=lowest_value
            )["coins"],
            ("400 CP", "10 EP"),
        )
        self.assertEqual(
            generate_individual_loot(
                "4", d100_roll=1, randrange=lowest_value
            )["coins"],
            ("2000 EP", "800 GP"),
        )

    def test_rejects_invalid_table_and_d100(self):
        with self.assertRaisesRegex(ValueError, "between 1 and 4"):
            generate_individual_loot("5")
        with self.assertRaisesRegex(ValueError, "between 1 and 100"):
            generate_individual_loot("1", d100_roll=0)
        with self.assertRaisesRegex(ValueError, "between 1 and 100"):
            generate_individual_loot("1", d100_roll=101)


if __name__ == "__main__":
    unittest.main()
