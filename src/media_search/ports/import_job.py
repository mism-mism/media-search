from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class ImportJobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class ImportJobSkipped:
    path: str
    reason: str


@dataclass
class ImportJobRecord:
    job_id: str
    status: ImportJobStatus
    holder: str
    created_at: str
    updated_at: str
    processed: int = 0
    total: int | None = None
    imported: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[ImportJobSkipped] = field(default_factory=list)
    error: str | None = None


class ImportJobPort(Protocol):
    """Enqueue and observe async import work."""

    def enqueue(self) -> ImportJobRecord:
        """Start a job or raise ImportLockBusy if a writer is active."""

    def get(self, job_id: str) -> ImportJobRecord | None: ...

    def latest(self) -> ImportJobRecord | None: ...
