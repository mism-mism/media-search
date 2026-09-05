from __future__ import annotations

import re
from pathlib import Path


def frame_cache_path(frame_root: Path, frame_key: str) -> Path:
    """Map frame_key to a safe on-disk JPEG path under frame_root."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", frame_key)
    return frame_root / f"{safe}.jpg"
