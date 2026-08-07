import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cryptography.fernet import Fernet

from manage_secrets import main
from services.platformConfigService import PlatformConfigService
from services.platformSecretService import PlatformSecretService


class PlatformSecretServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.secret_dir = self.root / "data" / "secrets"
        self.key_file = self.root / "secrets" / "eyebot_master_key"
        PlatformSecretService.generate_key_file(self.key_file)

    def tearDown(self):
        self.temp.cleanup()

    def service(self):
        return PlatformSecretService(
            self.secret_dir,
            master_key_file=self.key_file,
        )

    def test_global_secret_is_encrypted_and_names_do_not_expose_value(self):
        service = self.service()
        service.set_secret("discord", "bot_token", "highly-sensitive-token")

        path = self.secret_dir / "global.secrets"
        self.assertTrue(path.is_file())
        self.assertNotIn(b"highly-sensitive-token", path.read_bytes())
        self.assertEqual(
            service.global_platforms()["discord"]["bot_token"],
            "highly-sensitive-token",
        )
        self.assertEqual(
            service.list_secret_names(),
            {"discord": ("bot_token",)},
        )

    def test_guild_secret_is_isolated_and_overrides_global_secret(self):
        service = self.service()
        service.set_secret("youtube", "api_key", "global-key")
        service.set_secret(
            "youtube",
            "api_key",
            "guild-key",
            guild_id="42",
        )
        platform_path = self.root / "platforms.yaml"
        platform_path.write_text("youtube:\n  enabled: true\n", encoding="utf-8")
        platforms = PlatformConfigService(
            str(platform_path),
            secret_dir=str(self.secret_dir),
            master_key_file=str(self.key_file),
        )

        self.assertEqual(
            platforms.merged_with_global({})["youtube"]["api_key"],
            "global-key",
        )
        self.assertEqual(
            platforms.effective_guild_platform("42", "youtube")["api_key"],
            "guild-key",
        )
        self.assertEqual(
            platforms.effective_guild_platform("84", "youtube")["api_key"],
            "global-key",
        )

    def test_encrypted_store_requires_the_matching_master_key(self):
        service = self.service()
        service.set_secret("discord", "bot_token", "secret")
        wrong_key = Fernet.generate_key()
        wrong = PlatformSecretService(self.secret_dir, master_key=wrong_key)

        with self.assertRaises(RuntimeError):
            wrong.global_platforms()

    def test_existing_store_without_key_fails_closed(self):
        service = self.service()
        service.set_secret("discord", "bot_token", "secret")

        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                PlatformSecretService(self.secret_dir)

    def test_corrupt_secret_store_recovers_from_encrypted_backup(self):
        service = self.service()
        service.set_secret("discord", "bot_token", "first")
        service.set_secret("discord", "bot_token", "second")
        path = self.secret_dir / "global.secrets"
        path.write_bytes(b"not-fernet-data")

        self.assertEqual(
            service.global_platforms()["discord"]["bot_token"],
            "first",
        )
        self.assertNotEqual(path.read_bytes(), b"not-fernet-data")

    def test_invalid_secret_name_and_guild_id_are_rejected(self):
        service = self.service()
        with self.assertRaises(ValueError):
            service.set_secret("youtube", "not_a_secret", "value")
        with self.assertRaises(ValueError):
            service.set_secret(
                "youtube",
                "api_key",
                "value",
                guild_id="../../escape",
            )

    def test_delete_removes_only_selected_secret(self):
        service = self.service()
        service.set_secret("twitter", "api_key", "key")
        service.set_secret("twitter", "api_secret", "secret")

        self.assertTrue(service.delete_secret("twitter", "api_key"))
        self.assertEqual(
            service.list_secret_names(),
            {"twitter": ("api_secret",)},
        )


class ManageSecretsCliTests(unittest.TestCase):
    def test_cli_initializes_key_and_sets_secret_from_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            key_file = root / "master_key"
            secret_dir = root / "encrypted"
            value_file = root / "input.secret"
            value_file.write_text("cli-secret\n", encoding="utf-8")
            value_file.chmod(0o600)

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            "--secret-dir",
                            str(secret_dir),
                            "--key-file",
                            str(key_file),
                            "init",
                        ]
                    ),
                    0,
                )
                self.assertEqual(
                    main(
                        [
                            "--secret-dir",
                            str(secret_dir),
                            "--key-file",
                            str(key_file),
                            "set",
                            "discord",
                            "bot_token",
                            "--value-file",
                            str(value_file),
                        ]
                    ),
                    0,
                )

            service = PlatformSecretService(
                secret_dir,
                master_key_file=key_file,
            )
            self.assertEqual(
                service.global_platforms()["discord"]["bot_token"],
                "cli-secret",
            )


if __name__ == "__main__":
    unittest.main()
