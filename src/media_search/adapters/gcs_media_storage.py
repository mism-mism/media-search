from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator


class GcsMediaStorage:
    """GCS-backed media store. Keys are object names relative to prefix."""

    def __init__(self, *, bucket_name: str, prefix: str = "") -> None:
        from google.cloud import storage as gcs

        self._client = gcs.Client()
        self._bucket = self._client.bucket(bucket_name)
        self._prefix = prefix.strip("/")

    def _blob_name(self, key: str) -> str:
        key = self._safe_key(key)
        if not self._prefix:
            return key
        return f"{self._prefix}/{key}"

    def list_media_keys(self) -> list[str]:
        prefix = f"{self._prefix}/" if self._prefix else ""
        keys: list[str] = []
        list_kwargs = {"prefix": prefix} if prefix else {}
        for blob in self._client.list_blobs(self._bucket, **list_kwargs):
            name = blob.name
            if prefix and not name.startswith(prefix):
                continue
            rel = name[len(prefix) :] if prefix else name
            if not rel or rel.endswith("/"):
                continue
            if rel.endswith(".meta.json"):
                continue
            keys.append(rel)
        return sorted(keys)

    def exists(self, key: str) -> bool:
        return self._bucket.blob(self._blob_name(key)).exists()

    def size_bytes(self, key: str) -> int:
        blob = self._bucket.blob(self._blob_name(key))
        blob.reload()
        size = blob.size
        if size is None:
            raise FileNotFoundError(key)
        return int(size)

    def read_bytes(self, key: str) -> bytes:
        return self._bucket.blob(self._blob_name(key)).download_as_bytes()

    def put_bytes(self, key: str, data: bytes, *, content_type: str | None = None) -> None:
        blob = self._bucket.blob(self._blob_name(key))
        blob.upload_from_string(data, content_type=content_type or "application/octet-stream")

    def delete(self, key: str) -> None:
        blob = self._bucket.blob(self._blob_name(key))
        if blob.exists():
            blob.delete()
        meta = self._bucket.blob(self._blob_name(f"{key}.meta.json"))
        if meta.exists():
            meta.delete()

    def open_stream(self, key: str) -> BinaryIO:
        from io import BytesIO

        return BytesIO(self.read_bytes(key))

    @staticmethod
    def _safe_key(key: str) -> str:
        parts = [p for p in key.replace("\\", "/").split("/") if p and p != "."]
        if not parts or any(p == ".." for p in parts):
            raise ValueError(f"invalid media key: {key!r}")
        return "/".join(parts)

    @contextmanager
    def materialize(self, key: str, dest_dir: Path) -> Iterator[Path]:
        key = self._safe_key(key)
        dest = dest_dir / key
        dest = dest.resolve()
        dest_dir = dest_dir.resolve()
        dest.relative_to(dest_dir)
        dest.parent.mkdir(parents=True, exist_ok=True)
        self._bucket.blob(self._blob_name(key)).download_to_filename(str(dest))
        meta_key = f"{key}.meta.json"
        meta_blob = self._bucket.blob(self._blob_name(meta_key))
        meta_dest = dest_dir / f"{key}.meta.json"
        if meta_blob.exists():
            meta_dest.parent.mkdir(parents=True, exist_ok=True)
            meta_blob.download_to_filename(str(meta_dest))
        try:
            yield dest
        finally:
            if dest.exists():
                dest.unlink(missing_ok=True)
            if meta_dest.exists():
                meta_dest.unlink(missing_ok=True)
