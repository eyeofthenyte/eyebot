import base64
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from services.kickWebhookService import (
    KickWebhookAuthenticationError,
    KickWebhookDuplicateError,
    KickWebhookError,
    KickWebhookService,
)


class KickWebhookServiceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 12, 20, 0, tzinfo=timezone.utc)
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = self.private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.temporary = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temporary.name) / "kick-events.json"
        self.service = KickWebhookService(
            self.state_path,
            public_key_pem=public_key,
            now=lambda: self.now,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def signed_request(self, payload=None, *, timestamp=None, message_id="message-1"):
        raw = json.dumps(payload or {"content": "!r 1d20"}, separators=(",", ":")).encode()
        timestamp_text = (timestamp or self.now).isoformat().replace("+00:00", "Z")
        signed = b".".join((message_id.encode(), timestamp_text.encode(), raw))
        signature = self.private_key.sign(signed, padding.PKCS1v15(), hashes.SHA256())
        return raw, {
            "Kick-Event-Message-Id": message_id,
            "Kick-Event-Subscription-Id": "subscription-1",
            "Kick-Event-Signature": base64.b64encode(signature).decode(),
            "Kick-Event-Message-Timestamp": timestamp_text,
            "Kick-Event-Type": "chat.message.sent",
            "Kick-Event-Version": "1",
        }

    def test_authenticates_valid_signed_raw_body(self):
        raw, headers = self.signed_request()
        event = self.service.authenticate(raw, headers)

        self.assertEqual(event.message_id, "message-1")
        self.assertEqual(event.subscription_id, "subscription-1")
        self.assertEqual(event.event_type, "chat.message.sent")

    def test_modified_body_fails_signature_verification(self):
        raw, headers = self.signed_request()
        with self.assertRaisesRegex(KickWebhookAuthenticationError, "signature"):
            self.service.authenticate(raw + b" ", headers)

    def test_missing_headers_are_rejected_before_authentication(self):
        with self.assertRaisesRegex(KickWebhookError, "missing required headers"):
            self.service.authenticate(b"{}", {})

    def test_stale_and_future_timestamps_are_rejected(self):
        for timestamp in (
            self.now - timedelta(minutes=6),
            self.now + timedelta(seconds=61),
        ):
            raw, headers = self.signed_request(timestamp=timestamp)
            with self.subTest(timestamp=timestamp):
                with self.assertRaisesRegex(KickWebhookAuthenticationError, "stale"):
                    self.service.authenticate(raw, headers)

    def test_remember_persists_and_rejects_duplicate_message_id(self):
        raw, headers = self.signed_request()
        event = self.service.authenticate(raw, headers)
        self.service.remember(event)

        reloaded = KickWebhookService(
            self.state_path,
            public_key_pem=self.private_key.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            ),
            now=lambda: self.now,
        )
        with self.assertRaises(KickWebhookDuplicateError):
            reloaded.authenticate(raw, headers)

    def test_claim_blocks_concurrent_delivery_and_release_allows_retry(self):
        raw, headers = self.signed_request()
        event = self.service.authenticate(raw, headers)
        self.service.claim(event)

        with self.assertRaises(KickWebhookDuplicateError):
            self.service.authenticate(raw, headers)

        self.service.release(event.message_id)
        self.assertEqual(self.service.authenticate(raw, headers).message_id, "message-1")

    def test_invalid_json_is_rejected_after_signature_verification(self):
        raw = b"not-json"
        timestamp = self.now.isoformat().replace("+00:00", "Z")
        signed = b".".join((b"message-1", timestamp.encode(), raw))
        signature = self.private_key.sign(signed, padding.PKCS1v15(), hashes.SHA256())
        headers = {
            "Kick-Event-Message-Id": "message-1",
            "Kick-Event-Subscription-Id": "subscription-1",
            "Kick-Event-Signature": base64.b64encode(signature).decode(),
            "Kick-Event-Message-Timestamp": timestamp,
            "Kick-Event-Type": "chat.message.sent",
            "Kick-Event-Version": "1",
        }

        with self.assertRaisesRegex(KickWebhookError, "valid JSON"):
            self.service.authenticate(raw, headers)


if __name__ == "__main__":
    unittest.main()
