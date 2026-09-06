from __future__ import annotations

from media_search.domain.media_asset import AssetSearchHit, FrameHit, MediaAsset
from media_search.ports.embedding import EmbeddingPort
from media_search.ports.search import (
    ImageSearchQuery,
    MetadataRepositoryPort,
    SearchQuery,
    VectorSearchPort,
)

TEXT_MATCH_FLOOR = 0.15


class EmptyQueryError(ValueError):
    """Semantic query is required (HTTP 400)."""


class EmptyImageError(ValueError):
    """Query image bytes are required (HTTP 400)."""


class SearchMediaAssets:
    def __init__(
        self,
        *,
        embedder: EmbeddingPort,
        vectors: VectorSearchPort,
        metadata: MetadataRepositoryPort,
    ) -> None:
        self._embedder = embedder
        self._vectors = vectors
        self._metadata = metadata

    def execute(self, query: SearchQuery) -> list[AssetSearchHit]:
        q = query.q.strip()
        if not q:
            raise EmptyQueryError("semantic query q is required")

        query_vec = self._embedder.embed_text(q)
        best_by_asset = self._knn_best_by_asset(query_vec.tolist(), query.top_k)

        merged: dict[str, _HitAcc] = {}
        for asset_id, (frame_key, score, position) in best_by_asset.items():
            asset = self._metadata.get(asset_id)
            if asset is None:
                continue
            merged[asset_id] = _HitAcc(
                asset=asset,
                score=score,
                frame_key=frame_key,
                position=position,
                kinds={"semantic"},
            )

        needle = q.lower()
        for asset in self._metadata.search_text(needle):
            prev = merged.get(asset.asset_id)
            if prev is None:
                merged[asset.asset_id] = _HitAcc(
                    asset=asset,
                    score=TEXT_MATCH_FLOOR,
                    frame_key=None,
                    position=0.0,
                    kinds={"text"},
                )
            else:
                prev.kinds.add("text")
                if prev.score < TEXT_MATCH_FLOOR:
                    prev.score = TEXT_MATCH_FLOOR

        return self._finalize(merged, query)

    def warm(self) -> None:
        warm = getattr(self._embedder, "warm", None)
        if callable(warm):
            warm()
        else:
            self._embedder.embed_text("warmup")

    def execute_image(self, query: ImageSearchQuery) -> list[AssetSearchHit]:
        if not query.image_bytes:
            raise EmptyImageError("query image is required")

        query_vec = self._embedder.embed_image(query.image_bytes)
        best_by_asset = self._knn_best_by_asset(query_vec.tolist(), query.top_k)

        merged: dict[str, _HitAcc] = {}
        for asset_id, (frame_key, score, position) in best_by_asset.items():
            asset = self._metadata.get(asset_id)
            if asset is None:
                continue
            merged[asset_id] = _HitAcc(
                asset=asset,
                score=score,
                frame_key=frame_key,
                position=position,
                kinds={"visual"},
            )

        return self._finalize(merged, query)

    def _knn_best_by_asset(
        self, query_vector: list[float], top_k: int
    ) -> dict[str, tuple[str, float, float]]:
        frame_hits = self._vectors.search(
            query_vector=query_vector,
            top_k=max(top_k * 10, 50),
        )
        best_by_asset: dict[str, tuple[str, float, float]] = {}
        for asset_id, frame_key, score, position in frame_hits:
            prev = best_by_asset.get(asset_id)
            if prev is None or score > prev[1]:
                best_by_asset[asset_id] = (frame_key, score, position)
        return best_by_asset

    def _finalize(
        self,
        merged: dict[str, _HitAcc],
        query: SearchQuery | ImageSearchQuery,
    ) -> list[AssetSearchHit]:
        hits: list[AssetSearchHit] = []
        for acc in merged.values():
            asset = acc.asset
            if query.media_type is not None and asset.media_type != query.media_type:
                continue
            if query.tags and not _tags_include_all(asset.tags, query.tags):
                continue
            if query.product_id is not None:
                if (asset.product_id or "") != query.product_id:
                    continue
            best_frame = None
            if acc.frame_key is not None:
                best_frame = FrameHit(
                    frame_key=acc.frame_key,
                    score=acc.score,
                    position=acc.position,
                )
            kinds = tuple(sorted(acc.kinds))
            hits.append(
                AssetSearchHit(
                    asset=asset,
                    score=acc.score,
                    best_frame=best_frame,
                    match_kinds=kinds,
                )
            )

        if isinstance(query, SearchQuery):
            # A literal metadata match must survive top_k even when the
            # visual embedding assigns semantic-only candidates higher scores.
            hits.sort(key=lambda h: ("text" not in h.match_kinds, -h.score, h.asset.asset_id))
        else:
            hits.sort(key=lambda h: h.score, reverse=True)
        return hits[: query.top_k]


class _HitAcc:
    __slots__ = ("asset", "score", "frame_key", "position", "kinds")

    def __init__(
        self,
        *,
        asset: MediaAsset,
        score: float,
        frame_key: str | None,
        position: float,
        kinds: set[str],
    ) -> None:
        self.asset = asset
        self.score = score
        self.frame_key = frame_key
        self.position = position
        self.kinds = kinds


def _tags_include_all(asset_tags: list[str], required: tuple[str, ...]) -> bool:
    have = {t.lower() for t in asset_tags}
    return all(t.lower() in have for t in required)
