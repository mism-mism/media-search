import threading
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from media_search.adapters.sqlite_store import (
    SqliteMetadataRepository,
    SqliteVecSearch,
    open_db,
)
from media_search.api.app import create_app
from media_search.adapters.media_probe import LocalMediaProbe
from media_search.application.import_directory import ImportDirectory
from media_search.application.search_media import SearchMediaAssets
from media_search.ports.embedding import FakeEmbedder


def test_sqlite_search_works_from_fastapi_threadpool(tmp_path: Path):
    """Regression: sync FastAPI routes run off the startup thread."""
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    Image.new("RGB", (16, 16), (9, 9, 9)).save(incoming / "a.png")

    embedder = FakeEmbedder(dimension=32)
    conn = open_db(tmp_path / "t.db")
    lock = threading.Lock()
    meta = SqliteMetadataRepository(conn, lock=lock)
    vectors = SqliteVecSearch(conn, dimension=32, lock=lock)
    importer = ImportDirectory(embedder=embedder, vectors=vectors, metadata=meta, media_probe=LocalMediaProbe())
    search = SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta)
    app = create_app(
        search=search,
        importer=importer,
        metadata=meta,
        media_root=incoming,
    )
    client = TestClient(app)
    assert client.post("/api/import", params={"path": str(incoming)}).status_code == 200

    q = "thread-safe"
    vectors.upsert_frame(
        asset_id="a.png",
        frame_key="a.png::0",
        position=0.0,
        vector=embedder.embed_text(q).tolist(),
    )
    res = client.get("/api/search", params={"q": q})
    assert res.status_code == 200
    assert res.json()["results"][0]["asset_id"] == "a.png"
