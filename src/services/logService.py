"""EyeBot logging with terminal, global, guild, rollover, and archives."""

from __future__ import annotations

import logging
import os
import re
import sys
import threading
import time
import zipfile
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path


_ROLLED_LOG = re.compile(r"^(\d{8}-\d{4})_.+\.txt(?:\.\d+)?$")
_ENTRY_TIME = re.compile(r"^\[(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})\]")
_ARCHIVE = re.compile(r"^\d{8}-\d{4}_30-day-archive\.zip$")
_LOCAL_ARCHIVE_LOCK = threading.Lock()


@contextmanager
def _folder_archive_lock(directory: Path):
    """Serialize folder archives across EyeBot processes where supported."""
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / ".archive.lock"
    with _LOCAL_ARCHIVE_LOCK:
        handle = lock_path.open("a+b")
        try:
            try:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            except ImportError:
                pass
            yield
        finally:
            try:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except ImportError:
                pass
            handle.close()


class EyeBotArchiveHandler(RotatingFileHandler):
    """Rename full logs by their final entry and create 30-day ZIP windows."""

    def __init__(
        self,
        filename,
        *,
        max_bytes: int,
        archive_days: int,
        archive_count: int,
    ):
        super().__init__(
            filename,
            maxBytes=max(1, int(max_bytes)),
            backupCount=0,
            encoding="utf-8",
        )
        self.archive_days = max(1, int(archive_days))
        self.archive_count = max(1, int(archive_count))
        self.last_entry_time: float | None = self._last_file_entry_time()
        # Apply overdue retention immediately on process start, even if the
        # active file does not roll again during this run.
        self._archive_completed_windows(Path(self.baseFilename).parent)

    def emit(self, record):
        super().emit(record)
        self.last_entry_time = record.created

    def _last_file_entry_time(self) -> float | None:
        path = Path(self.baseFilename)
        try:
            with path.open("rb") as handle:
                handle.seek(0, os.SEEK_END)
                position = handle.tell()
                block = b""
                while position > 0 and b"\n" not in block:
                    read_size = min(4096, position)
                    position -= read_size
                    handle.seek(position)
                    block = handle.read(read_size) + block
            lines = block.decode("utf-8", errors="replace").splitlines()
            match = _ENTRY_TIME.match(lines[-1]) if lines else None
            if match:
                parsed = time.strptime(match.group(1), "%Y/%m/%d %H:%M:%S")
                return time.mktime(parsed)
            return path.stat().st_mtime
        except (FileNotFoundError, OSError, ValueError):
            return None

    def _rollover_path(self, timestamp: float) -> Path:
        active = Path(self.baseFilename)
        stamp = time.strftime("%Y%m%d-%H%M", time.localtime(timestamp))
        candidate = active.with_name(f"{stamp}_{active.stem}.txt")
        sequence = 2
        while candidate.exists():
            candidate = active.with_name(f"{stamp}_{active.stem}.txt.{sequence}")
            sequence += 1
        return candidate

    def doRollover(self):
        if self.stream:
            self.stream.flush()
            self.stream.close()
            self.stream = None
        active = Path(self.baseFilename)
        if active.exists() and active.stat().st_size:
            timestamp = self.last_entry_time or self._last_file_entry_time() or time.time()
            active.replace(self._rollover_path(timestamp))
        if not self.delay:
            self.stream = self._open()
        self.last_entry_time = None
        self._archive_completed_windows(active.parent)

    def _archive_completed_windows(self, directory: Path) -> None:
        with _folder_archive_lock(directory):
            while True:
                backups = []
                for path in directory.iterdir():
                    match = _ROLLED_LOG.match(path.name)
                    if match and path.is_file():
                        timestamp = time.mktime(
                            time.strptime(match.group(1), "%Y%m%d-%H%M")
                        )
                        backups.append((timestamp, path))
                if not backups:
                    break
                backups.sort(key=lambda item: (item[0], item[1].name))
                window_start = backups[0][0]
                window_end = window_start + self.archive_days * 86400
                if time.time() < window_end:
                    break
                selected = [path for timestamp, path in backups if timestamp < window_end]
                archive_name = (
                    time.strftime("%Y%m%d-%H%M", time.localtime(window_start))
                    + "_30-day-archive.zip"
                )
                archive_path = directory / archive_name
                temporary = archive_path.with_suffix(".zip.tmp")
                with zipfile.ZipFile(
                    temporary, "w", compression=zipfile.ZIP_DEFLATED
                ) as archive:
                    for path in selected:
                        archive.write(path, arcname=path.name)
                temporary.replace(archive_path)
                for path in selected:
                    path.unlink()

            archives = sorted(
                (
                    path
                    for path in directory.iterdir()
                    if path.is_file() and _ARCHIVE.match(path.name)
                ),
                key=lambda path: path.name,
            )
            for path in archives[:-self.archive_count]:
                path.unlink()


