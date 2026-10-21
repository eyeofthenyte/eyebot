"""Validation and durable state for Discord and livestream polls."""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import emoji as unicode_emoji


MAX_DURATION = timedelta(days=30)
PORTABLE_DURATION_RE = re.compile(r"^(?P<amount>[0-9]+)(?P<unit>[mMhHdD]?)$")


class PollError(ValueError):
    """A poll validation or state-transition error safe to show to users."""


def normalize_builtin_emoji(value: str) -> str | None:
    """Return one Unicode emoji from a pasted glyph or recognized shortcode."""
    selected = str(value or "").strip()
    converted = unicode_emoji.emojize(selected, language="alias")
    return converted if unicode_emoji.is_emoji(converted) else None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_duration(amount: int, unit: str = "minutes") -> timedelta:
    try:
        amount = int(amount)
    except (TypeError, ValueError) as error:
        raise PollError("Duration must be a whole number.") from error
    if amount < 1:
        raise PollError("Duration must be at least 1 minute.")
    normalized = str(unit).strip().casefold()
    multipliers = {
        "m": 1, "minute": 1, "minutes": 1,
        "h": 60, "hour": 60, "hours": 60,
        "d": 1440, "day": 1440, "days": 1440,
    }
    if normalized not in multipliers:
        raise PollError("Duration unit must be minutes, hours, or days.")
    duration = timedelta(minutes=amount * multipliers[normalized])
    if duration > MAX_DURATION:
        raise PollError("Poll duration cannot exceed 30 days.")
    return duration


def parse_portable_duration(value: str) -> timedelta:
    match = PORTABLE_DURATION_RE.fullmatch(str(value or "").strip())
    if not match:
        raise PollError("Duration must be a number, optionally followed by m, h, or d.")
    return parse_duration(int(match.group("amount")), match.group("unit") or "m")


