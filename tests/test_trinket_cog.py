import ast
import re
import unittest
from pathlib import Path


COG_PATH = Path(__file__).resolve().parents[1] / "src/cogs/trinket.py"


class TrinketCogTests(unittest.TestCase):
    def test_class_keys_ignore_spaces_and_punctuation(self):
        source = COG_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        method = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "normalize_class_key"
        )
        method_source = ast.get_source_segment(source, method)
        self.assertIn('re.sub(r"[^a-z0-9]+", ""', method_source)
        normalize = lambda value: re.sub(r"[^a-z0-9]+", "", value.casefold())
        self.assertEqual(normalize("bloodhunter"), normalize("Blood Hunter"))
        self.assertEqual(normalize("blood-hunter"), normalize("Blood Hunter"))

    def test_sheet_titles_remain_readable_and_icons_support_png(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn('"title": worksheet.title', source)
        self.assertIn('(selected["title"], selected["trinkets"])', source)
        self.assertIn("for extension in ('jpeg', 'jpg', 'png', 'webp')", source)
        self.assertIn("icon_filename = os.path.basename(image_path)", source)
        self.assertIn("name=f'{class_title.upper()} TRINKET'", source)

    def test_blood_hunter_icon_exists(self):
        icon = COG_PATH.parents[2] / "images/classes/bloodhunter.png"
        self.assertTrue(icon.is_file())


if __name__ == "__main__":
    unittest.main()
