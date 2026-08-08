import hashlib
import hmac
import unittest

from services.webhookService import WebhookService


class WebhookVerificationTests(unittest.TestCase):
    def test_meta_sha256_signature(self):
        body = b'{"object":"page"}'
        secret = "secret"
        signature = "sha256=" + hmac.new(
            secret.encode(), body, hashlib.sha256
        ).hexdigest()
        self.assertTrue(WebhookService.verify_meta_signature(body, signature, secret))
        self.assertFalse(WebhookService.verify_meta_signature(body + b"x", signature, secret))


if __name__ == "__main__":
    unittest.main()
