import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image

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

    async def test_png_gif_and_webp_can_be_normalized_to_jpeg(self):
        formats = (
            ("PNG", "image/png", "image.png"),
            ("GIF", "image/gif", "image.gif"),
            ("WEBP", "image/webp", "image.webp"),
        )
        for image_format, content_type, filename in formats:
            with self.subTest(image_format=image_format), tempfile.TemporaryDirectory() as root:
                source = BytesIO()
                Image.new("RGBA", (2, 2), (0, 128, 255, 128)).save(
                    source,
                    format=image_format,
                )
                service = MediaStagingService(root)
                staged = await service.stage_images(
                    "instagram",
                    [Attachment(source.getvalue(), content_type, filename)],
                    output_content_type="image/jpeg",
                )

                path = Path(staged[0]["path"])
                self.assertEqual(staged[0]["content_type"], "image/jpeg")
                self.assertEqual(path.suffix, ".jpg")
                self.assertTrue(path.read_bytes().startswith(b"\xff\xd8\xff"))


if __name__ == "__main__":
    unittest.main()
