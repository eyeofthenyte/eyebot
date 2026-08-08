import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

from services.oauthStateService import OAuthStateService
from services.platformConfigService import PlatformConfigService
from services.platformConnectionService import PlatformConnectionService


class OAuthStateTests(unittest.TestCase):
    def setUp(self):
        self.states = OAuthStateService(b"x" * 32)

    def test_callback_state_is_signed_and_single_use(self):
        token, issued = self.states.issue("42", "youtube", "7")
        consumed = self.states.consume(token)
        self.assertEqual(consumed, issued)
        with self.assertRaisesRegex(ValueError, "already used|unknown"):
            self.states.consume(token)

    def test_tampered_state_is_rejected(self):
        token, _ = self.states.issue("42", "youtube", "7")
        with self.assertRaises(ValueError):
            self.states.consume("x" + token)

    def test_start_request_is_single_use(self):
        token = self.states.sign_start_request("42", "youtube", "7")
        self.assertEqual(self.states.verify_start_request(token)["guild_id"], "42")
        with self.assertRaises(ValueError):
            self.states.verify_start_request(token)


class ConnectionStorageTests(unittest.TestCase):
    def test_token_response_is_encrypted_and_metadata_is_guild_scoped(self):
        with tempfile.TemporaryDirectory() as root:
            platform_path = Path(root) / "platforms.yaml"
            platform_path.write_text("youtube: {}\n", encoding="utf-8")
            service = PlatformConfigService(
                str(platform_path),
                master_key=Fernet.generate_key(),
            )
            service.ensure_discord_guild("42")
            connection = PlatformConnectionService(service)
            connection.save_token_response(
                "42",
                "youtube",
                {
                    "access_token": "access",
                    "refresh_token": "refresh",
                    "expires_in": 3600,
                    "scope": "youtube.readonly",
                },
            )
            effective = service.effective_guild_platform("42", "youtube")
            self.assertEqual(effective["access_token"], "access")
            self.assertEqual(effective["refresh_token"], "refresh")
            self.assertTrue(effective["connected"])
            guild_text = service.guild_path("42").read_text(encoding="utf-8")
            self.assertNotIn("access", guild_text)
            self.assertNotIn("refresh", guild_text)


if __name__ == "__main__":
    unittest.main()
