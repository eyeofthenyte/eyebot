"""Durable per-platform job queue shared by Discord and connector children."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class PlatformJobService:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def enqueue(self, guild_id, platform, operation, payload) -> str:
        job_id = str(uuid4())
        directory = self.root / platform
        directory.mkdir(parents=True, exist_ok=True)
        job = {
            "id": job_id,
            "guild_id": str(guild_id),
            "platform": platform,
            "operation": operation,
            "payload": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "attempts": 0,
        }
        descriptor, temporary_name = tempfile.mkstemp(dir=directory, suffix=".tmp")
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(job, output)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, directory / f"{job_id}.json")
        finally:
            temporary.unlink(missing_ok=True)
        return job_id

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
