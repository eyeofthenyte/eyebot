import asyncio
import unittest

from services.googleSheetsService import GoogleSheetsError, GoogleSheetsService


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
        )

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


if __name__ == "__main__":
    unittest.main()
