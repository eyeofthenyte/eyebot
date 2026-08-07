import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import yaml

from services.platformConfigService import (
    PlatformConfigService,
    load_split_config,
    resolve_discord_prefix,
)


class PlatformConfigServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.global_path = self.root / "config.yaml"
        self.platform_path = self.root / "platforms.yaml"
        self.guild_dir = self.root / "data" / "guilds"

    def tearDown(self):
        self.temp.cleanup()

    def write_yaml(self, path, value):
        path.write_text(yaml.safe_dump(value), encoding="utf-8")

    def test_split_files_merge_into_backward_compatible_runtime_view(self):
        self.write_yaml(
            self.global_path,
            {"prefix": "!", "logging": {"level": "INFO"}},
        )
        self.write_yaml(
            self.platform_path,
            {
                "discord": {"enabled": True, "bot_token": "secret"},
                "twitch": {"enabled": False},
            },
        )

        merged, _global, platforms = load_split_config(
            self.global_path,
            self.platform_path,
        )

        self.assertEqual(merged["prefix"], "!")
        self.assertEqual(merged["discord"]["bot_token"], "secret")
        self.assertFalse(merged["twitch"]["enabled"])
        self.assertEqual(platforms.discord_guilds(), {})

    def test_migrates_both_legacy_guild_json_files(self):
        roller_path = self.root / "roller.json"
        clear_path = self.root / "clear.json"
        roller_path.write_text(
            json.dumps(
                {
                    "42": {
                        "guild_name": "Campaign",
                        "dm_channel": "100",
                        "dm_role": "DM",
                        "aliases": {"attack": {"expression": "1d20+5"}},
                        "user_channels": {"7": "101"},
                    }
                }
            ),
            encoding="utf-8",
        )
        clear_path.write_text(
            json.dumps(
                {
                    "mod_channel_name": "audit-log",
                    "mod_channels": {"42": 102},
                    "timers": {
                        "42": {
                            "103": {
                                "interval_minutes": 30,
                                "expires_at": None,
                                "start_time": "2026-01-01T00:00:00",
                            }
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

        service = PlatformConfigService(
            str(self.platform_path),
            legacy_roller_path=str(roller_path),
            legacy_clear_path=str(clear_path),
        )
        guild = service.discord_guilds()["42"]

        self.assertEqual(guild["guild_name"], "Campaign")
        self.assertEqual(guild["dm_channel"], "100")
        self.assertEqual(guild["mod_channel"], 102)
        self.assertEqual(guild["timers"]["103"]["interval_minutes"], 30)
        self.assertEqual(
            service.platform("discord")["mod_channel_name"],
            "audit-log",
        )
        self.assertTrue(self.platform_path.is_file())

    def test_existing_platform_values_win_over_legacy_json(self):
        self.write_yaml(
            self.platform_path,
            {
                "discord": {
                    "guilds": {
                        "42": {
                            "dm_channel": "current",
                            "aliases": {},
                        }
                    }
                }
            },
        )
        roller_path = self.root / "roller.json"
        roller_path.write_text(
            json.dumps(
                {
                    "42": {
                        "dm_channel": "legacy",
                        "aliases": {"old": {"expression": "1d6"}},
                    }
                }
            ),
            encoding="utf-8",
        )

        service = PlatformConfigService(
            str(self.platform_path),
            legacy_roller_path=str(roller_path),
        )

        guild = service.discord_guilds()["42"]
        self.assertEqual(guild["dm_channel"], "current")
        self.assertEqual(guild["aliases"], {})

    def test_guild_updates_persist_only_to_its_guild_file(self):
        self.write_yaml(self.global_path, {"prefix": "?"})
        self.write_yaml(self.platform_path, {"discord": {"guilds": {}}})
        service = PlatformConfigService(str(self.platform_path))
        guild = service.ensure_discord_guild("42", "Campaign")
        guild["dm_role"] = "Game Master"
        guild["timers"]["99"] = {"interval_minutes": 15}
        service.save_discord_guild("42")

        saved_platforms = yaml.safe_load(
            self.platform_path.read_text(encoding="utf-8")
        )
        self.assertNotIn("guilds", saved_platforms["discord"])
        saved = yaml.safe_load(
            (self.guild_dir / "42.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            saved["dm_role"],
            "Game Master",
        )
        self.assertEqual(
            saved["timers"]["99"]["interval_minutes"],
            15,
        )
        self.assertEqual(
            yaml.safe_load(self.global_path.read_text(encoding="utf-8")),
            {"prefix": "?"},
        )

    def test_platform_file_recovers_from_its_own_backup_namespace(self):
        self.platform_path.write_text(
            "discord: [unterminated",
            encoding="utf-8",
        )
        backup = self.root / "platforms-backup-2026-01-01.bak"
        self.write_yaml(
            backup,
            {"discord": {"enabled": True, "guilds": {}}},
        )

        service = PlatformConfigService(str(self.platform_path))

        self.assertTrue(service.platform("discord")["enabled"])
        restored = yaml.safe_load(
            self.platform_path.read_text(encoding="utf-8")
        )
        self.assertTrue(restored["discord"]["enabled"])

    def test_guild_prefix_defaults_and_resolves_per_server(self):
        self.write_yaml(self.platform_path, {"discord": {"guilds": {}}})
        service = PlatformConfigService(str(self.platform_path))
        guild = service.ensure_discord_guild(
            "42",
            "Campaign",
            default_prefix="!",
        )
        self.assertEqual(guild["prefix"], "!")

        guild_message = SimpleNamespace(guild=SimpleNamespace(id=42))
        dm_message = SimpleNamespace(guild=None)
        self.assertEqual(
            resolve_discord_prefix(service, guild_message, "!"),
            "!",
        )
        self.assertEqual(resolve_discord_prefix(service, dm_message, "!"), "!")

        guild["prefix"] = "?"
        service.ensure_discord_guild("42", "Campaign", default_prefix="!")
        self.assertEqual(
            resolve_discord_prefix(service, guild_message, "!"),
            "?",
        )

    def test_embedded_guilds_are_migrated_and_removed_from_platforms(self):
        self.write_yaml(
            self.platform_path,
            {"discord": {"enabled": True, "guilds": {"42": {"prefix": "?"}}}},
        )

        service = PlatformConfigService(str(self.platform_path))

        self.assertEqual(service.discord_guilds()["42"]["prefix"], "?")
        saved_platforms = yaml.safe_load(
            self.platform_path.read_text(encoding="utf-8")
        )
        self.assertNotIn("guilds", saved_platforms["discord"])
        self.assertTrue((self.guild_dir / "42.yaml").is_file())

    def test_invalid_guild_id_cannot_escape_storage_directory(self):
        service = PlatformConfigService(str(self.platform_path))

        with self.assertRaises(ValueError):
            service.ensure_discord_guild("../../platforms", "Unsafe")

    def test_corrupt_guild_file_recovers_from_its_backup(self):
        service = PlatformConfigService(str(self.platform_path))
        guild = service.ensure_discord_guild("42", "Campaign", "!")
        service.save_discord_guild("42")
        guild["prefix"] = "?"
        service.save_discord_guild("42")
        (self.guild_dir / "42.yaml").write_text(
            "prefix: [unterminated",
            encoding="utf-8",
        )

        recovered = PlatformConfigService(str(self.platform_path))

        self.assertEqual(recovered.discord_guilds()["42"]["prefix"], "!")
        restored = yaml.safe_load(
            (self.guild_dir / "42.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(restored["prefix"], "!")


if __name__ == "__main__":
    unittest.main()
