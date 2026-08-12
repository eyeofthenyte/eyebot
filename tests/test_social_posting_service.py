import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from cryptography.fernet import Fernet
from PIL import Image

from services.platformConfigService import PlatformConfigService
from services.platformJobService import DuplicateJobError
from services.socialPostingService import SocialPostRequest, SocialPostingService


class Attachment:
    def __init__(self, payload, content_type="image/png", filename="image.png"):
        self.payload = payload
        self.content_type = content_type
        self.filename = filename
        self.size = len(payload)

    async def read(self):
        return self.payload


class SocialPostingServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        platform_path = root / "platforms.yaml"
        platform_path.write_text(
            """
twitter: {enabled: true, connected: true, posting_enabled: true}
facebook: {enabled: true, connected: true, posting_enabled: true}
bluesky: {enabled: true, posting_enabled: true}
instagram: {enabled: true, connected: true, posting_enabled: true}
tiktok: {enabled: true, connected: true, posting_enabled: true}
kofi: {enabled: true}
""".lstrip(),
            encoding="utf-8",
        )
        self.config = PlatformConfigService(
            str(platform_path),
            guild_config_dir=str(root / "guilds"),
            secret_dir=str(root / "secrets"),
            master_key=Fernet.generate_key(),
        )
        self.config.ensure_discord_guild("42")
        self.service = SocialPostingService(self.config)

    def tearDown(self):
        self.temporary.cleanup()

    async def test_text_post_is_queued_for_twitter(self):
        result = await self.service.queue(
            SocialPostRequest("42", "twitter", "hello", "100", "7")
        )
        self.assertEqual(result.queued, ("twitter",))
        claimed, job = self.service.jobs.claim_next("twitter")
        self.assertEqual(job["payload"]["text"], "hello")
        self.service.jobs.complete(claimed)

    async def test_same_message_platform_is_not_queued_twice(self):
        request = SocialPostRequest("42", "twitter", "hello", "100", "7")
        await self.service.queue(request)
        with self.assertRaises(DuplicateJobError):
            await self.service.queue(request)

    async def test_bluesky_uses_handle_and_app_password_as_connection(self):
        self.config.set_guild_platform_override(
            "42", "bluesky", "handle", "example.bsky.social"
        )
        self.config.secret_service.set_secret(
            "bluesky",
            "app_password",
            "abcd-efgh-ijkl-mnop",
            guild_id="42",
        )

        result = await self.service.queue(
            SocialPostRequest("42", "bluesky", "hello", "bluesky-100", "7")
        )

        self.assertEqual(result.queued, ("bluesky",))

    async def test_bluesky_without_app_password_is_not_connected(self):
        self.config.set_guild_platform_override(
            "42", "bluesky", "handle", "example.bsky.social"
        )

        with self.assertRaisesRegex(ValueError, "enabled but not connected"):
            await self.service.queue(
                SocialPostRequest("42", "bluesky", "hello", "bluesky-101", "7")
            )

    async def test_instagram_requires_public_https_media_url(self):
        with self.assertRaisesRegex(ValueError, "public HTTPS"):
            await self.service.queue(
                SocialPostRequest("42", "instagram", "caption", "100", "7")
            )
        result = await self.service.queue(
            SocialPostRequest(
                "42",
                "instagram",
                "caption",
                "101",
                "7",
                media_url="https://media.example/image.jpg",
            )
        )
        self.assertEqual(result.queued, ("instagram",))

    async def test_enabled_but_disconnected_platform_has_clear_error(self):
        self.config.set_guild_platform_override("42", "instagram", "connected", False)
        with self.assertRaisesRegex(ValueError, "enabled but not connected"):
            await self.service.queue(
                SocialPostRequest(
                    "42",
                    "instagram",
                    "caption",
                    "disconnected-100",
                    "7",
                    media_url="https://media.example/image.jpg",
                )
            )

    async def test_tiktok_accepts_public_https_media_url(self):
        result = await self.service.queue(
            SocialPostRequest(
                "42",
                "tiktok",
                "caption",
                "100",
                "7",
                media_url="https://media.example/video.mp4",
            )
        )
        self.assertEqual(result.queued, ("tiktok",))

    async def test_instagram_attachment_is_hosted_under_guild_prefix(self):
        self.service = SocialPostingService(
            self.config,
            {
                "gateway": {"enabled": True},
                "public_media": {
                    "enabled": True,
                    "public_base_url": "https://media.example.test/media",
                    "storage_path": str(Path(self.temporary.name) / "public-media"),
                }
            },
        )
        payload = b"\xff\xd8\xff" + b"x" * 20
        result = await self.service.queue(
            SocialPostRequest(
                "42",
                "instagram",
                "caption",
                "hosted-100",
                "7",
                attachments=(
                    Attachment(
                        payload,
                        content_type="image/jpeg",
                        filename="image.jpg",
                    ),
                ),
            )
        )

        self.assertEqual(result.queued, ("instagram",))
        _claimed, job = self.service.jobs.claim_next("instagram")
        self.assertEqual(job["operation"], "hosted_media_post")
        self.assertIn("/media/42/", job["payload"]["media"][0]["url"])

    async def test_instagram_converts_png_upload_to_hosted_jpeg(self):
        self.service = SocialPostingService(
            self.config,
            {
                "gateway": {"enabled": True},
                "public_media": {
                    "enabled": True,
                    "public_base_url": "https://media.example.test/media",
                    "storage_path": str(Path(self.temporary.name) / "public-media"),
                },
            },
        )
        source = BytesIO()
        Image.new("RGBA", (2, 2), (255, 0, 0, 128)).save(source, format="PNG")
        result = await self.service.queue(
            SocialPostRequest(
                "42",
                "instagram",
                "caption",
                "hosted-png",
                "7",
                attachments=(Attachment(source.getvalue()),),
            )
        )

        self.assertEqual(result.queued, ("instagram",))
        _claimed, job = self.service.jobs.claim_next("instagram")
        media = job["payload"]["media"][0]
        self.assertEqual(media["content_type"], "image/jpeg")
        self.assertEqual(Path(media["path"]).suffix, ".jpg")
        self.assertTrue(Path(media["path"]).read_bytes().startswith(b"\xff\xd8\xff"))

    async def test_all_attachments_exclude_url_platforms_when_hosting_is_disabled(self):
        self.config.set_guild_platform_override(
            "42", "bluesky", "handle", "example.bsky.social"
        )
        self.config.secret_service.set_secret(
            "bluesky",
            "app_password",
            "abcd-efgh-ijkl-mnop",
            guild_id="42",
        )
        payload = b"\x89PNG\r\n\x1a\n" + b"x" * 20
        result = await self.service.queue(
            SocialPostRequest(
                "42",
                "all",
                "caption",
                "all-100",
                "7",
                attachments=(Attachment(payload),),
            )
        )

        self.assertEqual(result.queued, ("twitter", "facebook", "bluesky"))
        self.assertIsNone(self.service.jobs.claim_next("instagram"))
        self.assertIsNone(self.service.jobs.claim_next("tiktok"))

    async def test_kofi_is_not_a_posting_destination(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            await self.service.queue(
                SocialPostRequest("42", "kofi", "hello", "100", "7")
            )

    async def test_cancel_removes_pending_job(self):
        await self.service.queue(
            SocialPostRequest("42", "twitter", "hello", "100", "7")
        )
        self.assertEqual(self.service.cancel("42", "100"), 1)
        self.assertIsNone(self.service.jobs.claim_next("twitter"))


if __name__ == "__main__":
    unittest.main()
