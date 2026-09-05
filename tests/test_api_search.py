from fastapi.testclient import TestClient
from PIL import Image

from media_search.adapters.memory_store import InMemoryMetadataRepository, InMemoryVectorSearch
from media_search.api.app import create_app
from media_search.adapters.media_probe import LocalMediaProbe
from media_search.application.import_directory import ImportDirectory
from media_search.application.search_media import SearchMediaAssets
from media_search.domain.media_asset import MediaAsset, MediaType
from media_search.ports.embedding import FakeEmbedder


def test_search_empty_q_returns_400():
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    app = create_app(
        search=SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta),
        metadata=meta,
    )
    client = TestClient(app)
    res = client.get("/api/search", params={"q": ""})
    assert res.status_code == 400


def test_health_ok():
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    app = create_app(
        search=SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta)
    )
    assert TestClient(app).get("/health").json()["status"] == "ok"


def test_search_returns_seeded_asset():
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    meta.upsert(
        MediaAsset(
            asset_id="x.png",
            media_type=MediaType.IMAGE,
            mime_type="image/png",
            size_bytes=1,
            tags=["demo"],
        )
    )
    q = "demo query"
    vectors.upsert_frame(
        asset_id="x.png",
        frame_key="x.png::0",
        position=0.0,
        vector=embedder.embed_text(q).tolist(),
    )
    app = create_app(
        search=SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta),
        metadata=meta,
    )
    res = TestClient(app).get("/api/search", params={"q": q, "tags": ["demo"]})
    assert res.status_code == 200
    body = res.json()
    assert body["results"][0]["asset_id"] == "x.png"


def test_import_and_media_endpoints(tmp_path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    Image.new("RGB", (16, 16), (1, 2, 3)).save(incoming / "m.png")
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    importer = ImportDirectory(embedder=embedder, vectors=vectors, metadata=meta, media_probe=LocalMediaProbe())
    app = create_app(
        search=SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta),
        importer=importer,
        metadata=meta,
        media_root=incoming,
    )
    client = TestClient(app)
    res = client.post("/api/import", params={"path": str(incoming)})
    assert res.status_code == 200
    assert res.json()["imported"] == ["m.png"]
    detail = client.get("/api/assets/m.png")
    assert detail.status_code == 200
    assert detail.json()["media_url"] == "/media/m.png"
    media = client.get("/media/m.png")
    assert media.status_code == 200
    assert media.headers["content-type"].startswith("image/png")


def test_video_search_returns_best_frame_thumbnail(tmp_path):
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
            "color=c=red:s=64x64:d=2",
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
    work = tmp_path / "work"
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    importer = ImportDirectory(
        embedder=embedder, vectors=vectors, metadata=meta, media_probe=LocalMediaProbe(), work_dir=work
    )
    app = create_app(
        search=SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta),
        importer=importer,
        metadata=meta,
        media_root=incoming,
        frame_root=work / "frames",
    )
    client = TestClient(app)
    assert client.post("/api/import", params={"path": str(incoming)}).status_code == 200
    res = client.get("/api/search", params={"q": "anything"})
    assert res.status_code == 200
    hit = res.json()["results"][0]
    assert hit["asset_id"] == "clip.mp4"
    assert hit["best_frame_key"] == "clip.mp4::0"
    assert hit["thumbnail_url"].startswith("/thumbnails/")
    thumb = client.get(hit["thumbnail_url"])
    assert thumb.status_code == 200
    assert thumb.headers["content-type"].startswith("image/jpeg")
    assert thumb.content[:2] == b"\xff\xd8"
