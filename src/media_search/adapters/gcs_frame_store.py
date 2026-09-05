from __future__ import annotations

import json
import time
from typing import BinaryIO
from io import BytesIO

from media_search.domain.frames import MAX_REPRESENTATIVE_FRAMES
from media_search.ports.import_lock import ImportLockBusy


def _safe_frame_blob(frame_key: str) -> str:
    parts = [p for p in frame_key.replace("\\", "/").split("/") if p and p != "."]
    if not parts or any(p == ".." for p in parts):
        raise ValueError(f"invalid frame key: {frame_key!r}")
    # Keep :: for frame index but flatten path separators.
    return "__".join(parts).replace("::", "__")


class GcsFrameStore:
    def __init__(self, *, bucket_name: str, prefix: str = "frames") -> None:
        from google.cloud import storage as gcs

        self._client = gcs.Client()
        self._bucket = self._client.bucket(bucket_name)
        self._prefix = prefix.strip("/")

    def _blob_name(self, frame_key: str) -> str:
        safe = _safe_frame_blob(frame_key)
        return f"{self._prefix}/{safe}.jpg" if self._prefix else f"{safe}.jpg"

    def put_jpeg(self, frame_key: str, data: bytes) -> None:
        self._bucket.blob(self._blob_name(frame_key)).upload_from_string(
            data, content_type="image/jpeg"
        )

    def open_stream(self, frame_key: str) -> BinaryIO:
        blob = self._bucket.blob(self._blob_name(frame_key))
        if not blob.exists():
            raise FileNotFoundError(frame_key)
        return BytesIO(blob.download_as_bytes())

    def exists(self, frame_key: str) -> bool:
        return self._bucket.blob(self._blob_name(frame_key)).exists()

    def delete_prefix(self, asset_id: str, *, max_frames: int = MAX_REPRESENTATIVE_FRAMES) -> None:
        for i in range(max_frames):
            blob = self._bucket.blob(self._blob_name(f"{asset_id}::{i}"))
            if blob.exists():
                blob.delete()


class GcsImportLock:
    """Lock object in GCS with TTL payload (best-effort single writer)."""

    def __init__(self, *, bucket_name: str, object_name: str = "state/import.lock.json") -> None:
        from google.cloud import storage as gcs

        self._client = gcs.Client()
        self._bucket = self._client.bucket(bucket_name)
        self._object_name = object_name.lstrip("/")

    def try_acquire(self, holder: str, *, ttl_seconds: int = 7200) -> bool:
        now = time.time()
        blob = self._bucket.blob(self._object_name)
        if blob.exists():
            try:
                data = json.loads(blob.download_as_text())
                exp = float(data.get("expires_at", 0))
                current = str(data.get("holder", ""))
                if exp > now and current and current != holder:
                    return False
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                pass
        payload = json.dumps(
            {"holder": holder, "expires_at": now + ttl_seconds, "acquired_at": now}
        )
        blob.upload_from_string(payload, content_type="application/json")
        try:
            data = json.loads(blob.download_as_text())
            return str(data.get("holder")) == holder
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return False

    def release(self, holder: str) -> None:
        blob = self._bucket.blob(self._object_name)
        if not blob.exists():
            return
        try:
            data = json.loads(blob.download_as_text())
            if str(data.get("holder")) != holder:
                return
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return
        blob.delete()

    def current_holder(self) -> str | None:
        blob = self._bucket.blob(self._object_name)
        if not blob.exists():
            return None
        try:
            data = json.loads(blob.download_as_text())
            if float(data.get("expires_at", 0)) <= time.time():
                return None
            holder = str(data.get("holder") or "")
            return holder or None
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return None


def require_gcs_acquire(lock: GcsImportLock, holder: str, *, ttl_seconds: int = 7200) -> None:
    if not lock.try_acquire(holder, ttl_seconds=ttl_seconds):
        raise ImportLockBusy(lock.current_holder() or "unknown")
