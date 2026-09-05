from __future__ import annotations

from pathlib import Path

from media_search.adapters.memory_store import InMemoryMetadataRepository, InMemoryVectorSearch
from media_search.adapters.sqlite_store import (
    SqliteMetadataRepository,
    SqliteVecSearch,
    open_db,
)
from media_search.adapters.local_media_storage import LocalMediaStorage
from media_search.adapters.media_probe import LocalMediaProbe
from media_search.application.import_directory import ImportDirectory
from media_search.application.search_media import SearchMediaAssets
from media_search.ports.embedding import FakeEmbedder
from media_search.ports.search import SearchQuery
from PIL import Image


def _write_png(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 32), color).save(path)


def test_import_skips_unsupported_and_imports_png(tmp_path: Path):
    incoming = tmp_path / "incoming"
    _write_png(incoming / "ok.png", (255, 0, 0))
    (incoming / "nope.webp").write_bytes(b"not-a-real-webp")

    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    summary = ImportDirectory(
        embedder=embedder, vectors=vectors, metadata=meta, media_probe=LocalMediaProbe()
    ).execute_storage(LocalMediaStorage(incoming))

    assert summary.imported == ["ok.png"]
    assert any(s.reason == "unsupported format" for s in summary.skipped)
    assert meta.get("ok.png") is not None


def test_reimport_is_upsert(tmp_path: Path):
    incoming = tmp_path / "incoming"
    _write_png(incoming / "a.png", (0, 255, 0))
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    importer = ImportDirectory(embedder=embedder, vectors=vectors, metadata=meta, media_probe=LocalMediaProbe())
    first = importer.execute_storage(LocalMediaStorage(incoming))
    second = importer.execute_storage(LocalMediaStorage(incoming))
    assert first.imported == ["a.png"]
    assert second.updated == ["a.png"]
    assert second.imported == []
    assert len(meta.list_all()) == 1


def test_sidecar_tags(tmp_path: Path):
    incoming = tmp_path / "incoming"
    png = incoming / "tagged.png"
    _write_png(png, (0, 0, 255))
    (incoming / "tagged.png.meta.json").write_text(
        '{"tags":["ad","cosmetics"],"description":"demo"}', encoding="utf-8"
    )
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    ImportDirectory(embedder=embedder, vectors=vectors, metadata=meta, media_probe=LocalMediaProbe()).execute_storage(LocalMediaStorage(incoming))
    asset = meta.get("tagged.png")
    assert asset is not None
    assert asset.tags == ["ad", "cosmetics"]
    assert asset.description == "demo"


def test_sqlite_vec_import_and_search(tmp_path: Path):
    incoming = tmp_path / "incoming"
    _write_png(incoming / "hit.png", (10, 20, 30))
    db = open_db(tmp_path / "media.db")
    embedder = FakeEmbedder(dimension=32)
    meta = SqliteMetadataRepository(db)
    vectors = SqliteVecSearch(db, dimension=32)
    ImportDirectory(embedder=embedder, vectors=vectors, metadata=meta, media_probe=LocalMediaProbe()).execute_storage(LocalMediaStorage(incoming))

    # Rank by planting query vector equal to stored image vector
    asset = meta.get("hit.png")
    assert asset is not None
    stored = embedder.embed_image((incoming / "hit.png").read_bytes())
    # Monkey: search via use case with text won't match Fake img space; use direct
    # vector search then ensure metadata path works through SearchMediaAssets by
    # upserting a frame with text vector for the query string.
    q = "find me"
    vectors.delete_asset_frames("hit.png")
    vectors.upsert_frame(
        asset_id="hit.png",
        frame_key="hit.png::0",
        position=0.0,
        vector=embedder.embed_text(q).tolist(),
    )
    hits = SearchMediaAssets(
        embedder=embedder, vectors=vectors, metadata=meta
    ).execute(SearchQuery(q=q, top_k=5))
    assert hits[0].asset.asset_id == "hit.png"
