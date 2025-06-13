import yaml
import os
from yaml.loader import SafeLoader
from datetime import datetime
from typing_extensions import Self
from services.logService import LogService


class ConfigService:
    def __init__(self, configPath: str, logger: LogService = None) -> None:
        self.configPath = configPath
        self.logger = logger
        self.config = {}

        # Load config with backup handling
        try:
            self._load_config()
            self._ensure_backup()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load config: {e}. Attempting to recover from backup.")
            if self._recover_from_backup():
                if self.logger:
                    self.logger.info("Recovery from backup successful.")
                self._ensure_backup()  # re-backup after recovery
            else:
                if self.logger:
                    self.logger.error("Recovery failed. ConfigService could not initialize.")

    def _load_config(self):
        if not os.path.exists(self.configPath):
            if self.logger:
                self.logger.warn(f"Config file not found: {self.configPath}. Will create on save.")
            return

        with open(self.configPath, "r") as f:
            self.config = yaml.load(f, Loader=SafeLoader) or {}
            if self.logger:
                self.logger.info(f"Loaded config from {self.configPath}")

    def _ensure_backup(self):
        backup_dir = os.path.dirname(self.configPath)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        backup_file = os.path.join(backup_dir, f"backup-{today}.bak")

        # Remove any existing backups (only 1 kept at a time)
        for file in os.listdir(backup_dir):
            if file.startswith("backup-") and file.endswith(".bak") and file != os.path.basename(backup_file):
                try:
                    os.remove(os.path.join(backup_dir, file))
                    if self.logger:
                        self.logger.info(f"Removed old backup: {file}")
                except Exception as e:
                    if self.logger:
                        self.logger.warn(f"Failed to delete old backup: {file} - {e}")

        # Create new backup
        try:
            with open(backup_file, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            if self.logger:
                self.logger.info(f"Backup created: {backup_file}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create backup: {e}")

    def _recover_from_backup(self) -> bool:
        backup_dir = os.path.dirname(self.configPath)
        backups = [
            f for f in os.listdir(backup_dir)
            if f.startswith("backup-") and f.endswith(".bak")
        ]
        if not backups:
            if self.logger:
                self.logger.error("No backup files found for recovery.")
            return False

        backups.sort(reverse=True)  # Most recent first
        backup_path = os.path.join(backup_dir, backups[0])
        try:
            with open(backup_path, "r") as f:
                self.config = yaml.load(f, Loader=SafeLoader) or {}
            with open(self.configPath, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            if self.logger:
                self.logger.info(f"Restored config from backup: {backup_path}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load or restore backup {backup_path}: {e}")
            return False

    def get(self):
        return self.config

    def set(self, config: dict) -> Self:
        self.config = config
        return self

    def save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.configPath), exist_ok=True)
            with open(self.configPath, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            if self.logger:
                self.logger.info(f"Config saved to: {self.configPath}")
        except PermissionError:
            if self.logger:
                self.logger.error(f"Permission denied while saving config to: {self.configPath}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save config: {e}")
