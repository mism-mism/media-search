from __future__ import annotations

from pathlib import Path

SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
SUPPORTED_VIDEO_SUFFIXES = {".mp4"}


def classify_path(path: Path) -> str | None:
    """Return 'image', 'video', or None if unsupported for AC."""
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_IMAGE_SUFFIXES:
        return "image"
    if suffix in SUPPORTED_VIDEO_SUFFIXES:
        return "video"
    return None
