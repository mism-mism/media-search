from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from media_search.adapters.memory_store import InMemoryMetadataRepository, InMemoryVectorSearch
from media_search.api.app import create_app
from media_search.application.search_media import EmptyImageError, SearchMediaAssets
from media_search.domain.media_asset import MediaAsset, MediaType
from media_search.ports.embedding import FakeEmbedder
from media_search.ports.search import ImageSearchQuery, SearchQuery


def _seed(meta, vectors, embedder, *, asset_id, tags=None, display_name="", product_id=None, image_bytes=None):
    asset = MediaAsset(
        asset_id=asset_id,
        media_type=MediaType.IMAGE,
        mime_type="image/png",
        size_bytes=10,
        tags=tags or [],
        display_name=display_name or asset_id,
        product_id=product_id,
    )
    meta.upsert(asset)
    raw = image_bytes if image_bytes is not None else asset_id.encode()
    vectors.upsert_frame(
        asset_id=asset_id,
        frame_key=f"{asset_id}::0",
        position=0.0,
        vector=embedder.embed_image(raw).tolist(),
    )
    return raw


def test_text_merge_includes_display_name_match():
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    # Unrelated vector seed so semantic alone would not surface this asset
    _seed(
        meta,
        vectors,
        embedder,
        asset_id="sku.png",
        display_name="Acme Widget Pro",
        image_bytes=b"unrelated-visual",
    )
    use_case = SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta)
    hits = use_case.execute(SearchQuery(q="Widget Pro", top_k=5))
    assert any(h.asset.asset_id == "sku.png" for h in hits)
    hit = next(h for h in hits if h.asset.asset_id == "sku.png")
    assert "text" in hit.match_kinds


def test_text_merge_includes_tag_substring():
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    _seed(
        meta,
        vectors,
        embedder,
        asset_id="t.png",
        tags=["lipstick-rose"],
        image_bytes=b"noise",
    )
    use_case = SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta)
    hits = use_case.execute(SearchQuery(q="lipstick", top_k=5))
    assert hits[0].asset.asset_id == "t.png"
    assert "text" in hits[0].match_kinds


def test_product_id_filter_exact():
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    q = "shared"
    qvec = embedder.embed_text(q).tolist()
    for aid, pid in (("a.png", "SKU-1"), ("b.png", "SKU-2")):
        meta.upsert(
            MediaAsset(
                asset_id=aid,
                media_type=MediaType.IMAGE,
                mime_type="image/png",
                size_bytes=1,
                product_id=pid,
            )
        )
        vectors.upsert_frame(
            asset_id=aid, frame_key=f"{aid}::0", position=0.0, vector=qvec
        )
    use_case = SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta)
    hits = use_case.execute(SearchQuery(q=q, product_id="SKU-1", top_k=5))
    assert [h.asset.asset_id for h in hits] == ["a.png"]


def test_image_search_visual_knn():
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    query_bytes = b"query-image-bytes"
    _seed(
        meta,
        vectors,
        embedder,
        asset_id="match.png",
        image_bytes=query_bytes,
    )
    _seed(
        meta,
        vectors,
        embedder,
        asset_id="other.png",
        image_bytes=b"different",
    )
    use_case = SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta)
    hits = use_case.execute_image(
        ImageSearchQuery(image_bytes=query_bytes, top_k=5)
    )
    assert hits[0].asset.asset_id == "match.png"
    assert hits[0].match_kinds == ("visual",)


def test_empty_image_raises():
    use_case = SearchMediaAssets(
        embedder=FakeEmbedder(),
        vectors=InMemoryVectorSearch(),
        metadata=InMemoryMetadataRepository(),
    )
    try:
        use_case.execute_image(ImageSearchQuery(image_bytes=b""))
        assert False, "expected EmptyImageError"
    except EmptyImageError:
        pass


def test_api_post_text_and_by_image():
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    png = BytesIO()
    Image.new("RGB", (8, 8), (9, 8, 7)).save(png, format="PNG")
    raw = png.getvalue()
    _seed(
        meta,
        vectors,
        embedder,
        asset_id="p.png",
        display_name="Neon Bottle",
        product_id="SKU-N",
        image_bytes=raw,
    )
    app = create_app(
        search=SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta),
        metadata=meta,
    )
    client = TestClient(app)

    post = client.post("/api/search", json={"q": "Neon", "top_k": 5})
    assert post.status_code == 200
    assert post.json()["mode"] == "text"
    assert post.json()["results"][0]["asset_id"] == "p.png"
    assert "text" in post.json()["results"][0]["match_kinds"]

    filtered = client.get(
        "/api/search", params={"q": "Neon", "product_id": "SKU-N"}
    )
    assert filtered.status_code == 200
    assert filtered.json()["results"][0]["product_id"] == "SKU-N"

    miss = client.get(
        "/api/search", params={"q": "Neon", "product_id": "OTHER"}
    )
    assert miss.status_code == 200
    assert miss.json()["results"] == []

    by_img = client.post(
        "/api/search/by-image",
        files={"file": ("q.png", raw, "image/png")},
        data={"top_k": "5"},
    )
    assert by_img.status_code == 200
    body = by_img.json()
    assert body["mode"] == "visual_similar"
    assert body["results"][0]["asset_id"] == "p.png"
    assert body["results"][0]["match_kinds"] == ["visual"]

    empty = client.post(
        "/api/search/by-image",
        files={"file": ("q.png", b"", "image/png")},
    )
    assert empty.status_code == 400
