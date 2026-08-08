import ast
import unittest
from pathlib import Path


class SocialReactionConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path("src/cogs/social.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        assignments = {
            node.targets[0].id: ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in {"REACTION_PLATFORMS", "CANCEL_REACTION"}
        }
        cls.platforms = assignments["REACTION_PLATFORMS"]
        cls.cancel = assignments["CANCEL_REACTION"]

    def test_reaction_destinations_include_supported_platforms(self):
        self.assertEqual(
            set(self.platforms.values()),
            {"twitter", "facebook", "bluesky", "instagram", "tiktok", "all"},
        )

    def test_kofi_is_not_a_reaction_destination(self):
        self.assertNotIn("kofi", self.platforms.values())

    def test_cancel_reaction_is_separate_from_destinations(self):
        self.assertEqual(self.cancel, "❌")
        self.assertNotIn(self.cancel, self.platforms)


if __name__ == "__main__":
    unittest.main()