def format_duration(duration: timedelta) -> str:
    minutes = int(duration.total_seconds() // 60)
    if minutes % 1440 == 0:
        amount, label = minutes // 1440, "day"
    elif minutes % 60 == 0:
        amount, label = minutes // 60, "hour"
    else:
        amount, label = minutes, "minute"
    return f"{amount} {label}{'' if amount == 1 else 's'}"


def format_portable_results(title: str, options, votes) -> str:
    counts = Counter(int(choice) for choice in votes)
    highest = max(counts.values(), default=0)
    winners = [
        f"{index}-{option} ({counts[index]} vote{'s' if counts[index] != 1 else ''})"
        for index, option in enumerate(options, 1)
        if counts[index] == highest
    ]
    return (
        f"Poll - {title} - has ended. "
        f"Top result{'s' if len(winners) != 1 else ''}: " + ", ".join(winners)
    )


def parse_portable_poll(raw_content: str, prefix: str = "!") -> tuple[timedelta, str, str, tuple[str, ...]]:
    content = str(raw_content or "").strip()
    command_prefix = f"{prefix}poll"
    if not content.casefold().startswith(command_prefix.casefold()):
        raise PollError("Poll command is invalid.")
    remainder = content[len(command_prefix):].strip()
    duration_text, separator, fields_text = remainder.partition(" ")
    if not separator:
        raise PollError("Use: !poll <duration> <title>, <description>, <option 1>, <option 2> ...")
    fields = tuple(part.strip() for part in fields_text.split(","))
    if len(fields) < 4:
        raise PollError("A title, description, and at least two comma-separated options are required.")
    if len(fields) > 7:
        raise PollError("A poll can contain at most five options.")
    title, description, *options = fields
    validate_poll_text(title, description, options)
    return parse_portable_duration(duration_text), title, description, tuple(options)


def validate_poll_text(title: str, description: str, options) -> tuple[str, str, tuple[str, ...]]:
    title = str(title or "").strip()
    description = str(description or "").strip()
    selected = tuple(str(option or "").strip() for option in options if str(option or "").strip())
    if not title:
        raise PollError("Poll title is required.")
    if len(title) > 200:
        raise PollError("Poll title cannot exceed 200 characters.")
    if not description:
        raise PollError("Poll description is required.")
    if len(description) > 2000:
        raise PollError("Poll description cannot exceed 2,000 characters.")
    if not 2 <= len(selected) <= 5:
        raise PollError("A poll requires between two and five options.")
    if any(len(option) > 300 for option in selected):
        raise PollError("Each poll option must be 300 characters or fewer.")
    if len({option.casefold() for option in selected}) != len(selected):
        raise PollError("Poll options must be unique.")
    return title, description, selected


@dataclass
class Poll:
    id: str
    guild_id: str
    channel_id: str
    creator_id: str
    title: str
    description: str
    options: list[str]
    emojis: list[str]
    created_at: str
    ends_at: str
    status: str = "active"
    message_id: str | None = None
    mod_channel_id: str | None = None
    mod_message_id: str | None = None
    results: list[int] = field(default_factory=list)
    votes: dict[str, int] = field(default_factory=dict)
    ended_at: str | None = None
    canceled_at: str | None = None
    published_at: str | None = None

    @classmethod
    def from_dict(cls, value):
        allowed = cls.__dataclass_fields__
        selected = {key: item for key, item in value.items() if key in allowed}
        for key in (
            "guild_id", "channel_id", "creator_id", "message_id",
            "mod_channel_id", "mod_message_id",
        ):
            if selected.get(key) is not None:
                selected[key] = str(selected[key])
        return cls(**selected)

    def to_dict(self):
        return asdict(self)


class PollService:
    """Atomic JSON poll storage shared by the Discord cog's timer and buttons."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.path = self.root / "polls.json"
        self._lock = threading.RLock()
        self.root.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict:
        if not self.path.exists():
            return {"polls": {}}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise PollError("The poll store could not be loaded.") from error
        if not isinstance(value, dict) or not isinstance(value.get("polls"), dict):
            raise PollError("The poll store is invalid.")
        return value

    def _write(self, value: dict) -> None:
        descriptor, name = tempfile.mkstemp(dir=self.root, prefix=".polls-", suffix=".tmp", text=True)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(value, output, indent=2, sort_keys=True)
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    def create(self, *, guild_id, channel_id, creator_id, title, description, options, emojis, duration, mod_channel_id=None) -> Poll:
        title, description, options = validate_poll_text(title, description, options)
        duration = parse_duration(int(duration.total_seconds() // 60), "minutes")
        selected_emojis = tuple(str(emoji or "").strip() for emoji in emojis)
        if len(selected_emojis) != len(options) or any(not emoji for emoji in selected_emojis):
            raise PollError("Every poll option requires an emoji.")
        if len(set(selected_emojis)) != len(selected_emojis):
            raise PollError("Each poll option must use a different emoji.")
        now = utc_now()
        poll = Poll(
            id=uuid4().hex,
            guild_id=str(guild_id), channel_id=str(channel_id), creator_id=str(creator_id),
            title=title, description=description, options=list(options), emojis=list(selected_emojis),
            created_at=now.isoformat(), ends_at=(now + duration).isoformat(),
            mod_channel_id=str(mod_channel_id) if mod_channel_id else None,
            results=[0] * len(options),
        )
        with self._lock:
            store = self._read()
            store["polls"][poll.id] = poll.to_dict()
            self._write(store)
        return poll

    def get(self, poll_id: str) -> Poll:
        with self._lock:
            value = self._read()["polls"].get(str(poll_id))
        if not isinstance(value, dict):
            raise PollError("Poll was not found.")
        return Poll.from_dict(value)

    def list(self, *, status: str | None = None) -> tuple[Poll, ...]:
        with self._lock:
            polls = tuple(Poll.from_dict(value) for value in self._read()["polls"].values())
        return tuple(poll for poll in polls if status is None or poll.status == status)

    def find_active_by_message(self, message_id) -> Poll | None:
        selected = str(message_id)
        return next(
            (
                poll for poll in self.list(status="active")
                if poll.message_id is not None and str(poll.message_id) == selected
            ),
            None,
        )

    def record_vote(self, poll_id, user_id, option_index: int) -> bool:
        """Record a user's first selection and reject all later selections."""
        with self._lock:
            store = self._read()
            value = store["polls"].get(str(poll_id))
            if not isinstance(value, dict):
                raise PollError("Poll was not found.")
            if value.get("status") != "active":
                return False
            selected = int(option_index)
            if not 0 <= selected < len(value.get("options", ())):
                raise PollError("Poll option is invalid.")
            votes = value.setdefault("votes", {})
            voter = str(user_id)
            if voter in votes:
                return False
            votes[voter] = selected
            self._write(store)
            return True

    def remove_vote(self, poll_id, user_id, option_index: int) -> bool:
        """Clear a vote only when the user removed their currently selected option."""
        with self._lock:
            store = self._read()
            value = store["polls"].get(str(poll_id))
            if not isinstance(value, dict):
                raise PollError("Poll was not found.")
            if value.get("status") != "active":
                return False
            votes = value.setdefault("votes", {})
            voter = str(user_id)
            if int(votes.get(voter, -1)) != int(option_index):
                return False
            del votes[voter]
            self._write(store)
            return True

    def update_delivery(self, poll_id, **fields) -> Poll:
        allowed = {"message_id", "mod_channel_id", "mod_message_id"}
        if set(fields) - allowed:
            raise PollError("Invalid poll delivery update.")
        normalized = {
            key: str(value) if value is not None else None
            for key, value in fields.items()
        }
        return self._transition(poll_id, None, **normalized)

    def cancel(self, poll_id) -> Poll:
        return self._transition(poll_id, "active", status="canceled", canceled_at=utc_now().isoformat())

    def end(self, poll_id, results) -> Poll:
        poll = self.get(poll_id)
        selected = [max(0, int(value)) for value in results]
        if len(selected) != len(poll.options):
            raise PollError("Poll result count does not match its options.")
        return self._transition(poll_id, "active", status="ended", results=selected, ended_at=utc_now().isoformat())

    def publish(self, poll_id) -> Poll:
        return self._transition(poll_id, "ended", status="published", published_at=utc_now().isoformat())

    def due(self, now=None) -> tuple[Poll, ...]:
        selected = now or utc_now()
        return tuple(poll for poll in self.list(status="active") if datetime.fromisoformat(poll.ends_at) <= selected)

    def _transition(self, poll_id, required_status, **fields) -> Poll:
        with self._lock:
            store = self._read()
            value = store["polls"].get(str(poll_id))
            if not isinstance(value, dict):
                raise PollError("Poll was not found.")
            if required_status and value.get("status") != required_status:
                raise PollError(f"Poll is already {value.get('status', 'closed')}.")
            value.update(fields)
            store["polls"][str(poll_id)] = value
            self._write(store)
            return Poll.from_dict(value)
