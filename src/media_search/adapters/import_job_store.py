from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from media_search.ports.import_job import (
    ImportJobRecord,
    ImportJobSkipped,
    ImportJobStatus,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def job_to_dict(job: ImportJobRecord) -> dict:
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "holder": job.holder,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "processed": job.processed,
        "total": job.total,
        "imported": list(job.imported),
        "updated": list(job.updated),
        "skipped": [{"path": s.path, "reason": s.reason} for s in job.skipped],
        "only_keys": list(job.only_keys),
        "error": job.error,
    }


def job_from_dict(data: dict) -> ImportJobRecord:
    return ImportJobRecord(
        job_id=str(data["job_id"]),
        status=ImportJobStatus(str(data["status"])),
        holder=str(data.get("holder", "")),
        created_at=str(data.get("created_at", "")),
        updated_at=str(data.get("updated_at", "")),
        processed=int(data.get("processed") or 0),
        total=data.get("total"),
        imported=list(data.get("imported") or []),
        updated=list(data.get("updated") or []),
        skipped=[
            ImportJobSkipped(path=s["path"], reason=s["reason"])
            for s in (data.get("skipped") or [])
        ],
        only_keys=list(data.get("only_keys") or []),
        error=data.get("error"),
    )


class FilesystemJobStore:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)
        self._latest = self._root / "latest.txt"

    def _path(self, job_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in job_id)
        return self._root / f"{safe}.json"

    def create(
        self, holder: str, *, only_keys: list[str] | None = None
    ) -> ImportJobRecord:
        now = _now()
        job = ImportJobRecord(
            job_id=str(uuid.uuid4()),
            status=ImportJobStatus.QUEUED,
            holder=holder,
            created_at=now,
            updated_at=now,
            only_keys=list(only_keys or []),
        )
        self.save(job)
        return job

    def save(self, job: ImportJobRecord) -> None:
        job.updated_at = _now()
        path = self._path(job.job_id)
        path.write_text(json.dumps(job_to_dict(job), indent=2), encoding="utf-8")
        self._latest.write_text(job.job_id, encoding="utf-8")

    def get(self, job_id: str) -> ImportJobRecord | None:
        path = self._path(job_id)
        if not path.is_file():
            return None
        return job_from_dict(json.loads(path.read_text(encoding="utf-8")))

    def latest(self) -> ImportJobRecord | None:
        if not self._latest.is_file():
            return None
        return self.get(self._latest.read_text(encoding="utf-8").strip())


class GcsJobStore:
    def __init__(self, *, bucket_name: str, prefix: str = "state/import-jobs") -> None:
        from google.cloud import storage as gcs

        self._client = gcs.Client()
        self._bucket = self._client.bucket(bucket_name)
        self._prefix = prefix.strip("/")

    def _blob(self, job_id: str):
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in job_id)
        return self._bucket.blob(f"{self._prefix}/{safe}.json")

    def _latest_blob(self):
        return self._bucket.blob(f"{self._prefix}/latest.txt")

    def create(
        self, holder: str, *, only_keys: list[str] | None = None
    ) -> ImportJobRecord:
        now = _now()
        job = ImportJobRecord(
            job_id=str(uuid.uuid4()),
            status=ImportJobStatus.QUEUED,
            holder=holder,
            created_at=now,
            updated_at=now,
            only_keys=list(only_keys or []),
        )
        self.save(job)
        return job

    def save(self, job: ImportJobRecord) -> None:
        job.updated_at = _now()
        payload = json.dumps(job_to_dict(job), indent=2)
        self._blob(job.job_id).upload_from_string(payload, content_type="application/json")
        self._latest_blob().upload_from_string(job.job_id, content_type="text/plain")

    def get(self, job_id: str) -> ImportJobRecord | None:
        blob = self._blob(job_id)
        if not blob.exists():
            return None
        return job_from_dict(json.loads(blob.download_as_text()))

    def latest(self) -> ImportJobRecord | None:
        blob = self._latest_blob()
        if not blob.exists():
            return None
        return self.get(blob.download_as_text().strip())
