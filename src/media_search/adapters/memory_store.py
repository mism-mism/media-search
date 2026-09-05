from __future__ import annotations

from typing import Optional, Sequence

import numpy as np

from media_search.domain.media_asset import MediaAsset


class InMemoryMetadataRepository:
    def __init__(self) -> None:
        self._items: dict[str, MediaAsset] = {}

    def upsert(self, asset: MediaAsset) -> None:
        self._items[asset.asset_id] = asset

    def get(self, asset_id: str) -> Optional[MediaAsset]:
        return self._items.get(asset_id)

    def list_all(self) -> list[MediaAsset]:
        return list(self._items.values())

    def list_by_folder(self, folder_id: Optional[str]) -> list[MediaAsset]:
        return [
            a
            for a in self._items.values()
            if (folder_id is None and a.folder_id is None)
            or (folder_id is not None and a.folder_id == folder_id)
        ]

    def search_text(self, needle: str) -> list[MediaAsset]:
        n = needle.strip().lower()
        if not n:
            return []
        out: list[MediaAsset] = []
        for a in self._items.values():
            if n in (a.display_name or "").lower():
                out.append(a)
                continue
            if any(n in t.lower() for t in a.tags):
                out.append(a)
        return out

    def count_by_product_id(self, product_id: str) -> int:
        return sum(1 for a in self._items.values() if a.product_id == product_id)

    def delete(self, asset_id: str) -> None:
        self._items.pop(asset_id, None)


class InMemoryProductRepository:
    def __init__(self) -> None:
        self._items: dict[str, object] = {}

    def upsert(self, product) -> None:
        from media_search.domain.product import Product

        assert isinstance(product, Product)
        self._items[product.product_id] = product

    def get(self, product_id: str):
        return self._items.get(product_id)

    def list_all(self):
        from media_search.domain.product import Product

        items = [p for p in self._items.values() if isinstance(p, Product)]
        return sorted(items, key=lambda p: (p.name.lower(), p.product_id))

    def delete(self, product_id: str) -> None:
        self._items.pop(product_id, None)


class InMemoryVectorSearch:
    """Exact cosine over stored frame vectors (001-scale Fake/Local stand-in)."""

    def __init__(self) -> None:
        self._frames: dict[str, tuple[str, float, np.ndarray]] = {}
        # frame_key -> (asset_id, position, vector)

    def upsert_frame(
        self,
        *,
        asset_id: str,
        frame_key: str,
        position: float,
        vector: Sequence[float],
    ) -> None:
        vec = np.asarray(vector, dtype=float)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        self._frames[frame_key] = (asset_id, position, vec)

    def delete_asset_frames(self, asset_id: str) -> None:
        drop = [k for k, (aid, _, _) in self._frames.items() if aid == asset_id]
        for k in drop:
            del self._frames[k]

    def search(
        self,
        *,
        query_vector: Sequence[float],
        top_k: int,
    ) -> list[tuple[str, str, float, float]]:
        q = np.asarray(query_vector, dtype=float)
        qn = np.linalg.norm(q)
        if qn > 0:
            q = q / qn
        scored: list[tuple[str, str, float, float]] = []
        for frame_key, (asset_id, position, vec) in self._frames.items():
            score = float(np.dot(q, vec))
            scored.append((asset_id, frame_key, score, position))
        scored.sort(key=lambda t: t[2], reverse=True)
        return scored[:top_k]
