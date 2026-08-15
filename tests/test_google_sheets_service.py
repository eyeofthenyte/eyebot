import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.googleSheetsService import (
    GoogleSheetsError,
    GoogleSheetsService,
    refresh_command,
)


class FakeWorksheet:
    def __init__(self, title, rows):
        self.title = title
        self._rows = rows

    def get_all_values(self):
        return self._rows


class FakeWorkbook:
    def __init__(self, worksheets):
        self._worksheets = worksheets

    def worksheets(self):
        return self._worksheets


class FakeClient:
    def __init__(self, workbook):
        self.workbook = workbook
        self.open_count = 0

    def open_by_key(self, key):
        self.open_count += 1
        return self.workbook


class GoogleSheetsServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        workbook = FakeWorkbook(
            [
                FakeWorksheet(
                    "Ingredients",
                    [["Name", "Effect"], ["Aloe", "Healing"], ["", ""]],
                ),
                FakeWorksheet("Potion", [["Aloe", "", "", "", "", "", "-1"]]),
            ]
        )
        self.client = FakeClient(workbook)
        self.service = GoogleSheetsService(
            client_factory=lambda _: self.client,
            cache_ttl=300,
            stale_ttl=600,
            persistent_cache_dir=self.temporary_directory.name,
            refresh_interval=0,
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_returns_worksheet_snapshots(self):
        worksheet = asyncio.run(
            self.service.worksheet("spreadsheet", "Ingredients")
        )

        self.assertEqual(worksheet.title, "Ingredients")
        self.assertEqual(worksheet.col_values(1), ["Name", "Aloe"])
        self.assertEqual(worksheet.cell(2, 2).value, "Healing")
        self.assertIsNone(worksheet.cell(100, 100).value)

    def test_reuses_cached_workbook(self):
        asyncio.run(self.service.worksheet("spreadsheet", "Ingredients"))
        asyncio.run(self.service.worksheet("spreadsheet", "Potion"))

        self.assertEqual(self.client.open_count, 1)

    def test_refresh_reloads_workbook(self):
        asyncio.run(self.service.worksheets("spreadsheet"))
        asyncio.run(self.service.worksheets("spreadsheet", refresh=True))

        self.assertEqual(self.client.open_count, 2)

    def test_missing_worksheet_has_consistent_error(self):
        with self.assertRaisesRegex(GoogleSheetsError, "does not exist"):
            asyncio.run(self.service.worksheet("spreadsheet", "Missing"))

    def test_persistent_cache_survives_service_recreation(self):
        asyncio.run(self.service.worksheets("spreadsheet"))
        offline_client = FakeClient(self.client.workbook)
        second = GoogleSheetsService(
            client_factory=lambda _: offline_client,
            cache_ttl=300,
            stale_ttl=600,
            persistent_cache_dir=self.temporary_directory.name,
            refresh_interval=0,
        )

        worksheet = asyncio.run(second.worksheet("spreadsheet", "Ingredients"))

        self.assertEqual(worksheet.cell(2, 1).value, "Aloe")
        self.assertEqual(offline_client.open_count, 0)

    def test_stale_cache_returns_before_background_refresh(self):
        async def scenario():
            with patch("services.googleSheetsService.time.time", return_value=1000):
                await self.service.worksheets("spreadsheet")
            with patch("services.googleSheetsService.time.time", return_value=1400):
                rows = await self.service.worksheets("spreadsheet")
                self.assertEqual(rows[0].title, "Ingredients")
                await asyncio.sleep(0)
                tasks = tuple(self.service._refresh_tasks.values())
                if tasks:
                    await asyncio.gather(*tasks)

        asyncio.run(scenario())
        self.assertEqual(self.client.open_count, 2)

    def test_simultaneous_requests_share_one_google_load(self):
        async def scenario():
            await asyncio.gather(
                self.service.worksheets("spreadsheet"),
                self.service.worksheets("spreadsheet"),
                self.service.worksheets("spreadsheet"),
            )

        asyncio.run(scenario())
        self.assertEqual(self.client.open_count, 1)

    def test_start_preloads_registered_workbook(self):
        async def scenario():
            self.service.register_workbook("spreadsheet")
            await self.service.start()
            await self.service.close()

        asyncio.run(scenario())
        self.assertEqual(self.client.open_count, 1)
        self.assertTrue(tuple(Path(self.temporary_directory.name).glob("*.json")))

    def test_refresh_command_requires_moderator(self):
        class Context:
            request = type(
                "Request",
                (),
                {"actor": type("Actor", (), {"roles": (), "metadata": {}})()},
            )()
            messages = []

            async def send(self, message):
                self.messages.append(message)

        context = Context()
        result = asyncio.run(
            refresh_command(context, self.service, "spreadsheet", "Test")
        )
        self.assertFalse(result)
        self.assertIn("Only a server administrator", context.messages[0])

    def test_refresh_command_allows_stream_moderator(self):
        class Context:
            request = type(
                "Request",
                (),
                {
                    "actor": type(
                        "Actor", (), {"roles": ("moderator",), "metadata": {}}
                    )()
                },
            )()
            messages = []

            async def send(self, message):
                self.messages.append(message)

        context = Context()
        result = asyncio.run(
            refresh_command(context, self.service, "spreadsheet", "Test")
        )
        self.assertTrue(result)
        self.assertIn("was refreshed", context.messages[0])


if __name__ == "__main__":
    unittest.main()
