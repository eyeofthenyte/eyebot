"""Durable per-platform job queue shared by Discord and connector children."""

from __future__ import annotations

import json
import hashlib
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


IDEMPOTENCY_RETENTION_SECONDS = 30 * 24 * 60 * 60


class DuplicateJobError(ValueError):
    """The same external source has already queued this platform job."""


class PlatformJobService:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def enqueue(
        self,
        guild_id,
        platform,
        operation,
        payload,
        *,
        idempotency_key: str | None = None,
        source_message_id: str | None = None,
    ) -> str:
        job_id = str(uuid4())
        directory = self.root / platform
        directory.mkdir(parents=True, exist_ok=True)
        marker = None
        if idempotency_key:
            marker = self._reserve_idempotency(idempotency_key, job_id)
        job = {
            "id": job_id,
            "guild_id": str(guild_id),
            "platform": platform,
            "operation": operation,
            "payload": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "attempts": 0,
        }
        if source_message_id is not None:
            job["source_message_id"] = str(source_message_id)
        descriptor, temporary_name = tempfile.mkstemp(dir=directory, suffix=".tmp")
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(job, output)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, directory / f"{job_id}.json")
        except Exception:
            if marker is not None:
                marker.unlink(missing_ok=True)
            raise
        finally:
            temporary.unlink(missing_ok=True)
        return job_id

    def _reserve_idempotency(self, key: str, job_id: str) -> Path:
        directory = self.root / ".idempotency"
        directory.mkdir(parents=True, exist_ok=True)
        cutoff = time.time() - IDEMPOTENCY_RETENTION_SECONDS
        for stale in directory.glob("*.json"):
            try:
                if stale.stat().st_mtime < cutoff:
                    stale.unlink(missing_ok=True)
            except OSError:
                continue
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        marker = directory / f"{digest}.json"
        try:
            descriptor = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as error:
            raise DuplicateJobError("This message is already queued for that platform") from error
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump({"key": key, "job_id": job_id, "created_at": time.time()}, output)
        return marker

    def cancel_pending(self, guild_id, source_message_id) -> list[dict]:
        """Remove unclaimed jobs originating from one Discord message."""
        removed = []
        for directory in self.root.iterdir() if self.root.is_dir() else ():
            if not directory.is_dir() or directory.name.startswith("."):
                continue
            for path in directory.glob("*.json"):
                try:
                    job = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if (
                    str(job.get("guild_id")) == str(guild_id)
                    and str(job.get("source_message_id")) == str(source_message_id)
                ):
                    path.unlink(missing_ok=True)
                    self._release_idempotency(job.get("id"))
                    removed.append(job)
        return removed

    def _release_idempotency(self, job_id) -> None:
        directory = self.root / ".idempotency"
        if not directory.is_dir():
            return
        for marker in directory.glob("*.json"):
            try:
                value = json.loads(marker.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if str(value.get("job_id")) == str(job_id):
                marker.unlink(missing_ok=True)

    def claim_next(self, platform):
        directory = self.root / platform
        if not directory.is_dir():
            return None
        for path in sorted(directory.glob("*.json")):
            claimed = path.with_suffix(".processing")
            try:
                os.replace(path, claimed)
                job = json.loads(claimed.read_text(encoding="utf-8"))
                return claimed, job
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                continue
        return None

    @staticmethod
    def complete(claimed: Path) -> None:
        claimed.unlink(missing_ok=True)

    @staticmethod
    def fail(claimed: Path, job: dict, error: Exception, *, max_attempts=3) -> bool:
        job["attempts"] = int(job.get("attempts", 0)) + 1
        job["last_error"] = str(error)[:500]
        if job["attempts"] >= max_attempts:
            destination = claimed.with_suffix(".failed")
        else:
            destination = claimed.with_suffix(".json")
        claimed.write_text(json.dumps(job), encoding="utf-8")
        os.replace(claimed, destination)
        return job["attempts"] >= max_attempts
