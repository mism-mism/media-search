from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from media_search.application.frame_paths import frame_cache_path
from media_search.domain.frames import MAX_REPRESENTATIVE_FRAMES


class LocalFrameStore:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, frame_key: str) -> Path:
        path = frame_cache_path(self._root, frame_key).resolve()
        path.relative_to(self._root)
        return path

    def put_jpeg(self, frame_key: str, data: bytes) -> None:
        path = self._path(frame_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def open_stream(self, frame_key: str) -> BinaryIO:
        path = self._path(frame_key)
        if not path.is_file():
            raise FileNotFoundError(frame_key)
        return path.open("rb")

    def exists(self, frame_key: str) -> bool:
        try:
            return self._path(frame_key).is_file()
        except ValueError:
            return False

    def delete_prefix(self, asset_id: str, *, max_frames: int = MAX_REPRESENTATIVE_FRAMES) -> None:
        for i in range(max_frames):
            path = frame_cache_path(self._root, f"{asset_id}::{i}")
            if path.is_file():
                path.unlink()
