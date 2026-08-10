import unittest
from unittest.mock import AsyncMock, patch

from adapters.instagram_adapter import InstagramAdapter
from adapters.tiktok_adapter import TikTokAdapter


class HostedMediaAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_instagram_builds_carousel_for_multiple_images(self):
        adapter = InstagramAdapter()
        request = AsyncMock(
            side_effect=[
                {"id": "child-1"},
                {"id": "child-2"},
                {"id": "carousel"},
                {"id": "published"},
            ]
        )
        with patch("adapters.instagram_adapter.json_request", request):
            result = await adapter.create_image_post(
                {"account_id": "ig-1", "access_token": "token"},
                "caption",
                ["https://media.example/1.jpg", "https://media.example/2.jpg"],
                object(),
            )

        self.assertEqual(result, {"id": "published"})
        self.assertEqual(request.await_count, 4)
        parent = request.await_args_list[2].kwargs["data"]
        self.assertEqual(parent["media_type"], "CAROUSEL")
        self.assertEqual(parent["children"], "child-1,child-2")

    async def test_tiktok_initializes_photo_pull_from_url(self):
        adapter = TikTokAdapter()
        request = AsyncMock(return_value={"data": {"publish_id": "post-1"}})
        with patch("adapters.tiktok_adapter.json_request", request):
            await adapter.initialize_photo_post(
                {"access_token": "token"},
                "caption",
                ["https://media.example/1.jpg"],
                object(),
            )

        payload = request.await_args.kwargs["json"]
        self.assertEqual(payload["media_type"], "PHOTO")
        self.assertEqual(payload["post_mode"], "DIRECT_POST")
        self.assertEqual(payload["source_info"]["source"], "PULL_FROM_URL")
        self.assertEqual(
            payload["source_info"]["photo_images"],
            ["https://media.example/1.jpg"],
        )


if __name__ == "__main__":
    unittest.main()
