from __future__ import annotations

from typing import BinaryIO, Protocol


class FrameStorePort(Protocol):
    """Durable store for representative-frame JPEG bytes keyed by frame_key."""

    def put_jpeg(self, frame_key: str, data: bytes) -> None: ...

    def open_stream(self, frame_key: str) -> BinaryIO:
        """Open readable JPEG stream. Caller closes. Raises FileNotFoundError."""

    def exists(self, frame_key: str) -> bool: ...

    def delete_prefix(self, asset_id: str, *, max_frames: int = 8) -> None:
        """Delete frame keys ``{asset_id}::{i}`` for i in range(max_frames)."""
