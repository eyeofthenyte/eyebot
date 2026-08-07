import tempfile
import unittest
from pathlib import Path

import yaml

from services.configService import ConfigService


class FakeLogger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(("info", message))

    def error(self, message):
        self.messages.append(("error", message))

    def warn(self, message):
        self.messages.append(("warning", message))


class ConfigServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)
        self.config_path = self.directory / "config.yaml"
        self.logger = FakeLogger()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_yaml(self, path, value):
        path.write_text(yaml.safe_dump(value), encoding="utf-8")

    def read_yaml(self, path):
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_loads_valid_config_and_creates_backup(self):
        expected = {"prefix": "!", "discord": {"bot_token": "test"}}
        self.write_yaml(self.config_path, expected)

        service = ConfigService(str(self.config_path), self.logger)

        self.assertEqual(service.get(), expected)
        backups = list(self.directory.glob("backup-*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(self.read_yaml(backups[0]), expected)

    def test_set_and_save_round_trip(self):
        service = ConfigService(str(self.config_path), self.logger)
        expected = {"prefix": "?", "logging": {"level": "INFO"}}

        returned = service.set(expected)
        service.save()

        self.assertIs(returned, service)
        self.assertEqual(self.read_yaml(self.config_path), expected)

    def test_recovers_corrupted_config_from_backup(self):
        expected = {"prefix": "$", "discord": {"bot_token": "recovered"}}
        self.config_path.write_text("prefix: [unterminated", encoding="utf-8")
        self.write_yaml(self.directory / "backup-2026-01-01.bak", expected)

        service = ConfigService(str(self.config_path), self.logger)

        self.assertEqual(service.get(), expected)
        self.assertEqual(self.read_yaml(self.config_path), expected)
        self.assertTrue(
            any(
                level == "info" and "Recovery from backup successful" in message
                for level, message in self.logger.messages
            )
        )

    def test_corruption_without_backup_fails_safely(self):
        self.config_path.write_text("prefix: [unterminated", encoding="utf-8")

        service = ConfigService(str(self.config_path), self.logger)

        self.assertEqual(service.get(), {})
        self.assertTrue(
            any(
                level == "error" and "Recovery failed" in message
                for level, message in self.logger.messages
            )
        )

    def test_removes_old_backup_after_successful_load(self):
        expected = {"prefix": "!"}
        self.write_yaml(self.config_path, expected)
        old_backup = self.directory / "backup-2000-01-01.bak"
        self.write_yaml(old_backup, {"prefix": "old"})

        ConfigService(str(self.config_path), self.logger)

        self.assertFalse(old_backup.exists())
        self.assertEqual(len(list(self.directory.glob("backup-*.bak"))), 1)


if __name__ == "__main__":
    unittest.main()
