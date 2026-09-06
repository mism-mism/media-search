from __future__ import annotations

"""Run a single import worker pass (Cloud Run Job / local CLI)."""

import os
import sys
from pathlib import Path


def run_worker(job_id: str | None = None) -> int:
    job_id = job_id or os.environ.get("IMPORT_JOB_ID", "").strip() or None
    # Build the same composition root as the web service, then run import once.
    from media_search.main import build_runtime

    rt = build_runtime()
    warm = getattr(rt.search, "warm", None)
    if callable(warm):
        warm()
    holder = f"worker:{job_id or 'adhoc'}"
    store = rt.job_store
    lock = rt.import_lock
    if store is None or lock is None:
        print("import job store/lock not configured", file=sys.stderr)
        return 2

    from media_search.adapters.import_job_store import job_from_dict  # noqa: F401
    from media_search.ports.import_job import ImportJobSkipped, ImportJobStatus

    if job_id:
        job = store.get(job_id)
        if job is None:
            print(f"job not found: {job_id}", file=sys.stderr)
            return 1
    else:
        job = store.create(holder)

    if not lock.try_acquire(holder):
        job.status = ImportJobStatus.FAILED
        job.error = f"lock busy: {lock.current_holder()}"
        store.save(job)
        return 1

    job.status = ImportJobStatus.RUNNING
    job.holder = holder
    store.save(job)
    try:
        keys = (
            list(job.only_keys)
            if job.only_keys
            else rt.media_storage.list_media_keys()
        )
        job.total = len(keys)
        store.save(job)

        def on_progress(processed: int, total: int) -> None:
            cur = store.get(job.job_id)
            if cur is None:
                return
            cur.processed = processed
            cur.total = total
            store.save(cur)

        summary = rt.importer.execute_storage(
            rt.media_storage,
            only_keys=list(job.only_keys) if job.only_keys else None,
            on_progress=on_progress,
        )
        job = store.get(job.job_id) or job
        job.status = ImportJobStatus.SUCCEEDED
        job.imported = list(summary.imported)
        job.updated = list(summary.updated)
        job.skipped = [
            ImportJobSkipped(path=s.path, reason=s.reason) for s in summary.skipped
        ]
        job.processed = job.total or (
            len(job.imported) + len(job.updated) + len(job.skipped)
        )
        store.save(job)
        if rt.persist_db is not None:
            rt.persist_db()
        return 0
    except Exception as exc:  # noqa: BLE001
        job = store.get(job.job_id) or job
        job.status = ImportJobStatus.FAILED
        job.error = str(exc)
        store.save(job)
        return 1
    finally:
        lock.release(holder)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    job_id = None
    if argv:
        job_id = argv[0]
    return run_worker(job_id)


if __name__ == "__main__":
    raise SystemExit(main())
