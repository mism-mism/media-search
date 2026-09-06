from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from media_search.adapters.local_media_storage import LocalMediaStorage
from media_search.adapters.memory_store import (
    InMemoryMetadataRepository,
    InMemoryProductRepository,
    InMemoryVectorSearch,
)
from media_search.api.app import create_app
from media_search.application.library import LibraryService
from media_search.application.search_media import SearchMediaAssets
from media_search.ports.embedding import FakeEmbedder
from media_search.ports.folder import Folder, FolderRepositoryPort


class _MemFolders(FolderRepositoryPort):
    def __init__(self) -> None:
        self._items: dict[str, Folder] = {}

    def upsert(self, folder: Folder) -> None:
        self._items[folder.folder_id] = folder

    def get(self, folder_id: str):
        return self._items.get(folder_id)

    def list_children(self, parent_id=None):
        return [
            f
            for f in self._items.values()
            if f.parent_id == parent_id
        ]

    def list_all(self):
        return list(self._items.values())

    def delete(self, folder_id: str) -> None:
        del self._items[folder_id]


def _png() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (8, 8), (1, 2, 3)).save(buf, format="PNG")
    return buf.getvalue()


def _app(tmp_path):
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    products = InMemoryProductRepository()
    folders = _MemFolders()
    storage = LocalMediaStorage(tmp_path / "media")
    library = LibraryService(
        folders=folders,
        metadata=meta,
        storage=storage,
        vectors=vectors,
        products=products,
    )
    app = create_app(
        search=SearchMediaAssets(embedder=embedder, vectors=vectors, metadata=meta),
        library=library,
        metadata=meta,
        media_storage=storage,
    )
    return app, library, products


def test_create_list_rename_product(tmp_path):
    app, library, _ = _app(tmp_path)
    client = TestClient(app)
    res = client.post(
        "/api/library/products",
        json={"product_id": "SKU-1", "name": "Lip A"},
    )
    assert res.status_code == 200
    assert res.json()["product_id"] == "SKU-1"
    listed = client.get("/api/library/products")
    assert listed.json()["products"][0]["name"] == "Lip A"
    renamed = client.patch(
        "/api/library/products/SKU-1", json={"name": "Lip A+"}
    )
    assert renamed.json()["name"] == "Lip A+"
    # id immutable: creating duplicate fails
    dup = client.post(
        "/api/library/products",
        json={"product_id": "SKU-1", "name": "other"},
    )
    assert dup.status_code == 400


def test_upload_binds_product_id(tmp_path):
    app, library, _ = _app(tmp_path)
    client = TestClient(app)
    client.post(
        "/api/library/products",
        json={"product_id": "SKU-9", "name": "Bottle"},
    )
    res = client.post(
        "/api/library/upload",
        files={"file": ("a.png", _png(), "image/png")},
        data={"product_id": "SKU-9"},
    )
    assert res.status_code == 200
    assert res.json()["asset"]["product_id"] == "SKU-9"


def test_upload_unknown_product_rejected(tmp_path):
    app, _, _ = _app(tmp_path)
    client = TestClient(app)
    res = client.post(
        "/api/library/upload",
        files={"file": ("a.png", _png(), "image/png")},
        data={"product_id": "MISSING"},
    )
    assert res.status_code == 400


def test_delete_product_blocked_when_in_use(tmp_path):
    app, library, _ = _app(tmp_path)
    client = TestClient(app)
    client.post(
        "/api/library/products",
        json={"product_id": "SKU-2", "name": "X"},
    )
    client.post(
        "/api/library/upload",
        files={"file": ("a.png", _png(), "image/png")},
        data={"product_id": "SKU-2"},
    )
    blocked = client.delete("/api/library/products/SKU-2")
    assert blocked.status_code == 409
    # free asset then delete ok
    aid = library.list_assets(None)[0].asset_id
    client.delete("/api/library/assets/" + aid)
    ok = client.delete("/api/library/products/SKU-2")
    assert ok.status_code == 200
