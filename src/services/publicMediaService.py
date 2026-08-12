"""Temporary public media hosting for platform APIs that pull from HTTPS URLs."""

from __future__ import annotations

import asyncio
import os
import re
import time
from pathlib import Path
from urllib.parse import quote, urlparse

from services.mediaStagingService import MediaStagingService
from services.platformConfigService import validate_guild_id


SAFE_BATCH = re.compile(r"^[0-9a-f-]{36}$")
SAFE_FILENAME = re.compile(r"^[A-Za-z0-9_.-]{1,150}$")
DEFAULT_RETENTION_HOURS = 72
DEFAULT_CLEANUP_SECONDS = 3600
DEFAULT_GUILD_QUOTA_BYTES = 1_073_741_824


def _bounded_int(value, default, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return min(maximum, max(minimum, parsed))


class PublicMediaService:
    """Store validated media under isolated guild prefixes and return HTTPS URLs."""

    def __init__(self, config, guild_config_dir):
        settings = config.get("public_media", {}) if isinstance(config, dict) else {}
        gateway = config.get("gateway", {}) if isinstance(config, dict) else {}
        base_url = str(
            os.getenv("EYEBOT_PUBLIC_MEDIA_BASE_URL")
            or settings.get("public_base_url")
            or (str(gateway.get("public_base_url") or "").rstrip("/") + "/media")
        ).rstrip("/")
        configured_root = (
            os.getenv("EYEBOT_PUBLIC_MEDIA_DIR")
            or settings.get("storage_path")
            or str(Path(guild_config_dir).resolve().parent / "public_media")
        )
        self.enabled = settings.get("enabled") is True
        self.provider = str(settings.get("provider") or "local_caddy").casefold()
        self.public_base_url = base_url
        self.root = Path(configured_root).resolve()
        self.retention_seconds = 3600 * _bounded_int(
            settings.get("retention_hours"),
            DEFAULT_RETENTION_HOURS,
            1,
            24 * 30,
        )
        self.cleanup_seconds = _bounded_int(
            settings.get("cleanup_interval_seconds"),
            DEFAULT_CLEANUP_SECONDS,
            60,
            24 * 3600,
        )
        self.guild_quota_bytes = _bounded_int(
            settings.get("max_bytes_per_guild"),
            DEFAULT_GUILD_QUOTA_BYTES,
            5_000_000,
            1_099_511_627_776,
        )
        if self.enabled:
            if self.provider != "local_caddy":
                raise ValueError(
                    f"Public media provider {self.provider!r} is a documented "
                    "placeholder and is not implemented"
                )
            parsed_url = urlparse(self.public_base_url)
            if (
                parsed_url.scheme != "https"
                or not parsed_url.hostname
                or parsed_url.username
                or parsed_url.password
                or parsed_url.query
                or parsed_url.fragment
            ):
                raise ValueError("public_media.public_base_url must use HTTPS")
            if gateway.get("enabled") is not True:
                raise ValueError("Public media hosting requires gateway.enabled: true")
            self.root.mkdir(parents=True, exist_ok=True)
        self.staging = MediaStagingService(self.root)

    def _guild_usage(self, guild_id):
        guild_root = self.root / validate_guild_id(guild_id)
        total = 0
        if not guild_root.exists():
            return total
        for path in guild_root.rglob("*"):
            if path.is_file() and not path.is_symlink():
                try:
                    total += path.stat().st_size
                except OSError:
                    continue
        return total

    async def host_images(
        self,
        guild_id,
        attachments,
        *,
        alt_text="",
        output_content_type=None,
    ):
        if not self.enabled:
            raise ValueError(
                "Public media hosting is disabled; provide a stable public HTTPS media URL"
            )
        safe_guild_id = validate_guild_id(guild_id)
        declared_size = sum(int(getattr(item, "size", 0) or 0) for item in attachments)
        if self._guild_usage(safe_guild_id) + declared_size > self.guild_quota_bytes:
            raise ValueError("This server's temporary public-media quota would be exceeded")
        staged = await self.staging.stage_images(
            safe_guild_id,
            attachments,
            alt_text=alt_text,
            output_content_type=output_content_type,
        )
        if self._guild_usage(safe_guild_id) > self.guild_quota_bytes:
            self.remove(staged)
            raise ValueError("This server's temporary public-media quota was exceeded")
        hosted = []
        for item in staged:
            path = Path(item["path"]).resolve()
            relative = path.relative_to(self.root)
            url_path = "/".join(quote(part, safe="") for part in relative.parts)
            hosted.append({**item, "url": f"{self.public_base_url}/{url_path}"})
        return hosted

    def resolve(self, guild_id, batch, filename):
        safe_guild_id = validate_guild_id(guild_id)
        if not SAFE_BATCH.fullmatch(str(batch)) or not SAFE_FILENAME.fullmatch(str(filename)):
            raise ValueError("Invalid public-media path")
        path = (self.root / safe_guild_id / str(batch) / str(filename)).resolve()
        if self.root not in path.parents or path.is_symlink() or not path.is_file():
            raise FileNotFoundError("Public media not found")
        if time.time() - path.stat().st_mtime > self.retention_seconds:
            self.remove(({"path": str(path)},))
            raise FileNotFoundError("Public media expired")
        return path

    def remove(self, media):
        self.staging.remove(media)

    def cleanup_expired(self, *, now=None):
        if not self.root.exists():
            return 0
        cutoff = (time.time() if now is None else float(now)) - self.retention_seconds
        removed = 0
        for path in self.root.glob("*/*/*"):
            if path.is_symlink() or not path.is_file():
                continue
            try:
                if path.stat().st_mtime >= cutoff:
                    continue
            except OSError:
                continue
            self.remove(({"path": str(path)},))
            removed += 1
        for guild_root in self.root.iterdir():
            if guild_root.is_dir():
                try:
                    guild_root.rmdir()
                except OSError:
                    pass
        return removed

    async def cleanup_forever(self):
        while True:
            self.cleanup_expired()
            await asyncio.sleep(self.cleanup_seconds)
