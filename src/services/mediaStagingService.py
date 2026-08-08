"""Validate and persist Discord attachments before social workers consume them."""

from __future__ import annotations

import os
import re
from pathlib import Path
from uuid import uuid4


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
MAX_IMAGE_BYTES = 5_000_000
MAX_IMAGES = 4
SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")


def _matches_image_type(payload: bytes, content_type: str) -> bool:
    if content_type == "image/jpeg":
        return payload.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return payload.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/gif":
        return payload.startswith((b"GIF87a", b"GIF89a"))
    if content_type == "image/webp":
        return payload.startswith(b"RIFF") and payload[8:12] == b"WEBP"
    return False


class MediaStagingService:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    async def stage_images(self, platform, attachments, *, alt_text=""):
        selected = list(attachments)
        if not 1 <= len(selected) <= MAX_IMAGES:
            raise ValueError(f"Attach or reply to 1-{MAX_IMAGES} images")
        batch = self.root / platform / str(uuid4())
        batch.mkdir(parents=True, exist_ok=False)
        staged = []
        try:
            for index, attachment in enumerate(selected, 1):
                content_type = str(getattr(attachment, "content_type", "") or "").casefold()
                if content_type not in ALLOWED_IMAGE_TYPES:
                    raise ValueError(
                        "Images must be JPEG, PNG, GIF, or WebP files"
                    )
                declared_size = int(getattr(attachment, "size", 0) or 0)
                if declared_size <= 0 or declared_size > MAX_IMAGE_BYTES:
                    raise ValueError(
                        f"Each image must be between 1 byte and {MAX_IMAGE_BYTES} bytes"
                    )
                payload = await attachment.read()
                if len(payload) != declared_size or len(payload) > MAX_IMAGE_BYTES:
                    raise ValueError("Attachment size changed or exceeded the limit")
                if not _matches_image_type(payload, content_type):
                    raise ValueError("Attachment contents do not match its image type")
                original = SAFE_NAME.sub("_", str(getattr(attachment, "filename", "image")))
                filename = f"{index}-{original[:100]}"
                if not Path(filename).suffix:
                    filename += ALLOWED_IMAGE_TYPES[content_type]
                path = batch / filename
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, "wb") as output:
                    output.write(payload)
                    output.flush()
                    os.fsync(output.fileno())
                staged.append(
                    {
                        "path": str(path),
                        "content_type": content_type,
                        "alt_text": alt_text[:1000],
                    }
                )
            return staged
        except Exception:
            for path in batch.glob("*"):
                path.unlink(missing_ok=True)
            batch.rmdir()
            raise

    def remove(self, staged):
        parents = set()
        for item in staged or ():
            path = Path(str(item.get("path") or "")).resolve()
            if self.root not in path.parents:
                continue
            parents.add(path.parent)
            path.unlink(missing_ok=True)
        for parent in parents:
            try:
                parent.rmdir()
            except OSError:
                pass
