from __future__ import annotations

import os
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import uvicorn

from media_search.adapters.filesystem_import_lock import FilesystemImportLock
from media_search.adapters.import_job_store import FilesystemJobStore, GcsJobStore
from media_search.adapters.import_jobs import CloudRunImportJobs, LocalThreadImportJobs
from media_search.adapters.local_frame_store import LocalFrameStore
from media_search.adapters.local_media_storage import LocalMediaStorage
from media_search.adapters.media_probe import LocalMediaProbe
from media_search.adapters.sqlite_store import (
    SqliteFolderRepository,
    SqliteMetadataRepository,
    SqliteVecSearch,
    open_db,
)
from media_search.api.app import create_app
from media_search.application.import_directory import ImportDirectory
from media_search.application.library import LibraryService
from media_search.application.search_media import SearchMediaAssets
from media_search.ports.embedding import FakeEmbedder
from media_search.ports.frame_store import FrameStorePort
from media_search.ports.import_job import ImportJobPort
from media_search.ports.import_lock import ImportLockPort
from media_search.ports.media_storage import MediaStoragePort


def _build_embedder():
    name = os.environ.get("EMBEDDER", "local").lower()
    if name == "fake":
        return name, FakeEmbedder(dimension=32)
    if name == "local":
        from media_search.adapters.openclip_embedder import LazyOpenClipEmbedder

        return name, LazyOpenClipEmbedder()
    raise SystemExit(f"unsupported EMBEDDER={name!r}")


def _build_media_storage(data_dir: Path) -> MediaStoragePort:
    backend = os.environ.get("MEDIA_BACKEND", "local").lower()
    if backend == "local":
        media_root = Path(
            os.environ.get("MEDIA_SEARCH_MEDIA_ROOT", data_dir / "incoming")
        ).resolve()
        media_root.mkdir(parents=True, exist_ok=True)
        return LocalMediaStorage(media_root)
    if backend == "gcs":
        from media_search.adapters.gcs_media_storage import GcsMediaStorage

        bucket = os.environ.get("GCS_BUCKET", "").strip()
        if not bucket:
            raise SystemExit("GCS_BUCKET is required when MEDIA_BACKEND=gcs")
        prefix = os.environ.get("GCS_PREFIX", "incoming").strip()
        return GcsMediaStorage(bucket_name=bucket, prefix=prefix)
    raise SystemExit(f"unsupported MEDIA_BACKEND={backend!r}")


def _build_frame_store(work_dir: Path, data_dir: Path) -> FrameStorePort:
    backend = os.environ.get("FRAME_BACKEND", "").strip().lower()
    if not backend:
        backend = "gcs" if os.environ.get("MEDIA_BACKEND", "").lower() == "gcs" else "local"
    if backend == "local":
        root = work_dir / "frames"
        root.mkdir(parents=True, exist_ok=True)
        return LocalFrameStore(root)
    if backend == "gcs":
        from media_search.adapters.gcs_frame_store import GcsFrameStore

        bucket = os.environ.get("GCS_BUCKET", "").strip()
        if not bucket:
            raise SystemExit("GCS_BUCKET required for FRAME_BACKEND=gcs")
        prefix = os.environ.get("GCS_FRAMES_PREFIX", "frames").strip()
        return GcsFrameStore(bucket_name=bucket, prefix=prefix)
    raise SystemExit(f"unsupported FRAME_BACKEND={backend!r}")


def _build_lock(work_dir: Path) -> ImportLockPort:
    backend = os.environ.get("IMPORT_LOCK_BACKEND", "").strip().lower()
    if not backend:
        backend = "gcs" if os.environ.get("MEDIA_BACKEND", "").lower() == "gcs" else "fs"
    if backend == "fs":
        return FilesystemImportLock(work_dir / "import.lock.json")
    if backend == "gcs":
        from media_search.adapters.gcs_frame_store import GcsImportLock

        bucket = os.environ.get("GCS_BUCKET", "").strip()
        if not bucket:
            raise SystemExit("GCS_BUCKET required for IMPORT_LOCK_BACKEND=gcs")
        obj = os.environ.get("IMPORT_LOCK_OBJECT", "state/import.lock.json").strip()
        return GcsImportLock(bucket_name=bucket, object_name=obj)
    raise SystemExit(f"unsupported IMPORT_LOCK_BACKEND={backend!r}")


@dataclass
class Runtime:
    embedder_mode: str
    embedder: object
    media_storage: MediaStoragePort
    frame_store: FrameStorePort
    importer: ImportDirectory
    search: SearchMediaAssets
    metadata: SqliteMetadataRepository
    folders: SqliteFolderRepository
    library: LibraryService
    import_lock: ImportLockPort
    job_store: FilesystemJobStore | GcsJobStore
    import_jobs: ImportJobPort
    persist_db: Callable[[], None] | None
    work_dir: Path
    db_path: Path


