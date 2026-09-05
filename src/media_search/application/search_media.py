from __future__ import annotations

from media_search.domain.media_asset import AssetSearchHit, FrameHit, MediaAsset, MediaType
from media_search.ports.embedding import EmbeddingPort
from media_search.ports.search import MetadataRepositoryPort, SearchQuery, VectorSearchPort


class EmptyQueryError(ValueError):
    """Semantic query is required (HTTP 400)."""


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
        # Over-fetch frames then collapse + filter
        frame_hits = self._vectors.search(
            query_vector=query_vec.tolist(),
            top_k=max(query.top_k * 10, 50),
        )

        best_by_asset: dict[str, tuple[str, float, float]] = {}
        for asset_id, frame_key, score, position in frame_hits:
            prev = best_by_asset.get(asset_id)
            if prev is None or score > prev[1]:
                best_by_asset[asset_id] = (frame_key, score, position)

        hits: list[AssetSearchHit] = []
        for asset_id, (frame_key, score, position) in best_by_asset.items():
            asset = self._metadata.get(asset_id)
            if asset is None:
                continue
            if query.media_type is not None and asset.media_type != query.media_type:
                continue
            if query.tags and not _tags_include_all(asset.tags, query.tags):
                continue
            hits.append(
                AssetSearchHit(
                    asset=asset,
                    score=score,
                    best_frame=FrameHit(
                        frame_key=frame_key,
                        score=score,
                        position=position,
                    ),
                )
            )

        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[: query.top_k]


def _tags_include_all(asset_tags: list[str], required: tuple[str, ...]) -> bool:
    have = {t.lower() for t in asset_tags}
    return all(t.lower() in have for t in required)
