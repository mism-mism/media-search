from __future__ import annotations

import re
import uuid
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from media_search.domain.formats import classify_path
from media_search.domain.media_asset import MediaAsset, MediaType
from media_search.ports.folder import Folder, FolderRepositoryPort
from media_search.ports.frame_store import FrameStorePort
from media_search.ports.import_job import ImportJobPort, ImportJobRecord
from media_search.ports.media_storage import MediaStoragePort
from media_search.ports.search import MetadataRepositoryPort, VectorSearchPort


def _safe_filename(name: str) -> str:
    base = Path(name).name
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._") or "file"
    return safe[:180]


def _guess_mime(filename: str, media_type: MediaType) -> str:
    suffix = Path(filename).suffix.lower()
    mapping = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".mp4": "video/mp4",
    }
    if suffix in mapping:
        return mapping[suffix]
    return "image/jpeg" if media_type == MediaType.IMAGE else "video/mp4"


class LibraryService:
    def __init__(
        self,
        *,
        folders: FolderRepositoryPort,
        metadata: MetadataRepositoryPort,
        storage: MediaStoragePort,
        vectors: VectorSearchPort,
        frame_store: FrameStorePort | None = None,
        import_jobs: ImportJobPort | None = None,
        on_after_mutate: Callable[[], None] | None = None,
    ) -> None:
        self._folders = folders
        self._metadata = metadata
        self._storage = storage
        self._vectors = vectors
        self._frame_store = frame_store
        self._import_jobs = import_jobs
        self._on_after_mutate = on_after_mutate

    def list_folders(self, parent_id: str | None = None) -> list[Folder]:
        return self._folders.list_children(parent_id)

    def list_all_folders(self) -> list[Folder]:
        return self._folders.list_all()

    def create_folder(self, *, name: str, parent_id: str | None = None) -> Folder:
        name = name.strip()
        if not name:
            raise ValueError("folder name required")
        if parent_id is not None and self._folders.get(parent_id) is None:
            raise FileNotFoundError("parent folder not found")
        folder = Folder(folder_id=str(uuid.uuid4()), name=name, parent_id=parent_id)
        self._folders.upsert(folder)
        self._persist()
        return folder

    def delete_folder(self, folder_id: str) -> None:
        self._folders.delete(folder_id)
        self._persist()

    def list_assets(self, folder_id: str | None = None) -> list[MediaAsset]:
        return self._metadata.list_by_folder(folder_id)

    def upload(
        self,
        *,
        filename: str,
        data: bytes,
        folder_id: str | None = None,
        content_type: str | None = None,
        enqueue: bool = True,
    ) -> tuple[MediaAsset, ImportJobRecord | None]:
        kind_s = classify_path(Path(filename))
        if kind_s is None:
            raise ValueError("unsupported format")
        kind = MediaType(kind_s)
        if folder_id is not None and self._folders.get(folder_id) is None:
            raise FileNotFoundError("folder not found")
        safe = _safe_filename(filename)
        asset_id = f"library/{uuid.uuid4().hex}_{safe}"
        mime = content_type or _guess_mime(filename, kind)
        self._storage.put_bytes(asset_id, data, content_type=mime)
        asset = MediaAsset(
            asset_id=asset_id,
            media_type=kind,
            mime_type=mime,
            size_bytes=len(data),
            display_name=Path(filename).name,
            folder_id=folder_id,
        )
        self._metadata.upsert(asset)
        self._persist()
        job = None
        if enqueue and self._import_jobs is not None:
            job = self._import_jobs.enqueue()
        return asset, job

    def upload_many(
        self,
        *,
        items: list[tuple[str, bytes, str | None]],
        folder_id: str | None = None,
    ) -> tuple[list[MediaAsset], ImportJobRecord | None]:
        """Store many files, then enqueue a single Import job."""
        if not items:
            raise ValueError("no files")
        assets: list[MediaAsset] = []
        for filename, data, content_type in items:
            asset, _ = self.upload(
                filename=filename,
                data=data,
                folder_id=folder_id,
                content_type=content_type,
                enqueue=False,
            )
            assets.append(asset)
        job = None
        if self._import_jobs is not None:
            job = self._import_jobs.enqueue()
        return assets, job

    def rename(self, asset_id: str, display_name: str) -> MediaAsset:
        asset = self._require(asset_id)
        name = display_name.strip()
        if not name:
            raise ValueError("display_name required")
        asset = replace(asset, display_name=name)
        self._metadata.upsert(asset)
        self._persist()
        return asset

    def move(self, asset_id: str, folder_id: str | None) -> MediaAsset:
        asset = self._require(asset_id)
        if folder_id is not None and self._folders.get(folder_id) is None:
            raise FileNotFoundError("folder not found")
        asset = replace(asset, folder_id=folder_id)
        self._metadata.upsert(asset)
        self._persist()
        return asset

    def set_product_id(self, asset_id: str, product_id: str | None) -> MediaAsset:
        asset = self._require(asset_id)
        pid = product_id.strip() if product_id else None
        if pid == "":
            pid = None
        asset = replace(asset, product_id=pid)
        self._metadata.upsert(asset)
        self._persist()
        return asset

    def delete_asset(self, asset_id: str) -> None:
        self._require(asset_id)
        self._storage.delete(asset_id)
        self._vectors.delete_asset_frames(asset_id)
        if self._frame_store is not None:
            self._frame_store.delete_prefix(asset_id)
        self._metadata.delete(asset_id)
        self._persist()

    def _require(self, asset_id: str) -> MediaAsset:
        asset = self._metadata.get(asset_id)
        if asset is None:
            raise FileNotFoundError(asset_id)
        return asset

    def _persist(self) -> None:
        if self._on_after_mutate is not None:
            self._on_after_mutate()
