from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
from typing import BinaryIO, Protocol


class MediaStoragePort(Protocol):
    """Byte-oriented media store keyed by relative asset paths (POSIX)."""

    def list_media_keys(self) -> list[str]:
        """Return sorted relative keys for importable media files (no sidecars)."""

    def exists(self, key: str) -> bool: ...

    def read_bytes(self, key: str) -> bytes: ...

    def put_bytes(self, key: str, data: bytes, *, content_type: str | None = None) -> None:
        """Create or overwrite object at key."""

    def delete(self, key: str) -> None:
        """Remove object if present (no error if missing)."""

    def open_stream(self, key: str) -> BinaryIO:
        """Open a readable binary stream for key. Caller closes."""

    def materialize(self, key: str, dest_dir: Path) -> AbstractContextManager[Path]:
        """
        Provide a local filesystem path for probe/ffmpeg.

        Yields a Path under dest_dir (or equivalent). May download then clean up.
        """
