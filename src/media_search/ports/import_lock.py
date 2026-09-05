from __future__ import annotations

from typing import Protocol


class ImportLockBusy(Exception):
    """Another import holder currently owns the single-writer lock."""

    def __init__(self, holder: str) -> None:
        self.holder = holder
        super().__init__(f"import lock held by {holder!r}")


class ImportLockPort(Protocol):
    """Cross-process single-writer lock for index mutation."""

    def try_acquire(self, holder: str, *, ttl_seconds: int = 7200) -> bool:
        """Return True if acquired; False if another live holder exists."""

    def release(self, holder: str) -> None:
        """Release if ``holder`` owns the lock (no-op otherwise)."""

    def current_holder(self) -> str | None: ...
