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
            "list", "template", "show", "show-all", "import-pdf", "import-json", "create", "refresh",
            "nickname", "avatar", "image", "post", "download", "delete", "check",
            "skill", "save", "action", "spell", "modifier", "set",
            "container", "item",
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
        self.assertIn('kwargs["delete_after"] = EPHEMERAL_DELETE_AFTER', source)
        self.assertIn("self._delete_followup_after(message, EPHEMERAL_DELETE_AFTER)", source)

    def test_show_command_posts_character_sheet_ephemerally(self):
        show = next(
            method
            for method in CHARACTER.body
            if isinstance(method, ast.AsyncFunctionDef) and method.name == "show"
        )
        source = ast.get_source_segment(COG_PATH.read_text(encoding="utf-8"), show)
        self.assertIn("_send_sheet", source)
        self.assertIn("_send_section_pages", source)
        self.assertIn('selected_section = section.value if section else "summary"', source)
        self.assertEqual(source.count("ephemeral=True"), 2)

    def test_summary_displays_spellcasting_and_typed_proficiencies(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn('name="Spellcasting"', source)
        self.assertIn(
            'f"**Casting Modifier:** ({casting_ability.upper()}) "', source
        )
        self.assertIn(
            'f"**Spell DC:** {spellcasting.get(\'save_dc\', 0)}  |  "', source
        )
        self.assertIn(
            'f"**Spell Attack:** {signed(spellcasting.get(\'attack_bonus\', 0))}"',
            source,
        )
        self.assertIn('name="Proficiencies"', source)
        self.assertIn('f"  - {item[\'name\']} ({item[\'type\']})"', source)

    def test_show_all_posts_sections_in_requested_order(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn('app_commands.Choice(name="Skills (Skills & Saves)"', source)
        self.assertIn('app_commands.Choice(name="Feats (Features & Traits)"', source)
        expected = '(\n    "skills", "actions", "spells", "equipment", "features", "background", "notes"\n)'
        self.assertIn(expected, source)
        self.assertIn('@app_commands.command(name="show-all"', source)
        self.assertIn("for section in SHOW_ALL_SECTION_ORDER", source)
        show_all = next(
            method
            for method in CHARACTER.body
            if isinstance(method, ast.AsyncFunctionDef) and method.name == "show_all"
        )
        show_all_source = ast.get_source_segment(
            COG_PATH.read_text(encoding="utf-8"), show_all
        )
        self.assertIn("with_view=False", show_all_source)
        self.assertNotIn("CharacterView", show_all_source)
        self.assertNotIn("ephemeral=True", show_all_source)

    def test_skill_and_save_modifiers_have_clickable_roll_controls(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn("class CharacterSkillRollSelect", source)
        self.assertIn("class CharacterSaveRollSelect", source)
        self.assertIn('placeholder="Roll a skill check"', source)
        self.assertIn('placeholder="Roll a saving throw"', source)
        self.assertIn('f"{name.title()} ({signed(modifier)})"', source)
        self.assertIn('f"{ABILITY_NAMES[key]} ({signed(modifier)})"', source)
        self.assertIn("self.cog._roll_embed", source)
        self.assertIn('if self.section == "skills"', source)

    def test_typed_skill_roll_can_use_an_optional_controlling_stat(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn("@app_commands.choices(stat=STAT_CHOICES, mode=MODE_CHOICES)", source)
        self.assertIn("stat: app_commands.Choice[str] | None = None", source)
        self.assertIn("normal_ability = SKILL_ABILITIES.get(key)", source)
        self.assertIn("proficiency_contribution = skill_modifier - ability_modifier(", source)
        self.assertIn("ability_modifier(selected[\"abilities\"][stat.value])", source)
        self.assertIn('label = f"{key.title()} ({ABILITY_NAMES[stat.value]}) Check"', source)

    def test_only_skill_and_save_section_headings_are_underlined(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn(
            'f"  - {name.title()} ({SKILL_ABILITIES.get(name, \'???\').title()}): "',
            source,
        )
        self.assertIn(
            'f"  - {ABILITY_NAMES[key]} ({key.title()}): {signed(value)}"', source
        )
        self.assertNotIn('**__{name.title()}:__**', source)
        self.assertNotIn('**__{ABILITY_NAMES[key]}:__**', source)
        self.assertIn('("__Skills__"', source)
        self.assertIn('("__Saving Throws__"', source)

    def test_action_rolls_have_clickable_controls_and_typed_damage(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn("class CharacterActionAttackSelect", source)
        self.assertIn("class CharacterActionDamageSelect", source)
        self.assertIn('placeholder="Roll an action attack"', source)
        self.assertIn('placeholder="Roll action damage"', source)
        self.assertIn("self.cog._damage_roll_embed", source)
        self.assertIn('details.append(f"- **Attack:**', source)
        self.assertIn('details.append(f"  - **Damage:** `{roll}`{suffix}")', source)
        self.assertIn('elif self.section == "actions"', source)

    def test_character_posts_use_named_webhook_with_character_avatar(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn('CHARACTER_WEBHOOK_NAME = "EyeBot Characters"', source)
        self.assertIn("webhook_channel.permissions_for(bot_member).manage_webhooks", source)
        self.assertIn('"username": username[:80]', source)
        self.assertIn('kwargs["avatar_url"] = avatar_url', source)
        self.assertIn("discord.AllowedMentions.none()", source)
        self.assertIn("await webhook.send(**kwargs)", source)
        self.assertIn("self._webhook_avatar_lock = asyncio.Lock()", source)
        self.assertIn("async with self._webhook_avatar_lock", source)
        self.assertIn("avatar=Path(avatar_path).read_bytes()", source)

    def test_successful_character_post_has_no_ephemeral_confirmation(self):
        tree = ast.parse(COG_PATH.read_text(encoding="utf-8"))
        post = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "post"
        )
        post_source = ast.get_source_segment(
            COG_PATH.read_text(encoding="utf-8"), post
        )
        self.assertIn("await webhook.send(**kwargs)", post_source)
        self.assertIn("await interaction.delete_original_response()", post_source)
        self.assertNotIn("✅ Posted as", post_source)
        self.assertNotIn("_send_ephemeral_followup", post_source)

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
        self.assertIn('quantity_text = f" x {quantity}"', source)
        self.assertNotIn('f"  - **Weight:** {item[\'weight\']}"', source)
        self.assertIn('lines.append(f"**{name}**")', source)
        self.assertIn('lines.append(f"**{feature_name}**")', source)
        self.assertIn('lines.append(f"  - {detail}")', source)
        self.assertIn('for detail in item.get("details") or []', source)
        self.assertIn('f"**{name}:** {_plain(detail or \'NONE\'', source)
        self.assertIn('lines = ["**BLANK**"]', source)

    def test_character_sections_and_equipment_are_editable(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn('name="add"', source)
        self.assertIn('@add.command(name="container"', source)
        self.assertIn('@add.command(name="item"', source)
        self.assertIn('@app_commands.command(name="set"', source)
        self.assertIn("subsection=subsection_autocomplete", source)
        self.assertIn("container=container_autocomplete", source)

    def test_proficiencies_can_be_added_and_removed(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn('remove = app_commands.Group(', source)
        self.assertIn('@add.command(name="proficiency"', source)
        self.assertIn('@remove.command(name="proficiency"', source)
        self.assertIn("proficiency_type=PROFICIENCY_TYPE_CHOICES", source)
        self.assertIn("proficiency=proficiency_autocomplete", source)
        self.assertIn('proficiencies.append({"name": name, "type": proficiency_type.value})', source)
        self.assertIn("del proficiencies[index]", source)
        self.assertIn("That proficiency is already recorded", source)

    def test_features_can_be_added_removed_and_edited(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn('edit = app_commands.Group(', source)
        self.assertIn('@add.command(name="feature"', source)
        self.assertIn('@remove.command(name="feature"', source)
        self.assertIn('@edit.command(name="feature"', source)
        self.assertIn("feature_type=FEATURE_TYPE_CHOICES", source)
        self.assertIn("feature=feature_autocomplete", source)
        self.assertIn('features.append({"name": name, "details": detail_lines})', source)
        self.assertIn("detail_lines = self._feature_detail_lines(details)", source)
        self.assertIn("del features[index]", source)
        self.assertIn('item["name"] = name', source)
        self.assertIn('item["details"] = detail_lines', source)

    def test_feature_detail_lines_render_as_markdown_bullets(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn('for line in str(details or "").splitlines()', source)
        self.assertIn('lines.append(f"  - {_plain(detail, 2800)}")', source)

    def test_all_addable_entry_types_have_edit_and_remove_commands(self):
        source = COG_PATH.read_text(encoding="utf-8")
        for entry_type in ("container", "item", "proficiency", "feature", "action", "spell"):
            self.assertIn(f'@edit.command(name="{entry_type}"', source)
            self.assertIn(f'@remove.command(name="{entry_type}"', source)
        self.assertIn("item=equipment_item_autocomplete", source)
        self.assertIn("action=action_entry_autocomplete", source)
        self.assertIn("spell=spell_entry_autocomplete", source)
        self.assertIn("Remove the items from that container before removing it.", source)
        self.assertIn('selected_item["quantity"] = quantity', source)
        self.assertIn('item.update({"name": new_name, "type": new_type})', source)
        self.assertIn('item["damage_rolls"] = rolls', source)
        self.assertIn('item["save_dc"] = save_dc', source)

    def test_backstory_and_note_entries_have_command_parity(self):
        source = COG_PATH.read_text(encoding="utf-8")
        for entry_type in ("backstory", "organization", "ally", "enemy", "other-note"):
            self.assertIn(f'@add.command(name="{entry_type}"', source)
            self.assertIn(f'@edit.command(name="{entry_type}"', source)
            self.assertIn(f'@remove.command(name="{entry_type}"', source)
        self.assertIn('selected["sections"]["Notes"]["Backstory"] = "NONE"', source)
        self.assertIn("organization_autocomplete", source)
        self.assertIn("ally_autocomplete", source)
        self.assertIn("enemy_autocomplete", source)
        self.assertIn("other_note_autocomplete", source)

    def test_equipment_items_support_optional_gp_values(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn("gp_value: app_commands.Range[float, 0, 1000000000]", source)
        self.assertIn('"gp_value": gp_value', source)
        self.assertIn('selected_item["gp_value"] = gp_value', source)
        self.assertIn("f\" — {gp_value:g} gp\"", source)

    def test_avatar_and_gallery_commands_are_separate(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn('@app_commands.command(name="avatar"', source)
        self.assertIn('@app_commands.command(name="image", description="Display character gallery images")', source)
        for operation in ("add", "edit", "remove"):
            self.assertIn(f'@{operation}.command(name="avatar"', source)
            self.assertIn(f'@{operation}.command(name="image"', source)
        self.assertIn("slot: app_commands.Range[int, 1, 4]", source)
        self.assertIn("embed.set_thumbnail", source)
        self.assertIn("embed.set_image", source)
        self.assertIn("self.service.store_avatar", source)
        self.assertIn("self.service.store_gallery_image", source)
        self.assertIn("self.service.remove_gallery_image", source)
        self.assertNotIn("Character images must be no larger than", source)

    def test_actions_and_spells_use_the_add_command_group(self):
        source = COG_PATH.read_text(encoding="utf-8")
        self.assertIn('@add.command(name="action"', source)
        self.assertIn('@add.command(name="spell"', source)
        self.assertNotIn('@app_commands.command(name="action-add"', source)
        self.assertNotIn('@app_commands.command(name="spell-add"', source)


if __name__ == "__main__":
    unittest.main()
