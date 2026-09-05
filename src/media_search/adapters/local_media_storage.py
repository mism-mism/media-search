from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator


class LocalMediaStorage:
    """Filesystem media root; keys are paths relative to root."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    @property
    def root(self) -> Path:
        return self._root

    def _resolve(self, key: str) -> Path:
        path = (self._root / key).resolve()
        path.relative_to(self._root)
        return path

    def list_media_keys(self) -> list[str]:
        if not self._root.is_dir():
            return []
        keys: list[str] = []
        for path in sorted(self._root.rglob("*")):
            if not path.is_file():
                continue
            if path.name.endswith(".meta.json"):
                continue
            keys.append(path.relative_to(self._root).as_posix())
        return keys

    def exists(self, key: str) -> bool:
        try:
            return self._resolve(key).is_file()
        except ValueError:
            return False

    def read_bytes(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()

    def put_bytes(self, key: str, data: bytes, *, content_type: str | None = None) -> None:
        del content_type
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def delete(self, key: str) -> None:
        try:
            path = self._resolve(key)
        except ValueError:
            return
        if path.is_file():
            path.unlink()
        meta = path.parent / f"{path.name}.meta.json"
        if meta.is_file():
            meta.unlink()

    def open_stream(self, key: str) -> BinaryIO:
        return self._resolve(key).open("rb")

    @contextmanager
    def materialize(self, key: str, dest_dir: Path) -> Iterator[Path]:
        del dest_dir  # local files are already on disk
        path = self._resolve(key)
        if not path.is_file():
            raise FileNotFoundError(key)
        # Ensure sidecar is visible next to the file (already on disk).
        yield path
