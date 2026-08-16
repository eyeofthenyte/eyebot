"""Cached, asynchronous access to Google Sheets-backed command data."""

from __future__ import annotations

import asyncio
import hashlib
import json
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


@dataclass(frozen=True)
class _CacheEntry:
    fetched_at: float
    worksheets: tuple[WorksheetSnapshot, ...]


class GoogleSheetsService:
    """Sheets access with memory, disk, preload, and background refresh."""

    def __init__(
        self,
        credentials_file: str | os.PathLike | None = None,
        *,
        cache_ttl: int = 21600,
        stale_ttl: int = 604800,
        persistent_cache_dir: str | os.PathLike | None = None,
        preload: bool = True,
        refresh_in_background: bool = True,
        refresh_interval: int = 21600,
        client_factory: Callable | None = None,
        logger=None,
    ):
        project_root = Path(__file__).resolve().parents[2]
        configured_path = credentials_file or os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_FILE", project_root / "service_account.json"
        )
        self.credentials_file = Path(configured_path).expanduser().resolve()
        self.cache_ttl = max(0, int(cache_ttl))
        self.stale_ttl = max(self.cache_ttl, int(stale_ttl))
        cache_dir = persistent_cache_dir or project_root / "data/cache/google_sheets"
        self.persistent_cache_dir = Path(cache_dir).expanduser().resolve()
        self.preload_enabled = bool(preload)
        self.refresh_in_background = bool(refresh_in_background)
        self.refresh_interval = max(0, int(refresh_interval))
        self._client_factory = client_factory
        self._client = None
        self._cache: dict[str, _CacheEntry] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._load_tasks: dict[str, asyncio.Task] = {}
        self._refresh_tasks: dict[str, asyncio.Task] = {}
        self._registered: set[str] = set()
        self._scheduled_task: asyncio.Task | None = None
        self._logger = logger

    @property
    def available(self) -> bool:
        return self._client_factory is not None or self.credentials_file.is_file()

    def register_workbook(self, spreadsheet_key: str) -> None:
        """Register a workbook for startup and scheduled cache warming."""
        key = str(spreadsheet_key).strip()
        if key:
            self._registered.add(key)

    def clear_cache(self, spreadsheet_key: str | None = None, *, disk: bool = False) -> None:
        keys = (
            tuple(self._registered | set(self._cache))
            if spreadsheet_key is None
            else (spreadsheet_key,)
        )
        for key in keys:
            self._cache.pop(key, None)
            if disk:
                try:
                    self._cache_path(key).unlink()
                except FileNotFoundError:
                    pass

    async def start(self) -> None:
        """Warm registered workbooks and begin scheduled refreshes."""
        keys = sorted(self._registered)
        if self.preload_enabled and self.available:
            results = await asyncio.gather(
                *(self.worksheets(key) for key in keys), return_exceptions=True
            )
            for key, result in zip(keys, results):
                if isinstance(result, Exception):
                    self._warning(f"Unable to preload Google workbook {key}: {result}")
        if self.refresh_interval and keys:
            if self._scheduled_task is None or self._scheduled_task.done():
                self._scheduled_task = asyncio.create_task(self._scheduled_refresh_loop())

    async def close(self) -> None:
        tasks = [task for task in self._refresh_tasks.values() if not task.done()]
        tasks.extend(task for task in self._load_tasks.values() if not task.done())
        if self._scheduled_task is not None and not self._scheduled_task.done():
            self._scheduled_task.cancel()
            tasks.append(self._scheduled_task)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._refresh_tasks.clear()
        self._load_tasks.clear()

    def _warning(self, message: str) -> None:
        if self._logger is not None:
            warning = getattr(self._logger, "warning", None) or getattr(
                self._logger, "warn", None
            )
            if callable(warning):
                warning(message)

    def _info(self, message: str) -> None:
        if self._logger is not None:
            info = getattr(self._logger, "info", None)
            if callable(info):
                info(message)

    def _cache_path(self, spreadsheet_key: str) -> Path:
        digest = hashlib.sha256(spreadsheet_key.encode("utf-8")).hexdigest()
        return self.persistent_cache_dir / f"{digest}.json"

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

                self._client = gspread.service_account(filename=str(self.credentials_file))
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
            worksheets = tuple(workbook.worksheets())
            batch_get = getattr(workbook, "values_batch_get", None)
            if callable(batch_get) and worksheets:
                ranges = [
                    "'" + worksheet.title.replace("'", "''") + "'"
                    for worksheet in worksheets
                ]
                response = batch_get(ranges)
                value_ranges = response.get("valueRanges", ())
                if len(value_ranges) != len(worksheets):
                    raise GoogleSheetsError(
                        "Google Sheets batch response did not match the workbook tabs"
                    )
                return tuple(
                    WorksheetSnapshot(
                        title=worksheet.title,
                        rows=tuple(
                            tuple(str(value) for value in row)
                            for row in values.get("values", ())
                        ),
                    )
                    for worksheet, values in zip(worksheets, value_ranges)
                )
            return tuple(
                WorksheetSnapshot(
                    title=worksheet.title,
                    rows=tuple(
                        tuple(str(value) for value in row)
                        for row in worksheet.get_all_values()
                    ),
                )
                for worksheet in worksheets
            )
        except GoogleSheetsError:
            raise
        except Exception as error:
            raise GoogleSheetsError(
                f"Unable to load spreadsheet {spreadsheet_key}: {error}"
            ) from error

    def _write_disk_cache(self, spreadsheet_key: str, entry: _CacheEntry) -> None:
        try:
            self.persistent_cache_dir.mkdir(parents=True, exist_ok=True)
            path = self._cache_path(spreadsheet_key)
            temporary = path.with_suffix(f".{os.getpid()}.tmp")
            payload = {
                "version": 1,
                "spreadsheet_key": spreadsheet_key,
                "fetched_at": entry.fetched_at,
                "worksheets": [
                    {
                        "title": sheet.title,
                        "rows": [list(row) for row in sheet.rows],
                    }
                    for sheet in entry.worksheets
                ],
            }
            temporary.write_text(
                json.dumps(payload, separators=(",", ":")), encoding="utf-8"
            )
            temporary.replace(path)
        except OSError as error:
            self._warning(f"Unable to persist Google Sheets cache: {error}")

    def _read_disk_cache(self, spreadsheet_key: str) -> _CacheEntry | None:
        try:
            payload = json.loads(
                self._cache_path(spreadsheet_key).read_text(encoding="utf-8")
            )
            if (
                payload.get("version") != 1
                or payload.get("spreadsheet_key") != spreadsheet_key
            ):
                return None
            entry = _CacheEntry(
                fetched_at=float(payload["fetched_at"]),
                worksheets=tuple(
                    WorksheetSnapshot(
                        title=str(sheet["title"]),
                        rows=tuple(
                            tuple(str(value) for value in row)
                            for row in sheet["rows"]
                        ),
                    )
                    for sheet in payload["worksheets"]
                ),
            )
            if time.time() - entry.fetched_at > self.stale_ttl:
                return None
            return entry
        except (
            FileNotFoundError,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            return None

    async def _load_and_store(
        self, spreadsheet_key: str
    ) -> tuple[WorksheetSnapshot, ...]:
        lock = self._locks.setdefault(spreadsheet_key, asyncio.Lock())
        async with lock:
            worksheets = await asyncio.to_thread(self._load_workbook, spreadsheet_key)
            entry = _CacheEntry(time.time(), worksheets)
            self._cache[spreadsheet_key] = entry
            await asyncio.to_thread(self._write_disk_cache, spreadsheet_key, entry)
            self._info(f"Cached Google workbook {spreadsheet_key}")
            return worksheets

    async def _refresh(self, spreadsheet_key: str) -> tuple[WorksheetSnapshot, ...]:
        """Coalesce simultaneous loads of the same workbook into one task."""
        task = self._load_tasks.get(spreadsheet_key)
        if task is None or task.done():
            task = asyncio.create_task(self._load_and_store(spreadsheet_key))
            self._load_tasks[spreadsheet_key] = task
        try:
            return await asyncio.shield(task)
        finally:
            if task.done() and self._load_tasks.get(spreadsheet_key) is task:
                self._load_tasks.pop(spreadsheet_key, None)

    def _schedule_refresh(self, spreadsheet_key: str) -> None:
        task = self._refresh_tasks.get(spreadsheet_key)
        if task is not None and not task.done():
            return

        async def runner():
            try:
                await self._refresh(spreadsheet_key)
            except Exception as error:
                self._warning(
                    f"Unable to refresh Google workbook {spreadsheet_key}: {error}"
                )
            finally:
                self._refresh_tasks.pop(spreadsheet_key, None)

        self._refresh_tasks[spreadsheet_key] = asyncio.create_task(runner())

    async def _scheduled_refresh_loop(self) -> None:
        while True:
            await asyncio.sleep(self.refresh_interval)
            keys = sorted(self._registered)
            results = await asyncio.gather(
                *(self.refresh(key) for key in sorted(self._registered)),
                return_exceptions=True,
            )
            for key, result in zip(keys, results):
                if isinstance(result, Exception):
                    self._warning(
                        f"Scheduled Google workbook refresh failed for {key}: {result}"
                    )

    async def refresh(self, spreadsheet_key: str) -> tuple[WorksheetSnapshot, ...]:
        """Force and await an authoritative refresh from Google Sheets."""
        self.register_workbook(spreadsheet_key)
        return await self._refresh(spreadsheet_key)

    async def worksheets(
        self, spreadsheet_key: str, *, refresh: bool = False
    ) -> tuple[WorksheetSnapshot, ...]:
        self.register_workbook(spreadsheet_key)
        if refresh:
            return await self.refresh(spreadsheet_key)

        entry = self._cache.get(spreadsheet_key)
        if entry is None:
            entry = await asyncio.to_thread(self._read_disk_cache, spreadsheet_key)
            if entry is not None:
                self._cache[spreadsheet_key] = entry
        if entry is not None:
            age = time.time() - entry.fetched_at
            if age <= self.cache_ttl:
                return entry.worksheets
            if age <= self.stale_ttl:
                if self.refresh_in_background and self.available:
                    self._schedule_refresh(spreadsheet_key)
                return entry.worksheets

        return await self._refresh(spreadsheet_key)

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


async def refresh_command(
    ctx, service: GoogleSheetsService, spreadsheet_key: str, label: str
) -> bool:
    """Refresh a module cache for a Discord or stream moderator."""
    request = getattr(ctx, "request", None)
    actor_metadata = getattr(getattr(request, "actor", None), "metadata", {})
    portable_roles = {
        str(role).casefold()
        for role in getattr(getattr(request, "actor", None), "roles", ())
    }
    permissions = getattr(getattr(ctx, "author", None), "guild_permissions", None)
    permitted = bool(
        portable_roles & {"moderator", "broadcaster"}
        or actor_metadata.get("manage_guild") is True
        or actor_metadata.get("administrator") is True
        or (
            permissions
            and (permissions.manage_guild or permissions.administrator)
        )
    )
    if not permitted:
        await ctx.send(
            "⛔ Only a server administrator, stream moderator, or broadcaster "
            "can refresh command data."
        )
        return False
    try:
        await service.refresh(spreadsheet_key)
    except GoogleSheetsError as error:
        await ctx.send(f"❌ {label} data refresh failed: {error}")
        return False
    await ctx.send(f"✅ {label} data was refreshed from Google Sheets.")
    return True


def get_google_sheets_service(bot) -> GoogleSheetsService:
    """Return the single Sheets service shared by every cog."""
    service = getattr(bot, "google_sheets", None)
    if service is None:
        sheets_config = bot.config.get("google_sheets", {})
        service = GoogleSheetsService(
            credentials_file=sheets_config.get("credentials_file"),
            cache_ttl=int(sheets_config.get("cache_ttl", 21600)),
            stale_ttl=int(sheets_config.get("stale_ttl", 604800)),
            persistent_cache_dir=sheets_config.get("persistent_cache_dir"),
            preload=bool(sheets_config.get("preload", True)),
            refresh_in_background=bool(
                sheets_config.get("refresh_in_background", True)
            ),
            refresh_interval=int(sheets_config.get("refresh_interval", 21600)),
            logger=getattr(bot, "logger", None),
        )
        bot.google_sheets = service
    return service
