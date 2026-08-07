import asyncio
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


class GoogleSheetsError(RuntimeError):
    """Raised when Google Sheets data cannot be loaded."""


@dataclass(frozen=True)
class CellSnapshot:
    value: str | None


@dataclass(frozen=True)
class WorksheetSnapshot:
    """In-memory worksheet data with the small API used by the cogs."""

    title: str
    rows: tuple[tuple[str, ...], ...]

    def col_values(self, column: int) -> list[str]:
        if column < 1:
            raise ValueError("Column numbers start at 1.")
        index = column - 1
        values = [row[index] if index < len(row) else "" for row in self.rows]
        while values and values[-1] == "":
            values.pop()
        return values

    def cell(self, row: int, column: int) -> CellSnapshot:
        if row < 1 or column < 1:
            raise ValueError("Row and column numbers start at 1.")
        try:
            value = self.rows[row - 1][column - 1]
        except IndexError:
            value = None
        return CellSnapshot(value)


class GoogleSheetsService:
    """Lazy, cached, asynchronous access to Google Sheets."""

    def __init__(
        self,
        credentials_file: str | os.PathLike | None = None,
        *,
        cache_ttl: int = 300,
        client_factory: Callable | None = None,
    ):
        project_root = Path(__file__).resolve().parents[2]
        configured_path = credentials_file or os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_FILE",
            project_root / "service_account.json",
        )
        self.credentials_file = Path(configured_path).expanduser().resolve()
        self.cache_ttl = cache_ttl
        self._client_factory = client_factory
        self._client = None
        self._cache = {}
        self._lock = asyncio.Lock()

    @property
    def available(self) -> bool:
        return self._client_factory is not None or self.credentials_file.is_file()

    def clear_cache(self) -> None:
        self._cache.clear()

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self.available:
            raise GoogleSheetsError(
                f"Google service-account credentials were not found at "
                f"{self.credentials_file}."
            )
        try:
            if self._client_factory is None:
                import gspread

                self._client = gspread.service_account(
                    filename=str(self.credentials_file)
                )
            else:
                self._client = self._client_factory(str(self.credentials_file))
        except Exception as error:
            raise GoogleSheetsError(
                f"Google Sheets authentication failed: {error}"
            ) from error
        return self._client

    def _load_workbook(self, spreadsheet_key: str) -> tuple[WorksheetSnapshot, ...]:
        try:
            workbook = self._get_client().open_by_key(spreadsheet_key)
            return tuple(
                WorksheetSnapshot(
                    title=worksheet.title,
                    rows=tuple(
                        tuple(str(value) for value in row)
                        for row in worksheet.get_all_values()
                    ),
                )
                for worksheet in workbook.worksheets()
            )
        except GoogleSheetsError:
            raise
        except Exception as error:
            raise GoogleSheetsError(
                f"Unable to load spreadsheet {spreadsheet_key}: {error}"
            ) from error

    async def worksheets(
        self, spreadsheet_key: str, *, refresh: bool = False
    ) -> tuple[WorksheetSnapshot, ...]:
        now = time.monotonic()
        cached = self._cache.get(spreadsheet_key)
        if not refresh and cached and cached[0] > now:
            return cached[1]

        async with self._lock:
            now = time.monotonic()
            cached = self._cache.get(spreadsheet_key)
            if not refresh and cached and cached[0] > now:
                return cached[1]

            snapshots = await asyncio.to_thread(
                self._load_workbook, spreadsheet_key
            )
            self._cache[spreadsheet_key] = (
                time.monotonic() + self.cache_ttl,
                snapshots,
            )
            return snapshots

    async def worksheet(
        self,
        spreadsheet_key: str,
        worksheet: str | int = 0,
        *,
        refresh: bool = False,
    ) -> WorksheetSnapshot:
        worksheets = await self.worksheets(spreadsheet_key, refresh=refresh)
        if isinstance(worksheet, int):
            try:
                return worksheets[worksheet]
            except IndexError as error:
                raise GoogleSheetsError(
                    f"Worksheet index {worksheet} does not exist."
                ) from error

        for snapshot in worksheets:
            if snapshot.title == worksheet:
                return snapshot
        raise GoogleSheetsError(f"Worksheet '{worksheet}' does not exist.")


def get_google_sheets_service(bot) -> GoogleSheetsService:
    """Return the single Sheets service shared by every cog."""
    service = getattr(bot, "google_sheets", None)
    if service is None:
        sheets_config = bot.config.get("google_sheets", {})
        service = GoogleSheetsService(
            credentials_file=sheets_config.get("credentials_file"),
            cache_ttl=int(sheets_config.get("cache_ttl", 300)),
        )
        bot.google_sheets = service
    return service
