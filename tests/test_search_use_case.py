from media_search.application.search_media import EmptyQueryError, SearchMediaAssets
from media_search.domain.media_asset import MediaAsset, MediaType
from media_search.adapters.memory_store import InMemoryMetadataRepository, InMemoryVectorSearch
from media_search.ports.embedding import FakeEmbedder
from media_search.ports.search import SearchQuery


def _seed_asset(repo, vectors, embedder, asset_id: str, tags: list[str], text_seed: str):
    asset = MediaAsset(
        asset_id=asset_id,
        media_type=MediaType.IMAGE,
        mime_type="image/jpeg",
        size_bytes=100,
        tags=tags,
    )
    repo.upsert(asset)
    # Use text-like image bytes so FakeEmbedder is deterministic but distinct
    image_bytes = text_seed.encode()
    vec = embedder.embed_image(image_bytes)
    vectors.upsert_frame(
        asset_id=asset_id,
        frame_key=f"{asset_id}::0",
        position=0.0,
        vector=vec.tolist(),
    )


def test_empty_query_raises():
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    use_case = SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta)
    try:
        use_case.execute(SearchQuery(q="  "))
        assert False, "expected EmptyQueryError"
    except EmptyQueryError:
        pass


def test_tags_filter_is_and():
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    _seed_asset(meta, vectors, embedder, "a.jpg", ["ad", "cosmetics"], "woman product")
    _seed_asset(meta, vectors, embedder, "b.jpg", ["ad"], "other")

    use_case = SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta)
    # Query text identical to a.jpg seed so Fake ranks a.jpg high; filter AND
    hits = use_case.execute(
        SearchQuery(q="woman product", tags=("ad", "cosmetics"), top_k=5)
    )
    ids = [h.asset.asset_id for h in hits]
    assert "a.jpg" in ids
    assert "b.jpg" not in ids


def test_collapse_keeps_max_frame_score():
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    asset = MediaAsset(
        asset_id="clip.mp4",
        media_type=MediaType.VIDEO,
        mime_type="video/mp4",
        size_bytes=10,
        duration_seconds=20.0,
        tags=[],
    )
    meta.upsert(asset)
    # Two frames; make second match query text embedding more closely by using
    # same seed string as query for frame image bytes path — Fake separates
    # img vs txt namespaces, so we upsert query vector itself as one frame.
    q = "outdoor smile"
    qvec = embedder.embed_text(q)
    weak = embedder.embed_image(b"weak-frame")
    vectors.upsert_frame(
        asset_id="clip.mp4", frame_key="clip.mp4::0", position=0.0, vector=weak.tolist()
    )
    vectors.upsert_frame(
        asset_id="clip.mp4", frame_key="clip.mp4::1", position=0.5, vector=qvec.tolist()
    )

    use_case = SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta)
    hits = use_case.execute(SearchQuery(q=q, top_k=5))
    assert len(hits) == 1
    assert hits[0].asset.asset_id == "clip.mp4"
    assert hits[0].best_frame is not None
    assert hits[0].best_frame.frame_key == "clip.mp4::1"
    assert hits[0].score == hits[0].best_frame.score
