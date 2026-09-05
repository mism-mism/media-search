from __future__ import annotations

import hashlib
from typing import Protocol

import numpy as np


class EmbeddingPort(Protocol):
    """Multimodal embedding: image/frame and text share one vector space."""

    @property
    def dimension(self) -> int: ...

    def embed_image(self, image_bytes: bytes) -> np.ndarray: ...

    def embed_text(self, text: str) -> np.ndarray: ...


class FakeEmbedder:
    """Deterministic embedder for wiring tests. Must not satisfy semantic AC."""

    def __init__(self, dimension: int = 32) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_id(self) -> str:
        return "fake:deterministic-hash"

    def embed_image(self, image_bytes: bytes) -> np.ndarray:
        digest = hashlib.sha256(b"img:" + image_bytes).hexdigest()
        return self._from_seed(digest)

    def embed_text(self, text: str) -> np.ndarray:
        digest = hashlib.sha256(f"txt:{text.strip().lower()}".encode()).hexdigest()
        return self._from_seed(digest)

    def _from_seed(self, seed: str) -> np.ndarray:
        seed_int = int(seed[:16], 16)
        rng = np.random.default_rng(seed_int)
        vec = rng.standard_normal(self._dimension)
        norm = np.linalg.norm(vec)
        if norm == 0:
            return vec
        return vec / norm
