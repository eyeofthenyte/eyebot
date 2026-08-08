import tempfile
import unittest
from pathlib import Path

from services.mediaStagingService import MediaStagingService


class Attachment:
    def __init__(self, payload, content_type="image/png", filename="image.png"):
        self.payload = payload
        self.content_type = content_type
        self.filename = filename
        self.size = len(payload)

    async def read(self):
        return self.payload


class MediaStagingTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_image_is_persisted_and_removed(self):
        with tempfile.TemporaryDirectory() as root:
            service = MediaStagingService(root)
            payload = b"\x89PNG\r\n\x1a\n" + b"x" * 20
            staged = await service.stage_images(
                "bluesky", [Attachment(payload)], alt_text="map"
            )
            self.assertEqual(Path(staged[0]["path"]).read_bytes(), payload)
            self.assertEqual(staged[0]["alt_text"], "map")
            service.remove(staged)
            self.assertFalse(Path(staged[0]["path"]).exists())

    async def test_mismatched_content_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            service = MediaStagingService(root)
            with self.assertRaisesRegex(ValueError, "do not match"):
                await service.stage_images(
                    "twitter", [Attachment(b"not a png")]
                )


if __name__ == "__main__":
    unittest.main()
