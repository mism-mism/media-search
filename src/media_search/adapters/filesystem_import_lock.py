from __future__ import annotations

import json
import time
from pathlib import Path

from media_search.ports.import_lock import ImportLockBusy


class FilesystemImportLock:
    """Single-writer lock via an atomic lock file with TTL."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def try_acquire(self, holder: str, *, ttl_seconds: int = 7200) -> bool:
        now = time.time()
        if self._path.is_file():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                exp = float(data.get("expires_at", 0))
                current = str(data.get("holder", ""))
                if exp > now and current and current != holder:
                    return False
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                pass
        payload = {
            "holder": holder,
            "expires_at": now + ttl_seconds,
            "acquired_at": now,
        }
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        tmp.replace(self._path)
        # Re-read to detect lost race (best-effort).
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return str(data.get("holder")) == holder
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return False

    def release(self, holder: str) -> None:
        if not self._path.is_file():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if str(data.get("holder")) != holder:
                return
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return
        self._path.unlink(missing_ok=True)

    def current_holder(self) -> str | None:
        if not self._path.is_file():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if float(data.get("expires_at", 0)) <= time.time():
                return None
            holder = str(data.get("holder") or "")
            return holder or None
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return None


def require_acquire(lock: FilesystemImportLock, holder: str, *, ttl_seconds: int = 7200) -> None:
    if not lock.try_acquire(holder, ttl_seconds=ttl_seconds):
        current = lock.current_holder() or "unknown"
        raise ImportLockBusy(current)