class LogService:
    def __init__(self, name, config) -> None:
        self.name = str(name)
        self.config = dict(config)
        self.level = config.get("level", "INFO")
        self.max_bytes = max(1, int(config.get("max_bytes", 10_485_760)))
        self.archive_days = max(1, int(config.get("archive_days", 30)))
        self.archive_count = max(1, int(config.get("archive_count", 2)))
        self.guild_logs_enabled = bool(config.get("guild_logs_enabled", True))
        self.guild_directory = Path(
            config.get("guild_directory", "/app/data/logs/guilds")
        ).expanduser()
        self._guild_loggers: dict[str, logging.Logger] = {}

        self.formatter = logging.Formatter(
            datefmt="%Y/%m/%d %H:%M:%S",
            fmt="[%(asctime)s][%(levelname)s] %(name)s - %(message)s",
        )
        self.logger = logging.Logger(name=self.name, level=self.level)
        self.logger.propagate = False

        output = str(config.get("output", "terminal")).strip()
        mode = output.casefold()
        if mode in {"terminal", "stdout", "syslog", "both"}:
            terminal = logging.StreamHandler(sys.stdout)
            terminal.setFormatter(self.formatter)
            self.logger.addHandler(terminal)

        file_name = self._global_file_name(output, mode)
        if file_name:
            self.logger.addHandler(self._file_handler(Path(file_name)))

    def _global_file_name(self, output: str, mode: str) -> str:
        if mode == "both":
            if self.config.get("global_directory"):
                template = self.config.get("global_file", "{name}.txt")
                return str(Path(self.config["global_directory"]) / template).format(
                    name=self.name
                )
            return str(self.config.get("file", "output.log")).format(name=self.name)
        if mode in {"terminal", "stdout", "syslog"}:
            return ""
        return output.format(name=self.name)

    def _file_handler(self, path: Path) -> EyeBotArchiveHandler:
        path = path.expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = EyeBotArchiveHandler(
            path,
            max_bytes=self.max_bytes,
            archive_days=self.archive_days,
            archive_count=self.archive_count,
        )
        handler.setFormatter(self.formatter)
        return handler

    def _guild_logger(self, guild_id) -> logging.Logger | None:
        if not self.guild_logs_enabled:
            return None
        normalized = str(guild_id).strip()
        if not normalized.isdecimal():
            raise ValueError("Guild ID must contain only decimal digits")
        logger = self._guild_loggers.get(normalized)
        if logger is None:
            logger = logging.Logger(
                name=self.name,
                level=self.level,
            )
            logger.propagate = False
            template = str(self.config.get("guild_file", "{name}.txt"))
            file_name = template.format(name=self.name, platform=self.name)
            logger.addHandler(
                self._file_handler(self.guild_directory / normalized / file_name)
            )
            self._guild_loggers[normalized] = logger
        return logger

    def _write(self, level: int, message, guild_id=None) -> None:
        self.logger.log(level, msg=message)
        if guild_id is not None:
            guild_logger = self._guild_logger(guild_id)
            if guild_logger is not None:
                guild_logger.log(level, msg=message)

    def close(self):
        for logger in (self.logger, *self._guild_loggers.values()):
            for handler in tuple(logger.handlers):
                handler.flush()
                handler.close()
                logger.removeHandler(handler)
        self._guild_loggers.clear()

    def info(self, message, guild_id=None):
        self._write(logging.INFO, message, guild_id)

    def error(self, message, guild_id=None):
        self._write(logging.ERROR, message, guild_id)

    def warn(self, message, guild_id=None):
        self._write(logging.WARNING, message, guild_id)

    def log(self, message, guild_id=None):
        self._write(logging.DEBUG, message, guild_id)

    def warning(self, message, guild_id=None):
        self._write(logging.WARNING, message, guild_id)
