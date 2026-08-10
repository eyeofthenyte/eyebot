import os
import tempfile
import time
import unittest
from pathlib import Path

from services.publicMediaService import PublicMediaService


class Attachment:
    def __init__(self, payload, content_type="image/png", filename="image.png"):
        self.payload = payload
        self.content_type = content_type
        self.filename = filename
        self.size = len(payload)

    async def read(self):
        return self.payload


class PublicMediaServiceTests(unittest.IsolatedAsyncioTestCase):
    def config(self, root, **overrides):
        settings = {
            "enabled": True,
            "public_base_url": "https://media.example.test/media",
            "storage_path": str(Path(root) / "public"),
            "retention_hours": 72,
            "max_bytes_per_guild": 10_000_000,
        }
        settings.update(overrides)
        return {
            "gateway": {"enabled": True},
            "public_media": settings,
        }

    async def test_hosts_valid_image_under_guild_prefix(self):
        with tempfile.TemporaryDirectory() as root:
            service = PublicMediaService(self.config(root), Path(root) / "guilds")
            payload = b"\x89PNG\r\n\x1a\n" + b"x" * 20

            hosted = await service.host_images(
                "42", [Attachment(payload)], alt_text="campaign map"
            )

            path = Path(hosted[0]["path"])
            self.assertEqual(path.read_bytes(), payload)
            self.assertEqual(path.relative_to(service.root).parts[0], "42")
            self.assertTrue(hosted[0]["url"].startswith("https://media.example.test/media/42/"))
            self.assertEqual(
                service.resolve("42", path.parent.name, path.name),
                path,
            )

    async def test_guilds_use_separate_namespaces(self):
        with tempfile.TemporaryDirectory() as root:
            service = PublicMediaService(self.config(root), Path(root) / "guilds")
            payload = b"\x89PNG\r\n\x1a\n" + b"x" * 20
            first = await service.host_images("42", [Attachment(payload)])
            second = await service.host_images("84", [Attachment(payload)])

            self.assertIn("/42/", first[0]["url"])
            self.assertIn("/84/", second[0]["url"])
            with self.assertRaises(FileNotFoundError):
                first_path = Path(first[0]["path"])
                service.resolve("84", first_path.parent.name, first_path.name)

    async def test_cleanup_removes_expired_media(self):
        with tempfile.TemporaryDirectory() as root:
            service = PublicMediaService(
                self.config(root, retention_hours=1),
                Path(root) / "guilds",
            )
            payload = b"\x89PNG\r\n\x1a\n" + b"x" * 20
            hosted = await service.host_images("42", [Attachment(payload)])
            path = Path(hosted[0]["path"])
            old = time.time() - 7200
            os.utime(path, (old, old))

            self.assertEqual(service.cleanup_expired(), 1)
            self.assertFalse(path.exists())

    def test_enabled_hosting_requires_https(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "must use HTTPS"):
                PublicMediaService(
                    self.config(root, public_base_url="http://media.example.test/media"),
                    Path(root) / "guilds",
                )

    def test_enabled_hosting_requires_gateway(self):
        with tempfile.TemporaryDirectory() as root:
            config = self.config(root)
            config["gateway"]["enabled"] = False
            with self.assertRaisesRegex(ValueError, "requires gateway"):
                PublicMediaService(config, Path(root) / "guilds")

    def test_cloud_provider_placeholder_is_rejected_until_implemented(self):
        with tempfile.TemporaryDirectory() as root:
            config = self.config(root)
            config["public_media"]["provider"] = "cloudflare_r2"
            with self.assertRaisesRegex(ValueError, "placeholder.*not implemented"):
                PublicMediaService(config, Path(root) / "guilds")


if __name__ == "__main__":
    unittest.main()
