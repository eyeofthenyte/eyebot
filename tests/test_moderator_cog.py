import ast
import unittest
from pathlib import Path


MODERATOR_PATH = Path("src/cogs/moderator.py")
MODERATOR_SOURCE = MODERATOR_PATH.read_text(encoding="utf-8")
MODERATOR_TREE = ast.parse(MODERATOR_SOURCE)


class ModeratorCogTests(unittest.TestCase):
    def test_set_group_exposes_required_subcommands(self):
        moderator = next(
            node
            for node in MODERATOR_TREE.body
            if isinstance(node, ast.ClassDef) and node.name == "Moderator"
        )
        commands = {
            keyword.value.value
            for method in moderator.body
            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
            for decorator in method.decorator_list
            if isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "command"
            for keyword in decorator.keywords
            if keyword.arg == "name" and isinstance(keyword.value, ast.Constant)
        }
        self.assertEqual(commands, {"modchannel", "gm", "privateroll", "admin", "mod"})

    def test_channel_and_role_selectors_are_native_discord_selects(self):
        self.assertIn("discord.ui.ChannelSelect", MODERATOR_SOURCE)
        self.assertIn("discord.ui.RoleSelect", MODERATOR_SOURCE)
        self.assertIn("discord.ui.UserSelect", MODERATOR_SOURCE)

    def test_private_channel_defaults_are_present(self):
        self.assertIn('name="mod-logs"', MODERATOR_SOURCE)
        self.assertIn('name="gm-rolls"', MODERATOR_SOURCE)
        self.assertIn("view_channel=False", MODERATOR_SOURCE)

    def test_legacy_prefix_setters_are_not_registered(self):
        clear_source = Path("src/cogs/clear.py").read_text(encoding="utf-8")
        roller_source = Path("src/cogs/roller.py").read_text(encoding="utf-8")
        self.assertNotIn('@commands.command(name="setmodchannel"', clear_source)
        self.assertNotIn('@commands.command(name="set_dm"', roller_source)
        self.assertNotIn("@commands.command()\n    async def privateroll", roller_source)

    def test_gm_storage_remains_roll_router_compatible(self):
        self.assertIn('"dm_role"', MODERATOR_SOURCE)
        self.assertIn('"dm_channel"', MODERATOR_SOURCE)


if __name__ == "__main__":
    unittest.main()
