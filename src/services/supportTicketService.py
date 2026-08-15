"""Persistent, privacy-conscious state for Discord support tickets."""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import tempfile
import threading
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError


ACTIVE_STATUSES = frozenset({"open", "assigned"})
FINAL_STATUSES = frozenset({"resolved", "canceled"})
TICKET_PATTERN = re.compile(r"^TICKET-[0-9]{6}$")
MESSAGE_LINK_PATTERN = re.compile(
    r"^https://(?:canary\.|ptb\.)?discord(?:app)?\.com/channels/"
    r"(?P<guild>[0-9]{1,20})/(?P<channel>[0-9]{1,20})/(?P<message>[0-9]{1,20})$"
)
IMAGE_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


class SupportTicketError(ValueError):
    """A safe validation or state-transition failure."""


@dataclass(frozen=True)
class TicketImage:
    filename: str
    content_type: str
    data: bytes


@dataclass
class SupportTicket:
    number: str
    guild_id: str
    opener_id: str
    description: str
    message_link: str = ""
    status: str = "open"
    assigned_to: str | None = None
    opened_at: str = ""
    assigned_at: str | None = None
    closed_at: str | None = None
    closed_by: str | None = None
    public_message_id: str | None = None
    mod_message_id: str | None = None
    thread_id: str | None = None
    public_delete_at: str | None = None
    history: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value: dict) -> "SupportTicket":
        allowed = cls.__dataclass_fields__
        return cls(**{key: deepcopy(item) for key, item in value.items() if key in allowed})

    def to_dict(self) -> dict:
        return asdict(self)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_message_link(value: str | None, guild_id: str | int) -> str:
    selected = str(value or "").strip().rstrip("/>")
    if not selected:
        return ""
    match = MESSAGE_LINK_PATTERN.fullmatch(selected)
    if not match or match.group("guild") != str(guild_id):
        raise SupportTicketError(
            "The optional message link must be a Discord message from this server."
        )
    return selected


