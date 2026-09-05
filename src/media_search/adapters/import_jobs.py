from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from media_search.adapters.import_job_store import FilesystemJobStore, GcsJobStore
from media_search.application.import_directory import ImportDirectory, ImportSummary
from media_search.ports.import_job import ImportJobPort, ImportJobRecord, ImportJobSkipped, ImportJobStatus
from media_search.ports.import_lock import ImportLockBusy, ImportLockPort
from media_search.ports.media_storage import MediaStoragePort


class LocalThreadImportJobs(ImportJobPort):
    """Acquire lock, run ImportDirectory on a daemon thread, persist job records."""

    def __init__(
        self,
        *,
        store: FilesystemJobStore | GcsJobStore,
        lock: ImportLockPort,
        importer: ImportDirectory,
        storage: MediaStoragePort,
        on_after_import: Callable[[], None] | None = None,
        run_inline: bool = False,
    ) -> None:
        self._store = store
        self._lock = lock
        self._importer = importer
        self._storage = storage
        self._on_after_import = on_after_import
        self._run_inline = run_inline
        self._threads: dict[str, threading.Thread] = {}

    def enqueue(self) -> ImportJobRecord:
        holder = f"local-{threading.get_ident()}"
        current = self._lock.current_holder()
        if current is not None:
            raise ImportLockBusy(current)
        if not self._lock.try_acquire(holder):
            raise ImportLockBusy(self._lock.current_holder() or "unknown")
        job = self._store.create(holder)
        if self._run_inline:
            self._run(job.job_id, holder)
            return self._store.get(job.job_id) or job
        t = threading.Thread(
            target=self._run, args=(job.job_id, holder), daemon=True, name=f"import-{job.job_id}"
        )
        self._threads[job.job_id] = t
        t.start()
        return job

    def get(self, job_id: str) -> ImportJobRecord | None:
        return self._store.get(job_id)

    def latest(self) -> ImportJobRecord | None:
        return self._store.latest()

    def _run(self, job_id: str, holder: str) -> None:
        job = self._store.get(job_id)
        if job is None:
            self._lock.release(holder)
            return
        job.status = ImportJobStatus.RUNNING
        self._store.save(job)
        try:
            keys = self._storage.list_media_keys()
            job.total = len(keys)
            self._store.save(job)

            def on_progress(processed: int, total: int) -> None:
                cur = self._store.get(job_id)
                if cur is None:
                    return
                cur.processed = processed
                cur.total = total
                self._store.save(cur)

            summary = self._importer.execute_storage(
                self._storage, on_progress=on_progress
            )
            job = self._store.get(job_id) or job
            job.status = ImportJobStatus.SUCCEEDED
            job.imported = list(summary.imported)
            job.updated = list(summary.updated)
            job.skipped = [
                ImportJobSkipped(path=s.path, reason=s.reason) for s in summary.skipped
            ]
            job.processed = job.total or (
                len(job.imported) + len(job.updated) + len(job.skipped)
            )
            self._store.save(job)
            if self._on_after_import is not None:
                self._on_after_import()
        except Exception as exc:  # noqa: BLE001
            job = self._store.get(job_id) or job
            job.status = ImportJobStatus.FAILED
            job.error = str(exc)
            self._store.save(job)
        finally:
            self._lock.release(holder)


class CloudRunImportJobs(ImportJobPort):
    """Enqueue by creating a job record and starting a Cloud Run Job execution."""

    def __init__(
        self,
        *,
        store: GcsJobStore,
        lock: ImportLockPort,
        project: str,
        region: str,
        job_name: str,
    ) -> None:
        self._store = store
        self._lock = lock
        self._project = project
        self._region = region
        self._job_name = job_name

    def enqueue(self) -> ImportJobRecord:
        holder = f"cloudrun-job:{self._job_name}"
        current = self._lock.current_holder()
        if current is not None:
            raise ImportLockBusy(current)
        # Soft-check only; worker acquires the real lock.
        job = self._store.create(holder)
        try:
            self._start_execution(job.job_id)
        except Exception as exc:  # noqa: BLE001
            job.status = ImportJobStatus.FAILED
            job.error = f"failed to start Cloud Run Job: {exc}"
            self._store.save(job)
            raise
        return job

    def get(self, job_id: str) -> ImportJobRecord | None:
        return self._store.get(job_id)

    def latest(self) -> ImportJobRecord | None:
        return self._store.latest()

    def _start_execution(self, job_id: str) -> None:
        from google.cloud import run_v2

        client = run_v2.JobsClient()
        name = (
            f"projects/{self._project}/locations/{self._region}/jobs/{self._job_name}"
        )
        request = run_v2.RunJobRequest(
            name=name,
            overrides=run_v2.RunJobRequest.Overrides(
                container_overrides=[
                    run_v2.RunJobRequest.Overrides.ContainerOverride(
                        env=[
                            run_v2.EnvVar(name="IMPORT_JOB_ID", value=job_id),
                            run_v2.EnvVar(name="IMPORT_MODE", value="worker"),
                        ]
                    )
                ]
            ),
        )
        client.run_job(request=request)
