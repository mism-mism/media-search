import sqlite3

import pytest
from fastapi.testclient import TestClient

from media_search.adapters.memory_store import InMemoryMetadataRepository, InMemoryVectorSearch
from media_search.adapters.sqlite_store import SqliteMetadataRepository
from media_search.api.app import create_app
from media_search.application.search_media import SearchMediaAssets
from media_search.domain.media_asset import MediaAsset, MediaType
from media_search.ports.embedding import FakeEmbedder
from media_search.ports.search import SearchQuery


@pytest.fixture(params=["memory", "sqlite"])
def metadata(request):
    if request.param == "memory":
        yield InMemoryMetadataRepository()
    else:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        yield SqliteMetadataRepository(conn)
        conn.close()


def asset(asset_id="target.png", *, display_name="plain", tags=(), **kwargs):
    return MediaAsset(
        asset_id=asset_id,
        media_type=MediaType.IMAGE,
        mime_type="image/png",
        size_bytes=1,
        display_name=display_name,
        tags=list(tags),
        **kwargs,
    )


@pytest.mark.parametrize(
    ("tags", "query", "matches"),
    [
        (["保湿化粧水"], "化粧水", True),
        (["化粧水"], r"u5316", False),
        (['say "hello"'], '"hello"', True),
        ([r"folder\item"], r"folder\item", True),
        (["sale 50%"], "50%", True),
        (["sale 500"], "50%", False),
        (["sku_1"], "sku_1", True),
        (["skuX1"], "sku_1", False),
        (["LiPsTiCk-Rose"], "  LIPSTICK  ", True),
        (["red", "blue"], 'red", "blue', False),
        (["red", "blue"], '["', False),
        (["red"], "' OR 1=1 --", False),
        (["red"], " \t ", False),
        ([], "[", False),
    ],
)
def test_search_matches_tag_values_not_json(metadata, tags, query, matches):
    metadata.upsert(asset(tags=tags))
    assert [a.asset_id for a in metadata.search_text(query)] == (
        ["target.png"] if matches else []
    )


@pytest.mark.parametrize("field", ["name", "tag"])
@pytest.mark.parametrize("indexed", [False, True])
def test_keyword_hit_survives_top_one_over_stronger_semantic_hit(metadata, field, indexed):
    embedder = FakeEmbedder()
    vectors = InMemoryVectorSearch()
    query_vector = embedder.embed_text("化粧水")
    metadata.upsert(asset(
        display_name="化粧水" if field == "name" else "plain",
        tags=["化粧水"] if field == "tag" else [],
    ))
    metadata.upsert(asset("noise.png"))
    vectors.upsert_frame(
        asset_id="noise.png", frame_key="noise::0", position=0,
        vector=query_vector.tolist(),
    )
    if indexed:
        vectors.upsert_frame(
            asset_id="target.png", frame_key="target::0", position=0.5,
            vector=(-query_vector).tolist(),
        )
    search = SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=metadata)
    hits = search.execute(SearchQuery(q="化粧水", top_k=1))
    assert [h.asset.asset_id for h in hits] == ["target.png"]
    assert "text" in hits[0].match_kinds
    if indexed:
        assert hits[0].match_kinds == ("semantic", "text")
        assert hits[0].best_frame.frame_key == "target::0"
        assert hits[0].best_frame.position == 0.5
    all_hits = search.execute(SearchQuery(q="化粧水", top_k=5))
    assert [h.asset.asset_id for h in all_hits] == ["target.png", "noise.png"]
    assert all_hits[0].score < all_hits[1].score


def test_keyword_ties_use_asset_id_and_higher_scores_stay_first(metadata):
    embedder = FakeEmbedder()
    vectors = InMemoryVectorSearch()
    for aid in ("z.png", "b.png", "a.png"):
        metadata.upsert(asset(aid, tags=["化粧水"]))
    vectors.upsert_frame(
        asset_id="z.png", frame_key="z::0", position=0,
        vector=embedder.embed_text("化粧水").tolist(),
    )
    search = SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=metadata)
    hits = search.execute(SearchQuery(q="化粧水", top_k=5))
    assert [h.asset.asset_id for h in hits] == ["z.png", "a.png", "b.png"]


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_api_keyword_ranking_and_filters(metadata, method):
    embedder = FakeEmbedder()
    vectors = InMemoryVectorSearch()
    metadata.upsert(asset(tags=["化粧水", "ad"], product_id="SKU-1"))
    metadata.upsert(asset("noise.png", tags=["ad"], product_id="SKU-1"))
    vectors.upsert_frame(
        asset_id="noise.png", frame_key="noise::0", position=0,
        vector=embedder.embed_text("化粧水").tolist(),
    )
    app = create_app(
        search=SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=metadata),
        metadata=metadata,
    )
    with TestClient(app) as client:
        for filters, expected in [
            ({}, ["target.png"]),
            ({"product_id": "SKU-1", "tags": ["ad", "化粧水"], "media_type": "image"}, ["target.png"]),
            ({"product_id": "SKU"}, []),
            ({"tags": ["missing"]}, []),
            ({"media_type": "video"}, []),
        ]:
            data = {"q": "化粧水", "top_k": 1, **filters}
            response = client.request(
                method, "/api/search", **({"params": data} if method == "GET" else {"json": data})
            )
            assert response.status_code == 200
            results = response.json()["results"]
            assert [h["asset_id"] for h in results] == expected
            if results:
                assert "text" in results[0]["match_kinds"]
