"""Load, merge, migrate, and persist platform and Discord-guild config."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import threading
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path

import yaml

from services.configService import ConfigService
from services.platformSecretService import PlatformSecretService


PLATFORM_NAMES = (
    "discord",
    "twitch",
    "youtube",
    "facebook",
    "kick",
    "twitter",
    "bluesky",
    "tiktok",
    "instagram",
    "substack",
    "kofi",
)
GUILD_ID_PATTERN = re.compile(r"^[1-9][0-9]{0,19}$")


def deep_merge(base: Mapping, overlay: Mapping) -> dict:
    """Recursively merge mappings without modifying either input."""
    merged = deepcopy(dict(base))
    for key, value in overlay.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def validate_guild_id(guild_id: str | int) -> str:
    """Return a safe Discord snowflake string or reject it."""
    value = str(guild_id)
    if not GUILD_ID_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid Discord guild ID: {value!r}")
    return value


def resolve_discord_prefix(
    platform_service,
    message,
    default_prefix: str = "!",
) -> str:
    """Resolve a message prefix without creating or mutating guild state."""
    guild = getattr(message, "guild", None)
    if guild is None:
        return default_prefix
    guild_config = platform_service.discord_guilds().get(str(guild.id), {})
    prefix = guild_config.get("prefix", default_prefix)
    return prefix if isinstance(prefix, str) and prefix else default_prefix


class PlatformConfigService(ConfigService):
    """Own platform configuration and isolated Discord-guild YAML files."""

    def __init__(
        self,
        config_path: str,
        logger=None,
        *,
        guild_config_dir: str | None = None,
        secret_dir: str | None = None,
        master_key_file: str | None = None,
        master_key: str | bytes | None = None,
        legacy_roller_path: str | None = None,
        legacy_clear_path: str | None = None,
    ) -> None:
        super().__init__(config_path, logger)
        if not isinstance(self.config, dict):
            self.config = {}
        self.config.setdefault("discord", {})
        if not isinstance(self.config["discord"], dict):
            self.config["discord"] = {}

        self.guild_config_dir = Path(
            guild_config_dir
            or Path(config_path).resolve().parent / "data" / "guilds"
        )
        self.secret_service = PlatformSecretService(
            secret_dir or Path(config_path).resolve().parent / "data" / "secrets",
            master_key_file=master_key_file,
            master_key=master_key,
        )
        self._guild_lock = threading.RLock()
        self._guilds: dict[str, dict] = {}
        self._prepare_guild_directory()
        self._load_guild_files()

        had_embedded_guilds = "guilds" in self.config["discord"]
        embedded_guilds = self.config["discord"].pop("guilds", {})
        migrated = self._migrate_embedded_guilds(embedded_guilds)
        migrated |= self._migrate_legacy_guild_files(
            legacy_roller_path,
            legacy_clear_path,
        )
        if had_embedded_guilds:
            super().save()
        if migrated:
            self.save_discord_guilds()

    def _prepare_guild_directory(self) -> None:
        self.guild_config_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.guild_config_dir.chmod(0o700)
        except OSError:
            pass

    def platform(self, name: str) -> dict:
        value = self.config.setdefault(name, {})
        if not isinstance(value, dict):
            value = {}
            self.config[name] = value
        return value

    def discord_guilds(self) -> dict:
        """Return the in-memory guild map backed by individual YAML files."""
        return self._guilds

    def guild_path(self, guild_id: str | int) -> Path:
        return self.guild_config_dir / f"{validate_guild_id(guild_id)}.yaml"

    def ensure_discord_guild(
        self,
        guild_id: str,
        guild_name: str = "",
        default_prefix: str = "!",
    ) -> dict:
        safe_id = validate_guild_id(guild_id)
        guild = self._guilds.setdefault(safe_id, {})
        if not isinstance(guild, dict):
            guild = {}
            self._guilds[safe_id] = guild
        defaults = {
            "guild_name": guild_name,
            "prefix": default_prefix,
            "dm_channel": "UNSET",
            "dm_role": "UNSET",
            "mod_role": "UNSET",
            "admin_role": "UNSET",
            "player_role": "UNSET",
            "aliases": {},
            "user_channels": {},
            "mod_channel": "UNSET",
            "socialmedia_sources_channel": "UNSET",
            "timers": {},
        }
        for key, value in defaults.items():
            guild.setdefault(key, deepcopy(value))
        if guild_name:
            guild["guild_name"] = guild_name
        return guild

    def merged_with_global(self, global_config: Mapping) -> dict:
        platforms = deep_merge(
            self.config,
            self.secret_service.global_platforms(),
        )
        return deep_merge(global_config, platforms)

    def effective_guild_platform(
        self,
        guild_id: str | int,
        platform_name: str,
    ) -> dict:
        """Return platform-wide values merged with one guild's overrides."""
        safe_id = validate_guild_id(guild_id)
        global_secrets = self.secret_service.global_platforms().get(
            platform_name,
            {},
        )
        base = deep_merge(self.platform(platform_name), global_secrets)
        guild = self._guilds.get(safe_id, {})
        overrides = guild.get("platforms", {}) if isinstance(guild, dict) else {}
        selected = overrides.get(platform_name, {}) if isinstance(overrides, dict) else {}
        effective = deep_merge(
            base,
            selected if isinstance(selected, Mapping) else {},
        )
        guild_secrets = self.secret_service.guild_platforms(safe_id).get(
            platform_name,
            {},
        )
        effective = deep_merge(effective, guild_secrets)
        # Availability is a host-owner policy and cannot be overridden by a guild.
        if "available" in base:
            effective["available"] = base["available"]
        return effective

    def set_global_platform_value(self, platform_name: str, parameter: str, value) -> None:
        """Persist one connector-wide, bot-owner-controlled setting."""
        if platform_name not in PLATFORM_NAMES:
            raise ValueError(f"Unsupported platform: {platform_name}")
        self.platform(platform_name)[parameter] = deepcopy(value)
        self.save()

    def set_guild_platform_override(
        self,
        guild_id: str | int,
        platform_name: str,
        parameter: str,
        value,
    ) -> None:
        safe_id = validate_guild_id(guild_id)
        guild = self.ensure_discord_guild(safe_id)
        platforms = guild.setdefault("platforms", {})
        platform_overrides = platforms.setdefault(platform_name, {})
        platform_overrides[parameter] = deepcopy(value)
        self.save_discord_guild(safe_id)

    def clear_guild_platform_override(
        self,
        guild_id: str | int,
        platform_name: str,
        parameter: str,
    ) -> bool:
        """Remove one override, or every override when parameter is ``all``."""
        safe_id = validate_guild_id(guild_id)
        guild = self.ensure_discord_guild(safe_id)
        platforms = guild.setdefault("platforms", {})
        if parameter == "all":
            changed = platforms.pop(platform_name, None) is not None
        else:
            selected = platforms.get(platform_name, {})
            changed = isinstance(selected, dict) and parameter in selected
            if changed:
                del selected[parameter]
                if not selected:
                    platforms.pop(platform_name, None)
        if not platforms:
            guild.pop("platforms", None)
        if changed:
            self.save_discord_guild(safe_id)
        return changed

    def save_discord_guild(self, guild_id: str | int) -> None:
        safe_id = validate_guild_id(guild_id)
        guild = self._guilds.get(safe_id)
        if not isinstance(guild, dict):
            raise KeyError(f"Discord guild is not loaded: {safe_id}")
        self._atomic_write_guild(safe_id, guild)

    def save_discord_guilds(self) -> None:
        for guild_id in tuple(self._guilds):
            self.save_discord_guild(guild_id)

    def save(self) -> None:
        """Save platform-wide settings only; guilds have explicit writers."""
        self.platform("discord").pop("guilds", None)
        super().save()

    def _load_guild_files(self) -> None:
        for path in sorted(self.guild_config_dir.glob("*.yaml")):
            guild_id = path.stem
            if not GUILD_ID_PATTERN.fullmatch(guild_id):
                continue
            value = self._read_guild_yaml(path)
            if value is not None:
                self._guilds[guild_id] = value

    def _read_guild_yaml(self, path: Path) -> dict | None:
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if not isinstance(value, dict):
                raise ValueError("guild configuration must be a mapping")
            return value
        except (OSError, UnicodeError, yaml.YAMLError, ValueError) as error:
            backup = path.with_suffix(".yaml.bak")
            try:
                value = yaml.safe_load(backup.read_text(encoding="utf-8")) or {}
                if not isinstance(value, dict):
                    raise ValueError("guild backup must be a mapping")
                self._atomic_write_path(path, value, create_backup=False)
                if self.logger:
                    self.logger.info(f"Recovered guild config from {backup}")
                return value
            except (OSError, UnicodeError, yaml.YAMLError, ValueError):
                if self.logger:
                    self.logger.error(f"Failed to load guild config {path}: {error}")
                return None

    def _atomic_write_guild(self, guild_id: str, value: dict) -> None:
        with self._guild_lock:
            self._atomic_write_path(self.guild_path(guild_id), value)

    def _atomic_write_path(
        self,
        path: Path,
        value: dict,
        *,
        create_backup: bool = True,
    ) -> None:
        self._prepare_guild_directory()
        if create_backup and path.is_file():
            backup = path.with_suffix(".yaml.bak")
            shutil.copy2(path, backup)
            try:
                backup.chmod(0o600)
            except OSError:
                pass

        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.guild_config_dir,
            prefix=f".{path.stem}-",
            suffix=".tmp",
            text=True,
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as destination:
                yaml.safe_dump(value, destination, default_flow_style=False)
                destination.flush()
                os.fsync(destination.fileno())
            temporary_path.chmod(0o600)
            os.replace(temporary_path, path)
            try:
                path.chmod(0o600)
            except OSError:
                pass
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    @staticmethod
    def _read_json(path: str | None) -> dict:
        if not path or not os.path.isfile(path):
            return {}
        try:
            with open(path, encoding="utf-8") as source:
                value = json.load(source)
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _merge_migrated_guild(self, guild_id: str, legacy: Mapping) -> bool:
        try:
            safe_id = validate_guild_id(guild_id)
        except ValueError:
            return False
        current = self._guilds.get(safe_id, {})
        merged = deepcopy(dict(legacy))
        merged.update(deepcopy(current))
        if merged == current:
            return False
        self._guilds[safe_id] = merged
        return True

    def _migrate_embedded_guilds(self, embedded) -> bool:
        if not isinstance(embedded, Mapping):
            return False
        changed = False
        for guild_id, guild in embedded.items():
            if isinstance(guild, Mapping):
                changed |= self._merge_migrated_guild(str(guild_id), guild)
        return changed

    def _migrate_legacy_guild_files(
        self,
        roller_path: str | None,
        clear_path: str | None,
    ) -> bool:
        """Import legacy JSON values only when a destination value is absent."""
        changed = False
        roller = self._read_json(roller_path)
        for guild_id, legacy in roller.items():
            if not isinstance(legacy, dict):
                continue
            selected = {
                key: deepcopy(legacy[key])
                for key in (
                    "guild_name",
                    "dm_channel",
                    "dm_role",
                    "aliases",
                    "user_channels",
                )
                if key in legacy
            }
            changed |= self._merge_migrated_guild(str(guild_id), selected)

        clear = self._read_json(clear_path)
        mod_channels = clear.get("mod_channels", {})
        timers = clear.get("timers", {})
        if not isinstance(mod_channels, Mapping):
            mod_channels = {}
        if not isinstance(timers, Mapping):
            timers = {}
        for guild_id in set(mod_channels) | set(timers):
            selected = {}
            if guild_id in mod_channels:
                selected["mod_channel"] = mod_channels[guild_id]
            if guild_id in timers:
                selected["timers"] = deepcopy(timers[guild_id])
            changed |= self._merge_migrated_guild(str(guild_id), selected)

        discord_config = self.platform("discord")
        if "mod_channel_name" in clear and "mod_channel_name" not in discord_config:
            discord_config["mod_channel_name"] = clear["mod_channel_name"]
            super().save()
        return changed


