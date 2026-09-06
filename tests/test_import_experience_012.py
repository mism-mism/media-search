from __future__ import annotations

import time
from pathlib import Path

from PIL import Image

from media_search.adapters.local_media_storage import LocalMediaStorage
from media_search.adapters.media_probe import LocalMediaProbe
from media_search.adapters.memory_store import InMemoryMetadataRepository, InMemoryVectorSearch
from media_search.application.import_directory import ImportDirectory
from media_search.domain.media_asset import MediaAsset, MediaType
from media_search.ports.embedding import FakeEmbedder


def _write_png(path: Path, color: tuple[int, int, int], size: int = 32) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (size, size), color).save(path)


def _importer(meta, vectors, workers: int = 2) -> ImportDirectory:
    return ImportDirectory(
        embedder=FakeEmbedder(),
        vectors=vectors,
        metadata=meta,
        media_probe=LocalMediaProbe(),
        embed_workers=workers,
    )


def test_metadata_without_vectors_is_embedded(tmp_path: Path):
    """Library upload pre-writes metadata; Import must still embed (012)."""
    incoming = tmp_path / "incoming"
    _write_png(incoming / "lib.png", (10, 20, 30))
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    data = (incoming / "lib.png").read_bytes()
    meta.upsert(
        MediaAsset(
            asset_id="lib.png",
            media_type=MediaType.IMAGE,
            mime_type="image/png",
            size_bytes=len(data),
            display_name="lib.png",
        )
    )
    assert not vectors.has_frames("lib.png")
    summary = _importer(meta, vectors).execute_storage(LocalMediaStorage(incoming))
    assert "lib.png" in summary.imported or "lib.png" in summary.updated
    assert vectors.has_frames("lib.png")
    assert not any(s.reason == "unchanged" for s in summary.skipped)


def test_unchanged_with_vectors_skips(tmp_path: Path):
    incoming = tmp_path / "incoming"
    _write_png(incoming / "a.png", (1, 2, 3))
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    imp = _importer(meta, vectors)
    first = imp.execute_storage(LocalMediaStorage(incoming))
    assert first.imported == ["a.png"]
    second = imp.execute_storage(LocalMediaStorage(incoming))
    assert any(s.path == "a.png" and s.reason == "unchanged" for s in second.skipped)


def test_only_keys_scopes_work(tmp_path: Path):
    incoming = tmp_path / "incoming"
    _write_png(incoming / "keep.png", (1, 1, 1))
    _write_png(incoming / "new.png", (2, 2, 2))
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    imp = _importer(meta, vectors)
    imp.execute_storage(LocalMediaStorage(incoming), only_keys=["keep.png"])
    assert vectors.has_frames("keep.png")
    assert not vectors.has_frames("new.png")
    imp.execute_storage(LocalMediaStorage(incoming), only_keys=["new.png"])
    assert vectors.has_frames("new.png")


def test_incremental_single_add_faster_than_full_rescan(tmp_path: Path):
    """Hermetic ≥3×: scoped single embed vs re-embedding N files."""
    incoming = tmp_path / "incoming"
    n = 24
    for i in range(n):
        _write_png(incoming / f"old-{i:02d}.png", (i % 200, 40, 80), size=48)
    storage = LocalMediaStorage(incoming)

    class SlowEmbed(FakeEmbedder):
        def embed_image(self, image_bytes: bytes):  # type: ignore[override]
            time.sleep(0.02)
            return super().embed_image(image_bytes)

    meta_base = InMemoryMetadataRepository()
    vectors_base = InMemoryVectorSearch()
    for i in range(n):
        key = f"old-{i:02d}.png"
        meta_base.upsert(
            MediaAsset(
                asset_id=key,
                media_type=MediaType.IMAGE,
                mime_type="image/png",
                size_bytes=(incoming / key).stat().st_size,
                display_name=key,
            )
        )
    baseline = ImportDirectory(
        embedder=SlowEmbed(),
        vectors=vectors_base,
        metadata=meta_base,
        media_probe=LocalMediaProbe(),
        embed_workers=4,
    )
    t0 = time.perf_counter()
    baseline.execute_storage(
        storage, only_keys=[f"old-{i:02d}.png" for i in range(n)]
    )
    baseline_s = time.perf_counter() - t0

    _write_png(incoming / "brand-new.png", (9, 9, 9), size=48)
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    seed = _importer(meta, vectors, workers=4)
    seed.execute_storage(storage, only_keys=[f"old-{i:02d}.png" for i in range(n)])
    meta.upsert(
        MediaAsset(
            asset_id="brand-new.png",
            media_type=MediaType.IMAGE,
            mime_type="image/png",
            size_bytes=(incoming / "brand-new.png").stat().st_size,
            display_name="brand-new.png",
        )
    )
    scoped = ImportDirectory(
        embedder=SlowEmbed(),
        vectors=vectors,
        metadata=meta,
        media_probe=LocalMediaProbe(),
        embed_workers=4,
    )
    t1 = time.perf_counter()
    summary = scoped.execute_storage(storage, only_keys=["brand-new.png"])
    scoped_s = time.perf_counter() - t1
    assert "brand-new.png" in summary.imported or "brand-new.png" in summary.updated
    assert vectors.has_frames("brand-new.png")
    assert scoped_s * 3 <= baseline_s, (
        f"scoped={scoped_s:.3f}s baseline={baseline_s:.3f}s"
    )
