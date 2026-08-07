"""Encrypted global and per-guild platform-secret persistence."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import threading
from copy import deepcopy
from pathlib import Path

import yaml
from cryptography.fernet import Fernet, InvalidToken

from core.platform_secret_schema import validate_secret_name


GUILD_ID_PATTERN = re.compile(r"^[1-9][0-9]{0,19}$")
MAX_SECRET_BYTES = 65_536


def validate_secret_guild_id(guild_id: str | int) -> str:
    value = str(guild_id)
    if not GUILD_ID_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid Discord guild ID: {value!r}")
    return value


class PlatformSecretService:
    """Store encrypted secret mappings without exposing plaintext on disk."""

    def __init__(
        self,
        secret_dir: str | Path,
        *,
        master_key_file: str | Path | None = None,
        master_key: str | bytes | None = None,
    ) -> None:
        self.secret_dir = Path(secret_dir)
        self.guild_secret_dir = self.secret_dir / "guilds"
        self.master_key_file = Path(master_key_file) if master_key_file else None
        self._lock = threading.RLock()
        key = self._resolve_key(master_key)
        self.available = key is not None
        self._fernet = Fernet(key) if key is not None else None
        if not self.available and self._encrypted_files_exist():
            raise RuntimeError(
                "Encrypted platform secrets exist, but no EyeBot master key "
                "was provided. Set EYEBOT_MASTER_KEY_FILE or EYEBOT_MASTER_KEY."
            )

    def _resolve_key(self, provided: str | bytes | None) -> bytes | None:
        value = provided
        if value is None:
            value = os.getenv("EYEBOT_MASTER_KEY")
        if value is None and self.master_key_file and self.master_key_file.is_file():
            value = self.master_key_file.read_bytes()
        if value is None:
            return None
        key = value.encode("ascii") if isinstance(value, str) else value
        return key.strip()

    def _encrypted_files_exist(self) -> bool:
        if (self.secret_dir / "global.secrets").is_file():
            return True
        return self.guild_secret_dir.is_dir() and any(
            self.guild_secret_dir.glob("*.secrets")
        )

    @staticmethod
    def generate_key_file(path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            destination.parent.chmod(0o700)
        except OSError:
            pass
        descriptor = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(Fernet.generate_key() + b"\n")
                output.flush()
                os.fsync(output.fileno())
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return destination

    def global_platforms(self) -> dict:
        return self._read_mapping(self.secret_dir / "global.secrets")

    def guild_platforms(self, guild_id: str | int) -> dict:
        return self._read_mapping(self.guild_path(guild_id))

    def guild_path(self, guild_id: str | int) -> Path:
        return self.guild_secret_dir / f"{validate_secret_guild_id(guild_id)}.secrets"

    def set_secret(
        self,
        platform: str,
        parameter: str,
        value: str,
        *,
        guild_id: str | int | None = None,
    ) -> None:
        selected_platform, selected_parameter = validate_secret_name(
            platform,
            parameter,
        )
        if not isinstance(value, str) or not value:
            raise ValueError("Secret values cannot be empty")
        if len(value.encode("utf-8")) > MAX_SECRET_BYTES:
            raise ValueError(f"Secret exceeds the {MAX_SECRET_BYTES}-byte limit")
        path = (
            self.guild_path(guild_id)
            if guild_id is not None
            else self.secret_dir / "global.secrets"
        )
        mapping = self._read_mapping(path)
        mapping.setdefault(selected_platform, {})[selected_parameter] = value
        self._write_mapping(path, mapping)

    def delete_secret(
        self,
        platform: str,
        parameter: str,
        *,
        guild_id: str | int | None = None,
    ) -> bool:
        selected_platform, selected_parameter = validate_secret_name(
            platform,
            parameter,
        )
        path = (
            self.guild_path(guild_id)
            if guild_id is not None
            else self.secret_dir / "global.secrets"
        )
        mapping = self._read_mapping(path)
        selected = mapping.get(selected_platform, {})
        if selected_parameter not in selected:
            return False
        del selected[selected_parameter]
        if not selected:
            mapping.pop(selected_platform, None)
        if mapping:
            self._write_mapping(path, mapping)
        else:
            path.unlink(missing_ok=True)
            path.with_suffix(".secrets.bak").unlink(missing_ok=True)
        return True

    def list_secret_names(self, *, guild_id: str | int | None = None) -> dict:
        path = (
            self.guild_path(guild_id)
            if guild_id is not None
            else self.secret_dir / "global.secrets"
        )
        mapping = self._read_mapping(path)
        return {
            platform: tuple(sorted(parameters))
            for platform, parameters in sorted(mapping.items())
            if isinstance(parameters, dict)
        }

    def _read_mapping(self, path: Path) -> dict:
        if not path.is_file():
            return {}
        self._require_key()
        try:
            plaintext = self._fernet.decrypt(path.read_bytes())
            value = yaml.safe_load(plaintext.decode("utf-8")) or {}
            if not isinstance(value, dict):
                raise ValueError("decrypted secret data must be a mapping")
            return deepcopy(value)
        except (InvalidToken, OSError, UnicodeError, yaml.YAMLError, ValueError) as error:
            backup = path.with_suffix(path.suffix + ".bak")
            try:
                plaintext = self._fernet.decrypt(backup.read_bytes())
                value = yaml.safe_load(plaintext.decode("utf-8")) or {}
                if not isinstance(value, dict):
                    raise ValueError("decrypted secret backup must be a mapping")
                self._atomic_write(path, self._fernet.encrypt(yaml.safe_dump(value).encode("utf-8")), False)
                return deepcopy(value)
            except (InvalidToken, OSError, UnicodeError, yaml.YAMLError, ValueError):
                raise RuntimeError(f"Unable to decrypt secret store: {path}") from error

    def _write_mapping(self, path: Path, mapping: dict) -> None:
        self._require_key()
        payload = yaml.safe_dump(mapping, default_flow_style=False).encode("utf-8")
        encrypted = self._fernet.encrypt(payload)
        with self._lock:
            self._atomic_write(path, encrypted, True)

    def _atomic_write(self, path: Path, payload: bytes, create_backup: bool) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.parent.chmod(0o700)
        except OSError:
            pass
        if create_backup and path.is_file():
            backup = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, backup)
            try:
                backup.chmod(0o600)
            except OSError:
                pass
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}-",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
            temporary_path.chmod(0o600)
            os.replace(temporary_path, path)
            try:
                path.chmod(0o600)
            except OSError:
                pass
        finally:
            temporary_path.unlink(missing_ok=True)

    def _require_key(self) -> None:
        if not self.available or self._fernet is None:
            raise RuntimeError(
                "No EyeBot master key is configured. Run manage_secrets.py init."
            )