class SupportTicketService:
    """Own ticket validation, transitions, and atomic per-guild JSON files."""

    def __init__(self, settings, guild_config_dir, logger=None):
        self.settings = dict(settings or {})
        self.root = Path(guild_config_dir) / ".tickets"
        self.logger = logger
        self._lock = threading.RLock()
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            self.root.chmod(0o700)
        except OSError:
            pass

    @property
    def maximum_open_per_user(self) -> int:
        return max(1, min(10, int(self.settings.get("max_open_per_user", 3))))

    @property
    def maximum_images(self) -> int:
        return max(0, min(10, int(self.settings.get("max_images", 4))))

    def path(self, guild_id: str | int) -> Path:
        selected = str(guild_id)
        if not selected.isdecimal() or not 1 <= len(selected) <= 20:
            raise SupportTicketError("The Discord server ID is invalid.")
        return self.root / f"{selected}.json"

    @staticmethod
    def _blank() -> dict:
        return {"next_number": 1, "tickets": {}}

    def _read(self, guild_id: str | int) -> dict:
        path = self.path(guild_id)
        if not path.exists():
            return self._blank()
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or not isinstance(value.get("tickets"), dict):
                raise ValueError("ticket store must contain a tickets mapping")
            value["next_number"] = max(1, int(value.get("next_number", 1)))
            return value
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as error:
            backup = path.with_suffix(".json.bak")
            try:
                value = json.loads(backup.read_text(encoding="utf-8"))
                if not isinstance(value, dict) or not isinstance(value.get("tickets"), dict):
                    raise ValueError("ticket backup is invalid")
                self._write(guild_id, value, create_backup=False)
                if self.logger:
                    self.logger.info(
                        f"Recovered support ticket store from {backup}",
                        guild_id=guild_id,
                    )
                return value
            except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
                raise SupportTicketError(
                    "The server's support ticket store could not be loaded."
                ) from error

    def _write(self, guild_id: str | int, value: dict, *, create_backup=True) -> None:
        path = self.path(guild_id)
        if create_backup and path.is_file():
            backup = path.with_suffix(".json.bak")
            shutil.copy2(path, backup)
            try:
                backup.chmod(0o600)
            except OSError:
                pass
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.root,
            prefix=f".{path.stem}-",
            suffix=".tmp",
            text=True,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as destination:
                json.dump(value, destination, indent=2, sort_keys=True)
                destination.write("\n")
                destination.flush()
                os.fsync(destination.fileno())
            temporary.chmod(0o600)
            os.replace(temporary, path)
            try:
                path.chmod(0o600)
            except OSError:
                pass
        finally:
            if temporary.exists():
                temporary.unlink()

    def create(self, guild_id, opener_id, description, message_link="") -> SupportTicket:
        selected_description = str(description or "").strip()
        maximum = max(100, min(4000, int(self.settings.get("max_description_length", 4000))))
        if len(selected_description) < 10:
            raise SupportTicketError("The ticket description must contain at least 10 characters.")
        if len(selected_description) > maximum:
            raise SupportTicketError(f"The ticket description cannot exceed {maximum} characters.")
        selected_link = validate_message_link(message_link, guild_id)
        with self._lock:
            store = self._read(guild_id)
            active = [
                value for value in store["tickets"].values()
                if str(value.get("opener_id")) == str(opener_id)
                and value.get("status") in ACTIVE_STATUSES
            ]
            if len(active) >= self.maximum_open_per_user:
                raise SupportTicketError(
                    f"You may have at most {self.maximum_open_per_user} open support tickets."
                )
            sequence = store["next_number"]
            number = f"TICKET-{sequence:06d}"
            timestamp = utc_now()
            ticket = SupportTicket(
                number=number,
                guild_id=str(guild_id),
                opener_id=str(opener_id),
                description=selected_description,
                message_link=selected_link,
                opened_at=timestamp,
                history=[{"action": "opened", "actor_id": str(opener_id), "at": timestamp}],
            )
            store["next_number"] = sequence + 1
            store["tickets"][number] = ticket.to_dict()
            self._write(guild_id, store)
            return ticket

    def get(self, guild_id, number) -> SupportTicket:
        selected = str(number or "").strip().upper()
        if not TICKET_PATTERN.fullmatch(selected):
            raise SupportTicketError("Use a ticket number such as `TICKET-000001`.")
        with self._lock:
            value = self._read(guild_id)["tickets"].get(selected)
        if not isinstance(value, dict):
            raise SupportTicketError(f"Ticket `{selected}` was not found in this server.")
        return SupportTicket.from_dict(value)

    def list(self, guild_id, *, active_only=False) -> tuple[SupportTicket, ...]:
        with self._lock:
            values = tuple(self._read(guild_id)["tickets"].values())
        tickets = tuple(SupportTicket.from_dict(value) for value in values if isinstance(value, dict))
        if active_only:
            tickets = tuple(ticket for ticket in tickets if ticket.status in ACTIVE_STATUSES)
        return tuple(sorted(tickets, key=lambda ticket: ticket.number))

    def find_by_thread(self, guild_id, thread_id) -> SupportTicket | None:
        return next(
            (ticket for ticket in self.list(guild_id) if ticket.thread_id == str(thread_id)),
            None,
        )

    def update_delivery(self, guild_id, number, **identifiers) -> SupportTicket:
        allowed = {"public_message_id", "mod_message_id", "thread_id", "public_delete_at"}
        if set(identifiers) - allowed:
            raise SupportTicketError("An unsupported ticket delivery field was provided.")
        def change(ticket):
            for key, value in identifiers.items():
                setattr(ticket, key, str(value) if value is not None else None)

        return self._mutate(guild_id, number, change)

    def claim(self, guild_id, number, moderator_id) -> SupportTicket:
        def change(ticket):
            if ticket.status == "assigned" and ticket.assigned_to == str(moderator_id):
                return
            if ticket.status != "open":
                raise SupportTicketError(f"Ticket `{ticket.number}` is already {ticket.status}.")
            timestamp = utc_now()
            ticket.status = "assigned"
            ticket.assigned_to = str(moderator_id)
            ticket.assigned_at = timestamp
            ticket.history.append({"action": "assigned", "actor_id": str(moderator_id), "at": timestamp})
        return self._mutate(guild_id, number, change)

    def close(self, guild_id, number, moderator_id, status) -> SupportTicket:
        if status not in FINAL_STATUSES:
            raise SupportTicketError("The requested ticket state is invalid.")
        def change(ticket):
            if ticket.status in FINAL_STATUSES:
                if ticket.status == status:
                    return
                raise SupportTicketError(f"Ticket `{ticket.number}` is already {ticket.status}.")
            timestamp = utc_now()
            ticket.status = status
            ticket.closed_at = timestamp
            ticket.closed_by = str(moderator_id)
            ticket.history.append({"action": status, "actor_id": str(moderator_id), "at": timestamp})
        return self._mutate(guild_id, number, change)

    def reopen(self, guild_id, number, moderator_id) -> SupportTicket:
        with self._lock:
            store = self._read(guild_id)
            selected = str(number or "").strip().upper()
            value = store["tickets"].get(selected)
            if not isinstance(value, dict):
                raise SupportTicketError(
                    f"Ticket `{selected}` was not found in this server."
                )
            ticket = SupportTicket.from_dict(value)
            if ticket.status not in FINAL_STATUSES:
                raise SupportTicketError(f"Ticket `{ticket.number}` is not closed.")
            active_for_user = sum(
                1
                for current in store["tickets"].values()
                if str(current.get("opener_id")) == ticket.opener_id
                and current.get("status") in ACTIVE_STATUSES
            )
            if active_for_user >= self.maximum_open_per_user:
                raise SupportTicketError(
                    f"The ticket opener already has the maximum of "
                    f"{self.maximum_open_per_user} active tickets."
                )
            timestamp = utc_now()
            ticket.status = "open"
            ticket.assigned_to = None
            ticket.assigned_at = None
            ticket.closed_at = None
            ticket.closed_by = None
            ticket.thread_id = None
            ticket.public_delete_at = None
            ticket.history.append(
                {
                    "action": "reopened",
                    "actor_id": str(moderator_id),
                    "at": timestamp,
                }
            )
            store["tickets"][selected] = ticket.to_dict()
            self._write(guild_id, store)
            return ticket

    def _mutate(self, guild_id, number, callback) -> SupportTicket:
        with self._lock:
            store = self._read(guild_id)
            selected = str(number or "").strip().upper()
            value = store["tickets"].get(selected)
            if not isinstance(value, dict):
                raise SupportTicketError(f"Ticket `{selected}` was not found in this server.")
            ticket = SupportTicket.from_dict(value)
            callback(ticket)
            store["tickets"][selected] = ticket.to_dict()
            self._write(guild_id, store)
            return ticket

    def validate_images(self, images) -> tuple[TicketImage, ...]:
        selected = tuple(images)
        if len(selected) > self.maximum_images:
            raise SupportTicketError(f"A ticket may include at most {self.maximum_images} images.")
        maximum_each = max(1, int(self.settings.get("max_image_bytes", 5_242_880)))
        maximum_total = max(maximum_each, int(self.settings.get("max_total_image_bytes", 15_728_640)))
        maximum_pixels = max(
            1,
            min(100_000_000, int(self.settings.get("max_image_pixels", 40_000_000))),
        )
        total = 0
        validated = []
        for image in selected:
            suffix = Path(image.filename).suffix.casefold()
            expected = IMAGE_TYPES.get(suffix)
            if expected != image.content_type:
                raise SupportTicketError(f"Image `{image.filename}` has an invalid extension or content type.")
            if len(image.data) > maximum_each:
                raise SupportTicketError(f"Image `{image.filename}` exceeds the per-image size limit.")
            try:
                with Image.open(io.BytesIO(image.data)) as opened:
                    if opened.width * opened.height > maximum_pixels:
                        raise SupportTicketError(
                            f"Image `{image.filename}` exceeds the pixel limit."
                        )
                    opened.verify()
            except SupportTicketError:
                raise
            except (
                Image.DecompressionBombError,
                UnidentifiedImageError,
                OSError,
                ValueError,
            ) as error:
                raise SupportTicketError(f"Image `{image.filename}` is not a valid image file.") from error
            total += len(image.data)
            validated.append(image)
        if total > maximum_total:
            raise SupportTicketError("The combined images exceed the ticket size limit.")
        return tuple(validated)

    def sanitize_image(self, image: TicketImage) -> TicketImage:
        """Re-encode an image without EXIF or other metadata."""
        with Image.open(io.BytesIO(image.data)) as opened:
            output = io.BytesIO()
            suffix = Path(image.filename).suffix.casefold()
            if image.content_type == "image/gif":
                frames = []
                durations = []
                try:
                    while True:
                        opened.seek(len(frames))
                        frames.append(opened.convert("RGBA"))
                        durations.append(opened.info.get("duration", 100))
                except EOFError:
                    pass
                frames[0].save(
                    output,
                    format="GIF",
                    save_all=len(frames) > 1,
                    append_images=frames[1:],
                    duration=durations,
                    loop=0,
                )
            else:
                cleaned = ImageOps.exif_transpose(opened)
                if image.content_type == "image/jpeg":
                    cleaned.convert("RGB").save(output, format="JPEG", quality=95)
                elif image.content_type == "image/png":
                    cleaned.save(output, format="PNG")
                else:
                    cleaned.save(output, format="WEBP", quality=95)
            filename = Path(image.filename).name[:150] or f"ticket-image{suffix}"
            return TicketImage(filename, image.content_type, output.getvalue())
