import unittest

from services.accountDiscoveryService import discover_oauth_account


class _Response:
    def __init__(self, body, status=200):
        self.body = body
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def json(self, content_type=None):
        return self.body


class _Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def get(self, url, *, headers, params):
        self.requests.append((url, headers, params))
        return _Response(*self.responses.pop(0))


class _PlatformService:
    def __init__(self, settings):
        self.settings = settings
        self.overrides = []

    def effective_guild_platform(self, guild_id, platform):
        return self.settings.get(platform, {})

    def set_guild_platform_override(self, guild_id, platform, parameter, value):
        self.overrides.append((str(guild_id), platform, parameter, value))


class MetaAccountDiscoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_instagram_uses_page_returned_by_me_accounts(self):
        service = _PlatformService(
            {
                "facebook": {"page_id": "page-1"},
                "instagram": {"account_id": "ig-1"},
            }
        )
        session = _Session(
            [
                (
                    {
                        "data": [
                            {
                                "id": "page-1",
                                "name": "EoN Creations",
                                "access_token": "page-token",
                                "instagram_business_account": {
                                    "id": "ig-1",
                                    "username": "eon_creations",
                                },
                            }
                        ]
                    },
                    200,
                )
            ]
        )

        result = await discover_oauth_account(
            "instagram",
            "42",
            {"access_token": "user-token"},
            service,
            session,
        )

        self.assertEqual(result["access_token"], "page-token")
        self.assertIn(
            ("42", "instagram", "account_name", "eon_creations"),
            service.overrides,
        )
        self.assertEqual(len(session.requests), 1)

    async def test_instagram_falls_back_to_configured_facebook_page(self):
        service = _PlatformService(
            {
                "facebook": {"page_id": "page-1"},
                "instagram": {"account_id": "ig-1"},
            }
        )
        session = _Session(
            [
                ({"data": []}, 200),
                (
                    {
                        "id": "page-1",
                        "name": "EoN Creations",
                        "access_token": "page-token",
                        "instagram_business_account": {
                            "id": "ig-1",
                            "username": "eon_creations",
                        },
                    },
                    200,
                ),
            ]
        )

        result = await discover_oauth_account(
            "instagram",
            "42",
            {"access_token": "user-token"},
            service,
            session,
        )

        self.assertEqual(result["access_token"], "page-token")
        self.assertEqual(
            session.requests[1][0],
            "https://graph.facebook.com/v26.0/page-1",
        )

    async def test_facebook_falls_back_to_configured_page(self):
        service = _PlatformService({"facebook": {"page_id": "page-1"}})
        session = _Session(
            [
                ({"data": []}, 200),
                (
                    {
                        "id": "page-1",
                        "name": "EoN Creations",
                        "access_token": "page-token",
                    },
                    200,
                ),
            ]
        )

        result = await discover_oauth_account(
            "facebook",
            "42",
            {"access_token": "user-token"},
            service,
            session,
        )

        self.assertEqual(result["access_token"], "page-token")
        self.assertIn(
            ("42", "facebook", "account_name", "EoN Creations"),
            service.overrides,
        )

    async def test_instagram_rejects_different_linked_account(self):
        service = _PlatformService(
            {
                "facebook": {"page_id": "page-1"},
                "instagram": {"account_id": "ig-1"},
            }
        )
        session = _Session(
            [
                ({"data": []}, 200),
                (
                    {
                        "id": "page-1",
                        "name": "EoN Creations",
                        "instagram_business_account": {"id": "ig-2"},
                    },
                    200,
                ),
            ]
        )

        with self.assertRaisesRegex(ValueError, "configured instagram account"):
            await discover_oauth_account(
                "instagram",
                "42",
                {"access_token": "user-token"},
                service,
                session,
            )

    async def test_instagram_requires_configured_facebook_page_for_fallback(self):
        service = _PlatformService(
            {
                "facebook": {},
                "instagram": {"account_id": "ig-1"},
            }
        )
        session = _Session([({"data": []}, 200)])

        with self.assertRaisesRegex(ValueError, "Configure facebook page_id"):
            await discover_oauth_account(
                "instagram",
                "42",
                {"access_token": "user-token"},
                service,
                session,
            )


if __name__ == "__main__":
    unittest.main()
