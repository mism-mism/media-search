from dataclasses import replace

import pytest

from media_search.adapters.memory_store import InMemoryMetadataRepository, InMemoryVectorSearch
from media_search.adapters.sqlite_store import SqliteMetadataRepository, open_db
from media_search.application.search_media import SearchMediaAssets
from media_search.domain.media_asset import ImageAnnotation, MediaAsset, MediaType
from media_search.ports.embedding import FakeEmbedder
from media_search.ports.search import SearchQuery


def annotation():
    return ImageAnnotation(tags=("白いボトル", "手持ち"), description="室内で容器を持っている。", model_id="test-model", prompt_version="ja-v1")


def annotated_asset():
    return MediaAsset(asset_id="a.png", media_type=MediaType.IMAGE, mime_type="image/png", size_bytes=10,
                      display_name="IMG_01", tags=["広告"], description="春の撮影", product_id="SKU-1", annotation=annotation())


@pytest.fixture(params=["memory", "sqlite"])
def metadata(request, tmp_path):
    if request.param == "memory":
        yield InMemoryMetadataRepository()
    else:
        conn = open_db(tmp_path / "annotations.db")
        yield SqliteMetadataRepository(conn)
        conn.close()


def test_generated_metadata_survives_sqlite_reload(tmp_path):
    path = tmp_path / "annotations.db"
    conn = open_db(path)
    SqliteMetadataRepository(conn).upsert(annotated_asset())
    conn.close()
    conn = open_db(path)
    restored = SqliteMetadataRepository(conn).get("a.png")
    assert restored == annotated_asset()
    assert restored.tags == ["広告"]
    assert restored.description == "春の撮影"
    assert restored.annotation_status == "ready"
    conn.close()


@pytest.mark.parametrize("query", ["手持ち", "室内", "春の撮影", "広告", "IMG_01"])
def test_all_descriptive_fields_are_searchable(metadata, query):
    metadata.upsert(annotated_asset())
    assert [a.asset_id for a in metadata.search_text(query)] == ["a.png"]
    search = SearchMediaAssets(embedder=FakeEmbedder(), vectors=InMemoryVectorSearch(), metadata=metadata)
    hits = search.execute(SearchQuery(q=query, tags=("広告", "手持ち"), product_id="SKU-1"))
    assert [h.asset.asset_id for h in hits] == ["a.png"]
    assert "text" in hits[0].match_kinds


@pytest.mark.parametrize("query", ["test-model", "ja-v1", 'ボトル", "手持ち', "u767d", "unknown"])
def test_generation_provenance_and_serialization_are_not_keywords(metadata, query):
    metadata.upsert(annotated_asset())
    assert metadata.search_text(query) == []


def test_failed_annotation_roundtrip(metadata):
    asset = replace(annotated_asset(), annotation=None, annotation_error="generation_failed")
    metadata.upsert(asset)
    assert metadata.get(asset.asset_id) == asset
    assert metadata.get(asset.asset_id).annotation_status == "failed"


def test_annotation_rejects_unbounded_output():
    with pytest.raises(ValueError):
        ImageAnnotation(tags=("x" * 100,), description="画像", model_id="model", prompt_version="v1")


def test_replacing_connection_with_old_database_migrates_generated_fields(tmp_path):
    old = open_db(tmp_path / "old.db")
    old_meta = SqliteMetadataRepository(old)
    old_meta.upsert(replace(annotated_asset(), annotation=None))
    old.execute("ALTER TABLE assets DROP COLUMN annotation_json")
    old.execute("ALTER TABLE assets DROP COLUMN annotation_error")
    old.commit()
    active = open_db(tmp_path / "active.db")
    meta = SqliteMetadataRepository(active)
    meta.replace_connection(old)
    assert meta.search_text("広告")[0].annotation is None
    meta.upsert(annotated_asset())
    assert meta.get("a.png").annotation == annotation()
    active.close()
    old.close()


def test_import_to_persisted_api_keyword_search(tmp_path):
    from fastapi.testclient import TestClient
    from PIL import Image
    from media_search.adapters.local_media_storage import LocalMediaStorage
    from media_search.adapters.media_probe import LocalMediaProbe
    from media_search.adapters.sqlite_store import SqliteFolderRepository
    from media_search.api.app import create_app
    from media_search.application.import_directory import ImportDirectory
    from media_search.application.library import LibraryService

    class Annotator:
        def annotate(self, image_bytes):
            return annotation()

    source = tmp_path / "source"
    source.mkdir()
    Image.new("RGB", (10, 10), "white").save(source / "IMG_01.png")
    storage = LocalMediaStorage(source)
    path = tmp_path / "api.db"
    conn = open_db(path)
    meta = SqliteMetadataRepository(conn)
    vectors = InMemoryVectorSearch()
    embedder = FakeEmbedder()
    ImportDirectory(embedder=embedder, metadata=meta, vectors=vectors, media_probe=LocalMediaProbe(), annotator=Annotator()).execute_storage(storage)
    conn.close()
    conn = open_db(path)
    meta = SqliteMetadataRepository(conn)
    library = LibraryService(metadata=meta, folders=SqliteFolderRepository(conn), storage=storage, vectors=vectors)
    app = create_app(search=SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta), metadata=meta, library=library)
    with TestClient(app) as client:
        for response in [
            client.get("/api/search", params={"q": "手持ち"}),
            client.post("/api/search", json={"q": "室内"}),
        ]:
            assert response.status_code == 200
            result = response.json()["results"][0]
            assert result["asset_id"] == "IMG_01.png"
            assert result["annotation"]["tags"] == ["白いボトル", "手持ち"]
            assert result["annotation_status"] == "ready"
            assert result["tags"] == []
        detail = client.get("/api/assets/IMG_01.png").json()
        assert detail["annotation"]["model_id"] == "test-model"
        assert detail["annotation"]["prompt_version"] == "ja-v1"
        listed = client.get("/api/library/assets").json()["assets"][0]
        assert listed["annotation"]["description"] == "室内で容器を持っている。"
    conn.close()


def test_annotation_card_escapes_generated_text():
    import json
    import re
    import subprocess
    from media_search.api.app import _ui_html

    html = _ui_html(embedder_mode="fake", embedder_id="fake")
    renderer = re.search(r"function annotationHtml\(asset\) \{.*?\n    \}", html, re.S)
    assert renderer is not None
    script = "const esc = s => String(s).replace(/[&<>\"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '\"':'&quot;', \"'\":'&#39;'}[c]));\n" + renderer[0]
    payload = {"media_type": "image", "annotation_status": "ready", "annotation": {"tags": ['<img src=x onerror=alert(1)>'], "description": '<script>alert(1)</script>'}}
    script += "\nprocess.stdout.write(annotationHtml(" + json.dumps(payload) + "));"
    rendered = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout
    assert "<script>" not in rendered and "<img" not in rendered
    assert "&lt;script&gt;" in rendered and "AI" in rendered
