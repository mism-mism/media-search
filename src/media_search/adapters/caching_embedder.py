from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from typing import Protocol

import numpy as np


class _Embedder(Protocol):
    @property
    def dimension(self) -> int: ...

    def embed_image(self, image_bytes: bytes) -> np.ndarray: ...

    def embed_text(self, text: str) -> np.ndarray: ...


class CachingEmbedder:
    """Process-local LRU for query embeddings (repeat searches)."""

    def __init__(
        self,
        inner: _Embedder,
        *,
        text_size: int = 256,
        image_size: int = 64,
    ) -> None:
        self._inner = inner
        self._text_size = max(1, text_size)
        self._image_size = max(1, image_size)
        self._text: OrderedDict[str, np.ndarray] = OrderedDict()
        self._image: OrderedDict[str, np.ndarray] = OrderedDict()
        self._lock = threading.Lock()

    @property
    def dimension(self) -> int:
        return self._inner.dimension

    @property
    def model_id(self) -> str:
        return getattr(self._inner, "model_id", "cached")

    def warm(self) -> None:
        warm = getattr(self._inner, "warm", None)
        if callable(warm):
            warm()
        else:
            self.embed_text("warmup")

    def embed_text(self, text: str) -> np.ndarray:
        key = text.strip().lower()
        with self._lock:
            hit = self._text.get(key)
            if hit is not None:
                self._text.move_to_end(key)
                return hit.copy()
        vec = self._inner.embed_text(text)
        with self._lock:
            self._text[key] = vec
            self._text.move_to_end(key)
            while len(self._text) > self._text_size:
                self._text.popitem(last=False)
        return vec

    def embed_image(self, image_bytes: bytes) -> np.ndarray:
        key = hashlib.sha256(image_bytes).hexdigest()
        with self._lock:
            hit = self._image.get(key)
            if hit is not None:
                self._image.move_to_end(key)
                return hit.copy()
        vec = self._inner.embed_image(image_bytes)
        with self._lock:
            self._image[key] = vec
            self._image.move_to_end(key)
            while len(self._image) > self._image_size:
                self._image.popitem(last=False)
        return vec
