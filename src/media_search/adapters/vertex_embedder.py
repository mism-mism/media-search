from __future__ import annotations

import os
from functools import lru_cache

import numpy as np


def _l2(vec: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    if norm == 0:
        return vec
    return vec / norm


class VertexEmbedder:
    """Vertex multimodal embeddings (EmbeddingPort).

    Prefers google-genai Gemini embedding models; falls back to
    ``multimodalembedding@001`` via vertexai.vision_models when needed.

    Eval / optional spike only — production default remains OpenCLIP.
    """

    def __init__(
        self,
        *,
        project: str | None = None,
        location: str | None = None,
        model: str | None = None,
        dimension: int | None = None,
    ) -> None:
        self._project = project or os.environ.get("VERTEX_PROJECT") or os.environ.get(
            "GOOGLE_CLOUD_PROJECT", ""
        )
        if not self._project:
            raise SystemExit("VERTEX_PROJECT or GOOGLE_CLOUD_PROJECT required")
        self._location = location or os.environ.get("VERTEX_LOCATION", "us-central1")
        self._model = model or os.environ.get(
            "VERTEX_EMBED_MODEL", "multimodalembedding@001"
        )
        self._dimension = int(
            dimension or os.environ.get("VERTEX_EMBED_DIM", "1408")
        )
        self._calls = 0
        self._backend = "unknown"
        self._init_backend()

    def _init_backend(self) -> None:
        if self._model.startswith("multimodalembedding"):
            import vertexai
            from vertexai.vision_models import MultiModalEmbeddingModel

            vertexai.init(project=self._project, location=self._location)
            self._mm = MultiModalEmbeddingModel.from_pretrained(self._model)
            self._backend = "vision_models"
            # multimodalembedding@001 default dim is 1408 (also 128/256/512)
            if os.environ.get("VERTEX_EMBED_DIM") is None:
                self._dimension = 1408
            return

        from google import genai
        from google.genai import types

        self._types = types
        self._client = genai.Client(
            vertexai=True, project=self._project, location=self._location
        )
        self._backend = "genai"

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_id(self) -> str:
        return f"vertex:{self._model}/dim{self._dimension}/{self._backend}"

    @property
    def api_calls(self) -> int:
        return self._calls

    def embed_image(self, image_bytes: bytes) -> np.ndarray:
        self._calls += 1
        if self._backend == "vision_models":
            from vertexai.vision_models import Image

            image = Image(image_bytes=image_bytes)
            emb = self._mm.get_embeddings(
                image=image, dimension=self._dimension
            )
            return _l2(np.asarray(emb.image_embedding, dtype=np.float32))

        mime = "image/jpeg"
        if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            mime = "image/png"
        part = self._types.Part.from_bytes(data=image_bytes, mime_type=mime)
        return self._embed_genai([part])

    def embed_text(self, text: str) -> np.ndarray:
        self._calls += 1
        if self._backend == "vision_models":
            emb = self._mm.get_embeddings(
                contextual_text=text.strip(), dimension=self._dimension
            )
            return _l2(np.asarray(emb.text_embedding, dtype=np.float32))
        return self._embed_genai([text.strip()])

    def _embed_genai(self, contents: list) -> np.ndarray:
        result = self._client.models.embed_content(
            model=self._model,
            contents=contents,
            config=self._types.EmbedContentConfig(
                output_dimensionality=self._dimension
            ),
        )
        embeddings = getattr(result, "embeddings", None) or []
        if not embeddings:
            raise RuntimeError(f"empty embeddings from {self._model}")
        return _l2(np.asarray(embeddings[0].values, dtype=np.float32))


@lru_cache(maxsize=1)
def get_shared_vertex_embedder() -> VertexEmbedder:
    return VertexEmbedder()
