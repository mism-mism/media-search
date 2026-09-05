from __future__ import annotations

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
from media_search.adapters.sqlite_store import SqliteFolderRepository, open_db
from media_search.api.app import create_app
from media_search.application.import_directory import ImportDirectory
from media_search.application.library import LibraryService
from media_search.application.search_media import SearchMediaAssets
from media_search.ports.embedding import FakeEmbedder
from media_search.ports.folder import Folder


class InMemoryFolderRepository:
    def __init__(self) -> None:
        self._items: dict[str, Folder] = {}

    def upsert(self, folder: Folder) -> None:
        self._items[folder.folder_id] = folder

    def get(self, folder_id: str) -> Folder | None:
        return self._items.get(folder_id)

    def list_children(self, parent_id: str | None = None) -> list[Folder]:
        return [
            f
            for f in self._items.values()
            if f.parent_id == parent_id
        ]

    def list_all(self) -> list[Folder]:
        return list(self._items.values())

    def delete(self, folder_id: str) -> None:
        del self._items[folder_id]


def _client(tmp_path: Path):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    work = tmp_path / "work"
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    folders = InMemoryFolderRepository()
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
    library = LibraryService(
        folders=folders,
        metadata=meta,
        storage=storage,
        vectors=vectors,
        frame_store=frame_store,
        import_jobs=jobs,
    )
    app = create_app(
        search=SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta),
        importer=importer,
        import_jobs=jobs,
        library=library,
        metadata=meta,
        media_storage=storage,
        frame_store=frame_store,
    )
    return TestClient(app), incoming


def test_library_folder_upload_move_rename_delete(tmp_path: Path):
    client, _ = _client(tmp_path)
    folder = client.post(
        "/api/library/folders", json={"name": "Campaign"}
    ).json()
    assert folder["name"] == "Campaign"

    png = tmp_path / "shot.png"
    Image.new("RGB", (12, 12), (3, 4, 5)).save(png)
    with png.open("rb") as fh:
        up = client.post(
            "/api/library/upload",
            data={"folder_id": folder["folder_id"]},
            files={"file": ("shot.png", fh, "image/png")},
        )
    assert up.status_code == 200, up.text
    body = up.json()
    assert body["asset"]["folder_id"] == folder["folder_id"]
    assert body["job"]["status"] == "succeeded"
    asset_id = body["asset"]["asset_id"]

    listed = client.get(
        "/api/library/assets", params={"folder_id": folder["folder_id"]}
    ).json()
    assert any(a["asset_id"] == asset_id for a in listed["assets"])

    ren = client.patch(
        f"/api/library/assets/{asset_id}",
        json={"display_name": "Hero"},
    )
    assert ren.status_code == 200
    assert ren.json()["display_name"] == "Hero"
    assert ren.json()["asset_id"] == asset_id

    mov = client.patch(
        f"/api/library/assets/{asset_id}",
        json={"folder_id": None},
    )
    assert mov.status_code == 200
    assert mov.json()["folder_id"] is None

    root = client.get("/api/library/assets", params={"folder_id": ""}).json()
    assert any(a["asset_id"] == asset_id for a in root["assets"])

    deleted = client.delete(f"/api/library/assets/{asset_id}")
    assert deleted.status_code == 200
    assert client.get(f"/api/assets/{asset_id}").status_code == 404


def test_library_multi_upload_one_job(tmp_path: Path):
    client, _ = _client(tmp_path)
    paths = []
    for i, color in enumerate([(10, 20, 30), (40, 50, 60), (70, 80, 90)]):
        p = tmp_path / f"n{i}.png"
        Image.new("RGB", (8, 8), color).save(p)
        paths.append(p)
    files = [("files", (p.name, p.read_bytes(), "image/png")) for p in paths]
    up = client.post("/api/library/upload", files=files)
    assert up.status_code == 200, up.text
    body = up.json()
    assert len(body["assets"]) == 3
    assert body["job"]["status"] == "succeeded"
    all_assets = client.get("/api/library/folders", params={"all": "1"}).json()
    assert "folders" in all_assets


def test_sqlite_folder_repo(tmp_path: Path):
    conn = open_db(tmp_path / "t.db")
    # Ensure assets table exists for empty-folder checks.
    from media_search.adapters.sqlite_store import SqliteMetadataRepository

    SqliteMetadataRepository(conn)
    repo = SqliteFolderRepository(conn)
    f = Folder(folder_id="f1", name="A", parent_id=None)
    repo.upsert(f)
    assert repo.get("f1") is not None
    assert repo.list_children(None)[0].name == "A"
