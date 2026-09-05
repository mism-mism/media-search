from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from media_search.adapters.filesystem_import_lock import FilesystemImportLock
from media_search.adapters.import_job_store import FilesystemJobStore
from media_search.adapters.import_jobs import LocalThreadImportJobs
from media_search.adapters.local_frame_store import LocalFrameStore
from media_search.adapters.local_media_storage import LocalMediaStorage
from media_search.adapters.media_probe import LocalMediaProbe
from media_search.adapters.memory_store import InMemoryMetadataRepository, InMemoryVectorSearch
from media_search.api.app import create_app
from media_search.application.import_directory import ImportDirectory
from media_search.application.search_media import SearchMediaAssets
from media_search.ports.embedding import FakeEmbedder
from media_search.ports.import_job import ImportJobStatus
from media_search.ports.import_lock import ImportLockBusy


def test_filesystem_lock_conflict(tmp_path: Path):
    lock = FilesystemImportLock(tmp_path / "lock.json")
    assert lock.try_acquire("a")
    assert not lock.try_acquire("b")
    assert lock.current_holder() == "a"
    lock.release("a")
    assert lock.try_acquire("b")


def test_async_import_job_and_stats(tmp_path: Path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    Image.new("RGB", (16, 16), (1, 2, 3)).save(incoming / "m.png")
    work = tmp_path / "work"
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    storage = LocalMediaStorage(incoming)
    frame_store = LocalFrameStore(work / "frames")
    importer = ImportDirectory(
        embedder=embedder,
        vectors=vectors,
        metadata=meta,
        media_probe=LocalMediaProbe(),
        work_dir=work,
        frame_store=frame_store,
    )
    jobs = LocalThreadImportJobs(
        store=FilesystemJobStore(work / "jobs"),
        lock=FilesystemImportLock(work / "lock.json"),
        importer=importer,
        storage=storage,
        run_inline=True,
    )
    app = create_app(
        search=SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta),
        importer=importer,
        import_jobs=jobs,
        metadata=meta,
        media_storage=storage,
        frame_store=frame_store,
    )
    client = TestClient(app)
    res = client.post("/api/import")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "succeeded"
    assert body["imported"] == ["m.png"]
    st = client.get("/api/stats").json()
    assert st["assets"] == 1
    assert st["images"] == 1
    assert st["latest_job"]["job_id"] == body["job_id"]


def test_overlapping_import_returns_409(tmp_path: Path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    Image.new("RGB", (8, 8), (9, 9, 9)).save(incoming / "x.png")
    work = tmp_path / "work"
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    storage = LocalMediaStorage(incoming)
    importer = ImportDirectory(
        embedder=embedder,
        vectors=vectors,
        metadata=meta,
        media_probe=LocalMediaProbe(),
        work_dir=work,
    )
    lock = FilesystemImportLock(work / "lock.json")
    assert lock.try_acquire("other")
    jobs = LocalThreadImportJobs(
        store=FilesystemJobStore(work / "jobs"),
        lock=lock,
        importer=importer,
        storage=storage,
        run_inline=True,
    )
    app = create_app(
        search=SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta),
        import_jobs=jobs,
        metadata=meta,
        media_storage=storage,
    )
    res = TestClient(app).post("/api/import")
    assert res.status_code == 409


def test_frame_store_survives_local_wipe(tmp_path: Path):
    import subprocess

    incoming = tmp_path / "incoming"
    incoming.mkdir()
    video = incoming / "clip.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=64x64:d=2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-t",
            "2",
            str(video),
        ],
        check=True,
        capture_output=True,
    )
    durable = tmp_path / "durable-frames"
    work = tmp_path / "work"
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    frame_store = LocalFrameStore(durable)
    importer = ImportDirectory(
        embedder=embedder,
        vectors=vectors,
        metadata=meta,
        media_probe=LocalMediaProbe(),
        work_dir=work,
        frame_store=frame_store,
    )
    app = create_app(
        search=SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta),
        importer=importer,
        metadata=meta,
        media_root=incoming,
        frame_store=frame_store,
    )
    client = TestClient(app)
    assert client.post("/api/import", params={"path": str(incoming)}).status_code == 200
    # Simulate ephemeral work wipe (Cloud Run scale-to-zero).
    import shutil

    shutil.rmtree(work, ignore_errors=True)
    res = client.get("/api/search", params={"q": "clip"})
    thumb = client.get(res.json()["results"][0]["thumbnail_url"])
    assert thumb.status_code == 200
    assert thumb.content[:2] == b"\xff\xd8"
