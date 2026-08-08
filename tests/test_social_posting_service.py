import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

from services.platformConfigService import PlatformConfigService
from services.platformJobService import DuplicateJobError
from services.socialPostingService import SocialPostRequest, SocialPostingService


class SocialPostingServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        platform_path = root / "platforms.yaml"
        platform_path.write_text(
            """
twitter: {enabled: true, posting_enabled: true}
facebook: {enabled: true, posting_enabled: true}
bluesky: {enabled: true, posting_enabled: true}
instagram: {enabled: true, posting_enabled: true}
tiktok: {enabled: true, posting_enabled: true}
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
