import io
import logging
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from services.logService import LogService


class LogServiceTests(unittest.TestCase):
    def test_both_writes_terminal_and_named_file(self):
        with tempfile.TemporaryDirectory() as directory:
            terminal = io.StringIO()
            log_template = str(Path(directory) / "{name}.log")
            with patch("services.logService.sys.stdout", terminal):
                service = LogService(
                    "kick",
                    {
                        "level": "INFO",
                        "output": "both",
                        "file": log_template,
                        "max_bytes": 1024,
                        "backup_count": 2,
                    },
                )
                service.info("connected")
                service.close()

            self.assertIn("kick - connected", terminal.getvalue())
            self.assertIn(
                "kick - connected",
                (Path(directory) / "kick.log").read_text(encoding="utf-8"),
            )

    def test_legacy_filename_remains_file_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.log"
            service = LogService(
                "discord", {"level": "DEBUG", "output": str(path)}
            )
            service.error("failure")
            service.close()
            self.assertIn("discord - failure", path.read_text(encoding="utf-8"))

    def test_terminal_alias_does_not_create_file(self):
        terminal = io.StringIO()
        with patch("services.logService.sys.stdout", terminal):
            service = LogService(
                "gateway", {"level": "INFO", "output": "syslog"}
            )
            service.warning("warning")
            service.close()
        self.assertIn("gateway - warning", terminal.getvalue())

    def test_rollover_name_uses_last_entry_time(self):
        with tempfile.TemporaryDirectory() as directory:
            active = Path(directory) / "kick.txt"
            service = LogService(
                "kick",
                {
                    "level": "INFO",
                    "output": str(active),
                    "max_bytes": 80,
                    "archive_days": 30,
                    "archive_count": 2,
                },
            )
            first_time = time.mktime(time.strptime("2026-08-15 14:27", "%Y-%m-%d %H:%M"))
            first = logging.LogRecord(
                "kick", logging.INFO, "", 0, "first entry long enough to rotate", (), None
            )
            first.created = first_time
            service.logger.handle(first)
            second = logging.LogRecord(
                "kick", logging.INFO, "", 0, "second entry forces another file", (), None
            )
            second.created = first_time + 60
            service.logger.handle(second)
            service.close()

            self.assertTrue((Path(directory) / "20260815-1427_kick.txt").is_file())

    def test_guild_record_is_written_globally_and_per_guild(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service = LogService(
                "instagram",
                {
                    "level": "INFO",
                    "output": "both",
                    "global_directory": str(root / "global"),
                    "global_file": "{name}.txt",
                    "guild_logs_enabled": True,
                    "guild_directory": str(root / "guilds"),
                    "guild_file": "{platform}.txt",
                },
            )
            service.info("published", guild_id="225623840489734144")
            service.close()

            self.assertIn(
                "published",
                (root / "global" / "instagram.txt").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "published",
                (
                    root
                    / "guilds"
                    / "225623840489734144"
                    / "instagram.txt"
                ).read_text(encoding="utf-8"),
            )

    def test_completed_windows_are_archived_and_only_two_are_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service = LogService(
                "kick",
                {
                    "level": "INFO",
                    "output": str(root / "kick.txt"),
                    "archive_days": 30,
                    "archive_count": 2,
                },
            )
            handler = service.logger.handlers[0]
            now = time.time()
            for days_old, platform in ((100, "kick"), (95, "discord"), (65, "kick")):
                stamp = time.strftime(
                    "%Y%m%d-%H%M", time.localtime(now - days_old * 86400)
                )
                (root / f"{stamp}_{platform}.txt").write_text(
                    platform, encoding="utf-8"
                )
            old_archive = root / "20200101-0000_30-day-archive.zip"
            with zipfile.ZipFile(old_archive, "w") as archive:
                archive.writestr("old.txt", "old")

            handler._archive_completed_windows(root)
            service.close()

            archives = sorted(root.glob("*_30-day-archive.zip"))
            self.assertEqual(len(archives), 2)
            self.assertNotIn(old_archive, archives)
            archived_names = set()
            for path in archives:
                with zipfile.ZipFile(path) as archive:
                    archived_names.update(archive.namelist())
            self.assertTrue(any(name.endswith("_kick.txt") for name in archived_names))
            self.assertTrue(any(name.endswith("_discord.txt") for name in archived_names))


if __name__ == "__main__":
    unittest.main()
