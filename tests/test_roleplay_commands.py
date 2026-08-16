import ast
import unittest
from pathlib import Path


ROLEPLAY_PATH = Path(__file__).resolve().parents[1] / "src/cogs/roleplay.py"
TREE = ast.parse(ROLEPLAY_PATH.read_text(encoding="utf-8"))


def load_function(name):
    node = next(
        item for item in TREE.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name
    )
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"re": __import__("re")}
    exec(compile(module, str(ROLEPLAY_PATH), "exec"), namespace)
    return namespace[name]


private_lounge_name = load_function("private_lounge_name")
player_channel_name = load_function("player_channel_name")


class RoleplayCommandStructureTests(unittest.TestCase):
    def test_required_slash_subcommands_are_present(self):
        set_class = next(
            node for node in TREE.body
            if isinstance(node, ast.ClassDef) and node.name == "Roleplay"
        )
        methods = {
            node.name for node in set_class.body if isinstance(node, ast.AsyncFunctionDef)
        }
        self.assertTrue(
            {
                "modrole",
                "adminrole",
                "gmrole",
                "playerrole",
                "assign_player",
                "prompt_player_lounge",
                "open_gm_channel",
            }
            <= methods
        )

    def test_role_menu_has_no_cancel_button(self):
        source = ROLEPLAY_PATH.read_text(encoding="utf-8")
        self.assertNotIn('label="Cancel"', source)
        for label in ("Default", "Create", "Disable"):
            self.assertIn(f'label="{label}"', source)

    def test_player_and_lounge_prompts_have_yes_no_buttons(self):
        classes = {
            node.name: ast.get_source_segment(ROLEPLAY_PATH.read_text(encoding="utf-8"), node)
            for node in TREE.body if isinstance(node, ast.ClassDef)
        }
        for name in ("AddPlayerPrompt", "LoungePrompt"):
            self.assertIn('label="Yes"', classes[name])
            self.assertIn('label="No"', classes[name])


class PlayerChannelNameTests(unittest.TestCase):
    def test_expected_channel_names(self):
        self.assertEqual(player_channel_name("Alice", "notes"), "alice-notes")
        self.assertEqual(player_channel_name("Alice", "references"), "alice-references")
        self.assertEqual(player_channel_name("Alice", "private-rp"), "alice-private-rp")

    def test_names_are_sanitized_and_bounded(self):
        self.assertEqual(player_channel_name("Eye Of The Nyte!", "notes"), "eye-of-the-nyte-notes")
        self.assertLessEqual(len(player_channel_name("x" * 200, "references")), 100)
        self.assertLessEqual(len(private_lounge_name("x" * 200)), 100)


if __name__ == "__main__":
    unittest.main()
