from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from media_search.adapters.local_media_storage import LocalMediaStorage
from media_search.adapters.media_probe import LocalMediaProbe
from media_search.adapters.sqlite_store import (
    SqliteMetadataRepository,
    SqliteVecSearch,
    open_db,
)
from media_search.api.app import create_app
from media_search.application.import_directory import ImportDirectory
from media_search.application.search_media import SearchMediaAssets
from media_search.ports.embedding import FakeEmbedder


def _build_embedder():
    # Product-like default is local; tests/docker smoke can force fake.
    name = os.environ.get("EMBEDDER", "local").lower()
    if name == "fake":
        return name, FakeEmbedder(dimension=32)
    if name == "local":
        from media_search.adapters.openclip_embedder import LazyOpenClipEmbedder

        # Lazy: Cloud Run must listen on PORT before HF/OpenCLIP download.
        return name, LazyOpenClipEmbedder()
    raise SystemExit(f"unsupported EMBEDDER={name!r}")


def _build_media_storage(data_dir: Path):
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


def build_app():
    import threading

    data_dir = Path(os.environ.get("MEDIA_SEARCH_DATA", "data")).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    # Separate DB per embedder dim / model to avoid vec0 schema clashes.
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
    vectors = SqliteVecSearch(conn, dimension=embedder.dimension, lock=db_lock)
    search = SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta)
    frame_root = work_dir / "frames"
    frame_root.mkdir(parents=True, exist_ok=True)
    media_storage = _build_media_storage(data_dir)
    importer = ImportDirectory(
        embedder=embedder,
        vectors=vectors,
        metadata=meta,
        media_probe=LocalMediaProbe(),
        work_dir=work_dir,
    )

    def _persist_db() -> None:
        if not db_gcs_uri:
            return
        from media_search.adapters.gcs_db_sync import upload_db

        # Ensure sqlite flush before upload.
        conn.commit()
        upload_db(gcs_uri=db_gcs_uri, local_path=db_path)

    return create_app(
        search=search,
        importer=importer,
        metadata=meta,
        media_storage=media_storage,
        frame_root=frame_root,
        on_after_import=_persist_db if db_gcs_uri else None,
        embedder_mode=embedder_mode,
        embedder_id=getattr(embedder, "model_id", "unknown"),
    )


app = build_app()


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("media_search.main:app", host=host, port=port, reload=False)
