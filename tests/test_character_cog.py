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

    def test_attachments_use_original_discord_cdn_instead_of_media_proxy(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn("attachment.read(use_cached=False)", source)
        self.assertIn("image.read(use_cached=False)", source)
        self.assertNotIn("read(use_cached=True)", source)

    def test_ephemeral_character_responses_expire_after_thirty_seconds(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn("EPHEMERAL_DELETE_AFTER = 30", source)
        self.assertNotRegex(source, r"ephemeral=True\s*\)")
        self.assertNotRegex(source, r"ephemeral=True,\s*\)")

    def test_show_command_posts_character_sheet_publicly(self):
        show = next(
            method
            for method in CHARACTER.body
            if isinstance(method, ast.AsyncFunctionDef) and method.name == "show"
        )
        source = ast.get_source_segment(COG_PATH.read_text(encoding="utf-8"), show)
        self.assertIn("_send_sheet", source)
        self.assertNotIn("ephemeral=True", source)

    def test_character_posts_use_named_webhook_with_character_avatar(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn('CHARACTER_WEBHOOK_NAME = "EyeBot Characters"', source)
        self.assertIn("webhook_channel.permissions_for(bot_member).manage_webhooks", source)
        self.assertIn('"username": username[:80]', source)
        self.assertIn('kwargs["avatar_url"] = avatar_url', source)
        self.assertIn("discord.AllowedMentions.none()", source)
        self.assertIn("await webhook.send(**kwargs)", source)

    def test_followup_expiration_is_compatible_with_discord_webhooks(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn("async def _send_ephemeral_followup", source)
        self.assertIn("wait=True", source)
        self.assertIn("asyncio.create_task", source)
        self.assertIn("await message.delete()", source)
        self.assertNotRegex(
            source,
            r"interaction\.followup\.send\([\s\S]{0,300}?delete_after=",
        )

    def test_imported_details_have_structured_markdown_sections(self):
        source = COG_PATH.read_text(encoding="utf-8")
        for label in ("Equipment", "Features & Traits", "Background", "Notes"):
            self.assertIn(f'label="{label}"', source)
        self.assertIn('f"# __{main_section}__\\n"', source)
        self.assertIn('f"## {str(subsection)[:100]}{suffix}\\n"', source)
        self.assertIn('f"  - **Quantity:** {item[\'quantity\']}"', source)
        self.assertNotIn('f"  - **Weight:** {item[\'weight\']}"', source)
        self.assertIn('lines.append(f"**{name}**")', source)
        self.assertIn('lines.append(f"**{feature_name}**")', source)
        self.assertIn('lines.append(f"  - {detail}")', source)
        self.assertIn('for detail in item.get("details") or []', source)


if __name__ == "__main__":
    unittest.main()
