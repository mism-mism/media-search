import time
from pathlib import Path

from PIL import Image

from media_search.adapters.caching_embedder import CachingEmbedder
from media_search.adapters.local_media_storage import LocalMediaStorage
from media_search.adapters.media_probe import LocalMediaProbe
from media_search.adapters.memory_store import InMemoryMetadataRepository, InMemoryVectorSearch
from media_search.adapters.sqlite_store import SqliteMetadataRepository, open_db
from media_search.application.import_directory import ImportDirectory
from media_search.application.search_media import SearchMediaAssets
from media_search.domain.media_asset import MediaAsset, MediaType
from media_search.ports.embedding import FakeEmbedder
from media_search.ports.search import SearchQuery


def test_caching_embedder_reuses_text_vector():
    inner = FakeEmbedder()
    cached = CachingEmbedder(inner, text_size=8)
    a = cached.embed_text("Hello World")
    b = cached.embed_text(" hello world ")
    assert (a == b).all()


def test_search_text_sql_path(tmp_path: Path):
    conn = open_db(tmp_path / "t.db")
    meta = SqliteMetadataRepository(conn)
    meta.upsert(
        MediaAsset(
            asset_id="a.png",
            media_type=MediaType.IMAGE,
            mime_type="image/png",
            size_bytes=1,
            display_name="Neon Bottle",
            tags=["sku-x"],
        )
    )
    hits = meta.search_text("neon")
    assert [h.asset_id for h in hits] == ["a.png"]
    assert meta.search_text("sku-x")[0].asset_id == "a.png"
    assert meta.search_text("missing") == []


def test_text_search_uses_search_text_not_full_scan():
    class SpyMeta(InMemoryMetadataRepository):
        def __init__(self) -> None:
            super().__init__()
            self.list_all_calls = 0
            self.search_text_calls = 0

        def list_all(self) -> list[MediaAsset]:
            self.list_all_calls += 1
            return super().list_all()

        def search_text(self, needle: str) -> list[MediaAsset]:
            self.search_text_calls += 1
            return super().search_text(needle)

    embedder = FakeEmbedder()
    meta = SpyMeta()
    vectors = InMemoryVectorSearch()
    meta.upsert(
        MediaAsset(
            asset_id="n.png",
            media_type=MediaType.IMAGE,
            mime_type="image/png",
            size_bytes=1,
            display_name="Widget Pro",
        )
    )
    use_case = SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta)
    hits = use_case.execute(SearchQuery(q="Widget", top_k=5))
    assert hits[0].asset.asset_id == "n.png"
    assert meta.search_text_calls == 1
    assert meta.list_all_calls == 0


def test_parallel_import_indexes_multiple_images(tmp_path: Path):
    incoming = tmp_path / "in"
    incoming.mkdir()
    for i in range(6):
        Image.new("RGB", (8, 8), (i, 2, 3)).save(incoming / f"i{i}.png")

    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()

    def slow_embed(image_bytes: bytes):
        time.sleep(0.05)
        return FakeEmbedder.embed_image(embedder, image_bytes)

    embedder.embed_image = slow_embed  # type: ignore[method-assign]

    sequential = ImportDirectory(
        embedder=embedder,
        vectors=InMemoryVectorSearch(),
        metadata=InMemoryMetadataRepository(),
        media_probe=LocalMediaProbe(),
        work_dir=tmp_path / "w1",
        embed_workers=1,
    )
    t0 = time.perf_counter()
    sequential.execute_storage(LocalMediaStorage(incoming))
    seq_s = time.perf_counter() - t0

    parallel = ImportDirectory(
        embedder=embedder,
        vectors=vectors,
        metadata=meta,
        media_probe=LocalMediaProbe(),
        work_dir=tmp_path / "w2",
        embed_workers=4,
    )
    t1 = time.perf_counter()
    summary = parallel.execute_storage(LocalMediaStorage(incoming))
    par_s = time.perf_counter() - t1

    assert len(summary.imported) == 6
    assert len(vectors._frames) == 6
    # Parallel should be clearly faster than sequential under artificial sleep.
    assert par_s < seq_s * 0.75
