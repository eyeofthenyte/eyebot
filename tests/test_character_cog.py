import ast
import unittest
from pathlib import Path


COG_PATH = Path(__file__).resolve().parents[1] / "src/cogs/character.py"
TREE = ast.parse(COG_PATH.read_text(encoding="utf-8"))
CHARACTER = next(
    node for node in TREE.body
    if isinstance(node, ast.ClassDef) and node.name == "Character"
)


def command_name(method):
    for decorator in method.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        function = decorator.func
        if isinstance(function, ast.Attribute) and function.attr == "command":
            for keyword in decorator.keywords:
                if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                    return keyword.value.value
            return method.name.replace("_", "-")
    return None


class CharacterCogStructureTests(unittest.TestCase):
    def test_complete_character_command_suite_is_registered(self):
        commands = {
            command_name(method)
            for method in CHARACTER.body
            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        expected = {
            "list", "template", "show", "import-pdf", "import-json", "create", "refresh",
            "nickname", "image", "post", "download", "delete", "check",
            "skill", "save", "action", "spell", "modifier", "action-add",
            "spell-add",
        }
        self.assertTrue(expected.issubset(commands))

    def test_roll_commands_reuse_the_bounded_roller(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn('self.bot.get_cog("Roll")', source)
        self.assertIn("roll_full_expression", source)
        self.assertNotIn("random.randint", source)

    def test_owner_scoped_autocomplete_and_confirmation_are_present(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn("self.service.list(interaction.user.id)", source)
        self.assertIn("DeleteCharacterView", source)
        self.assertIn("Only the character owner", source)

    def test_no_undocumented_dnd_beyond_endpoint_is_used(self):
        source = COG_PATH.read_text(encoding="utf-8")
        source += (COG_PATH.parents[1] / "services/characterService.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("character-service.dndbeyond.com", source)
        self.assertNotIn("aiohttp", source)
        self.assertNotIn("requests.get", source)


if __name__ == "__main__":
    unittest.main()
