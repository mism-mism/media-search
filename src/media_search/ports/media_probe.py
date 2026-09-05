from __future__ import annotations

from pathlib import Path
from typing import Protocol

from media_search.domain.media_asset import MediaAsset


class MediaProbePort(Protocol):
    """Probe media files and extract representative frames (infra details hidden)."""

    def build_asset(self, path: Path, *, import_root: Path) -> MediaAsset:
        """Build a MediaAsset from a filesystem path under import_root."""

    def extract_frame_jpeg(
        self,
        path: Path,
        *,
        position: float,
        duration_seconds: float,
        dest: Path,
    ) -> None:
        """Write one JPEG frame at fractional position into dest."""
