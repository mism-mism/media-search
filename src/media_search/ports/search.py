from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Sequence

from media_search.domain.media_asset import MediaAsset, MediaType


@dataclass(frozen=True)
class SearchQuery:
    q: str
    media_type: Optional[MediaType] = None
    tags: tuple[str, ...] = ()
    top_k: int = 5
    product_id: Optional[str] = None


@dataclass(frozen=True)
class ImageSearchQuery:
    image_bytes: bytes
    media_type: Optional[MediaType] = None
    tags: tuple[str, ...] = ()
    top_k: int = 5
    product_id: Optional[str] = None


class VectorSearchPort(Protocol):
    def upsert_frame(
        self,
        *,
        asset_id: str,
        frame_key: str,
        position: float,
        vector: Sequence[float],
    ) -> None: ...

    def delete_asset_frames(self, asset_id: str) -> None: ...

    def search(
        self,
        *,
        query_vector: Sequence[float],
        top_k: int,
    ) -> list[tuple[str, str, float, float]]:
        """Return list of (asset_id, frame_key, score, position)."""
        ...


class MetadataRepositoryPort(Protocol):
    def upsert(self, asset: MediaAsset) -> None: ...

    def get(self, asset_id: str) -> Optional[MediaAsset]: ...

    def list_all(self) -> list[MediaAsset]: ...

    def list_by_folder(self, folder_id: Optional[str]) -> list[MediaAsset]: ...

    def delete(self, asset_id: str) -> None: ...