def build_runtime() -> Runtime:
    data_dir = Path(os.environ.get("MEDIA_SEARCH_DATA", "data")).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    embedder_mode, embedder = _build_embedder()
    default_db = data_dir / (
        "media-fake.db" if embedder_mode == "fake" else "media-local-cos.db"
    )
    db_path = Path(os.environ.get("MEDIA_SEARCH_DB", default_db)).resolve()
    work_dir = Path(
        os.environ.get("MEDIA_SEARCH_WORK", data_dir / "work")
    ).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    db_gcs_uri = os.environ.get("MEDIA_SEARCH_DB_GCS", "").strip()
    if db_gcs_uri:
        from media_search.adapters.gcs_db_sync import download_db_if_remote

        download_db_if_remote(gcs_uri=db_gcs_uri, local_path=db_path)

    conn = open_db(db_path)
    db_lock = threading.Lock()
    meta = SqliteMetadataRepository(conn, lock=db_lock)
    folders = SqliteFolderRepository(conn, lock=db_lock)
    vectors = SqliteVecSearch(conn, dimension=embedder.dimension, lock=db_lock)
    search = SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta)
    media_storage = _build_media_storage(data_dir)
    frame_store = _build_frame_store(work_dir, data_dir)
    import_lock = _build_lock(work_dir)
    importer = ImportDirectory(
        embedder=embedder,
        vectors=vectors,
        metadata=meta,
        media_probe=LocalMediaProbe(),
        work_dir=work_dir,
        frame_store=frame_store,
    )

    def persist_db() -> None:
        if not db_gcs_uri:
            return
        from media_search.adapters.gcs_db_sync import upload_db

        conn.commit()
        upload_db(gcs_uri=db_gcs_uri, local_path=db_path)

    persist = persist_db if db_gcs_uri else None

    is_worker = os.environ.get("IMPORT_MODE", "").strip().lower() == "worker"
    want_cloudrun_enqueue = (
        not is_worker
        and (
            os.environ.get("IMPORT_JOB_BACKEND", "").strip().lower() == "cloudrun"
            or bool(os.environ.get("CLOUD_RUN_IMPORT_JOB", "").strip())
        )
    )

    if os.environ.get("MEDIA_BACKEND", "").lower() == "gcs":
        bucket = os.environ.get("GCS_BUCKET", "").strip()
        job_store: FilesystemJobStore | GcsJobStore = GcsJobStore(
            bucket_name=bucket,
            prefix=os.environ.get("IMPORT_JOB_PREFIX", "state/import-jobs"),
        )
    else:
        job_store = FilesystemJobStore(work_dir / "import-jobs")

    if want_cloudrun_enqueue:
        project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get(
            "GCP_PROJECT", ""
        )
        region = os.environ.get(
            "CLOUD_RUN_REGION",
            os.environ.get("VERTEX_LOCATION", "asia-northeast1"),
        )
        job_name = os.environ.get("CLOUD_RUN_IMPORT_JOB", "").strip()
        if not job_name or not project:
            raise SystemExit(
                "CLOUD_RUN_IMPORT_JOB and GOOGLE_CLOUD_PROJECT required for cloudrun jobs"
            )
        import_jobs: ImportJobPort = CloudRunImportJobs(
            store=job_store,  # type: ignore[arg-type]
            lock=import_lock,
            project=project,
            region=region,
            job_name=job_name,
        )
    else:
        run_inline = os.environ.get("IMPORT_SYNC", "").strip() in {"1", "true", "yes"}
        import_jobs = LocalThreadImportJobs(
            store=job_store,
            lock=import_lock,
            importer=importer,
            storage=media_storage,
            on_after_import=persist,
            run_inline=run_inline,
        )

    library = LibraryService(
        folders=folders,
        metadata=meta,
        storage=media_storage,
        vectors=vectors,
        frame_store=frame_store,
        import_jobs=import_jobs,
        on_after_mutate=persist,
    )

    return Runtime(
        embedder_mode=embedder_mode,
        embedder=embedder,
        media_storage=media_storage,
        frame_store=frame_store,
        importer=importer,
        search=search,
        metadata=meta,
        folders=folders,
        library=library,
        import_lock=import_lock,
        job_store=job_store,
        import_jobs=import_jobs,
        persist_db=persist,
        work_dir=work_dir,
        db_path=db_path,
    )


def build_app():
    rt = build_runtime()
    return create_app(
        search=rt.search,
        importer=rt.importer,
        import_jobs=rt.import_jobs,
        library=rt.library,
        metadata=rt.metadata,
        media_storage=rt.media_storage,
        frame_store=rt.frame_store,
        on_after_import=rt.persist_db,
        embedder_mode=rt.embedder_mode,
        embedder_id=getattr(rt.embedder, "model_id", "unknown"),
    )


def main() -> None:
    mode = os.environ.get("IMPORT_MODE", "").strip().lower()
    if mode == "worker":
        from media_search.worker_import import run_worker

        raise SystemExit(run_worker())
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("media_search.main:app", host=host, port=port, reload=False)


app = build_app()


if __name__ == "__main__":
    main()
