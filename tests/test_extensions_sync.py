import ast
import unittest
from pathlib import Path


SOURCE = Path("src/cogs/extensions.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


class ExtensionSyncTests(unittest.TestCase):
    def test_owner_sync_command_supports_global_and_guild_scopes(self):
        self.assertIn('scope: str = "global"', SOURCE)
        self.assertIn('self.bot.tree.copy_global_to(guild=ctx.guild)', SOURCE)
        self.assertIn('self.bot.tree.clear_commands(guild=ctx.guild)', SOURCE)
        self.assertIn('await self.sync_slash_commands(guild=ctx.guild)', SOURCE)

    def test_sync_helper_passes_optional_guild_to_discord(self):
        extensions = next(
            node
            for node in TREE.body
            if isinstance(node, ast.ClassDef) and node.name == "Extensions"
        )
        helper = next(
            node
            for node in extensions.body
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "sync_slash_commands"
        )
        calls = [
            node
            for node in ast.walk(helper)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "sync"
        ]
        self.assertEqual(len(calls), 1)
        guild_keyword = next(
            keyword for keyword in calls[0].keywords if keyword.arg == "guild"
        )
        self.assertIsInstance(guild_keyword.value, ast.Name)
        self.assertEqual(guild_keyword.value.id, "guild")


if __name__ == "__main__":
    unittest.main()