def load_split_config(
    global_path: str | Path,
    platform_path: str | Path,
    logger=None,
    *,
    guild_config_dir: str | Path | None = None,
    secret_dir: str | Path | None = None,
    master_key_file: str | Path | None = None,
    master_key: str | bytes | None = None,
    legacy_roller_path: str | Path | None = None,
    legacy_clear_path: str | Path | None = None,
) -> tuple[dict, ConfigService, PlatformConfigService]:
    """Load global, platform, and per-guild layers into a runtime view."""
    global_service = ConfigService(str(global_path), logger)
    resolved_secret_dir = secret_dir or os.getenv("EYEBOT_SECRET_DIR")
    resolved_key_file = master_key_file or os.getenv("EYEBOT_MASTER_KEY_FILE")
    if resolved_key_file is None:
        local_key = Path(platform_path).resolve().parent / "secrets" / "eyebot_master_key"
        if local_key.is_file():
            resolved_key_file = local_key
    platform_service = PlatformConfigService(
        str(platform_path),
        logger,
        guild_config_dir=(str(guild_config_dir) if guild_config_dir else None),
        secret_dir=(str(resolved_secret_dir) if resolved_secret_dir else None),
        master_key_file=(str(resolved_key_file) if resolved_key_file else None),
        master_key=master_key,
        legacy_roller_path=(str(legacy_roller_path) if legacy_roller_path else None),
        legacy_clear_path=(str(legacy_clear_path) if legacy_clear_path else None),
    )
    guilds_before_defaults = deepcopy(platform_service.discord_guilds())
    default_prefix = global_service.get().get("prefix", "!") or "!"
    for guild_id, guild in tuple(platform_service.discord_guilds().items()):
        guild_name = guild.get("guild_name", "") if isinstance(guild, dict) else ""
        platform_service.ensure_discord_guild(
            guild_id,
            guild_name,
            default_prefix,
        )
    if guilds_before_defaults != platform_service.discord_guilds():
        platform_service.save_discord_guilds()
    merged = platform_service.merged_with_global(global_service.get())
    return merged, global_service, platform_service
