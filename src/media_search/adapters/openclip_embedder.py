from __future__ import annotations

import io
import os
from functools import lru_cache

import numpy as np
import torch
from PIL import Image

# Default Local embedder: multilingual text tower (JA queries included).
# Override with OPENCLIP_MODEL / OPENCLIP_PRETRAINED.
DEFAULT_OPENCLIP_MODEL = "xlm-roberta-base-ViT-B-32"
DEFAULT_OPENCLIP_PRETRAINED = "laion5b_s13b_b90k"


class OpenClipEmbedder:
    """Real local multimodal embedder (OpenCLIP). Used for semantic AC."""

    def __init__(
        self,
        *,
        model_name: str | None = None,
        pretrained: str | None = None,
        device: str | None = None,
    ) -> None:
        import open_clip

        self._model_name = model_name or os.environ.get(
            "OPENCLIP_MODEL", DEFAULT_OPENCLIP_MODEL
        )
        self._pretrained = pretrained or os.environ.get(
            "OPENCLIP_PRETRAINED", DEFAULT_OPENCLIP_PRETRAINED
        )
        self._device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model, _, self._preprocess = open_clip.create_model_and_transforms(
            self._model_name,
            pretrained=self._pretrained,
            device=self._device,
        )
        self._tokenizer = open_clip.get_tokenizer(self._model_name)
        self._model.eval()
        with torch.no_grad():
            dummy = self._tokenizer(["dim-probe"]).to(self._device)
            self._dimension = int(self._model.encode_text(dummy).shape[-1])

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_id(self) -> str:
        return f"open_clip:{self._model_name}/{self._pretrained}"

    def embed_image(self, image_bytes: bytes) -> np.ndarray:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = self._preprocess(image).unsqueeze(0).to(self._device)
        with torch.no_grad():
            feats = self._model.encode_image(tensor)
            feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats.squeeze(0).detach().cpu().numpy().astype(np.float32)

    def embed_text(self, text: str) -> np.ndarray:
        tokens = self._tokenizer([text.strip()]).to(self._device)
        with torch.no_grad():
            feats = self._model.encode_text(tokens)
            feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats.squeeze(0).detach().cpu().numpy().astype(np.float32)


@lru_cache(maxsize=1)
def get_shared_openclip_embedder() -> OpenClipEmbedder:
    """Process-wide singleton so model loads once (import + search)."""
    device = os.environ.get("MEDIA_SEARCH_DEVICE")
    return OpenClipEmbedder(device=device)


# Default tower output width for xlm-roberta-base-ViT-B-32 / laion5b.
# Override with OPENCLIP_DIMENSION if you change OPENCLIP_MODEL.
_DEFAULT_LOCAL_DIMENSION = 512


class LazyOpenClipEmbedder:
    """Defer HF/OpenCLIP load until first embed so Cloud Run can bind PORT."""

    def __init__(self) -> None:
        self._inner: OpenClipEmbedder | None = None
        self._dimension = int(
            os.environ.get("OPENCLIP_DIMENSION", str(_DEFAULT_LOCAL_DIMENSION))
        )
        model = os.environ.get("OPENCLIP_MODEL", DEFAULT_OPENCLIP_MODEL)
        pretrained = os.environ.get(
            "OPENCLIP_PRETRAINED", DEFAULT_OPENCLIP_PRETRAINED
        )
        self._pending_model_id = f"open_clip:{model}/{pretrained}"

    def _ensure(self) -> OpenClipEmbedder:
        if self._inner is None:
            self._inner = get_shared_openclip_embedder()
            self._dimension = self._inner.dimension
        return self._inner

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_id(self) -> str:
        if self._inner is None:
            return self._pending_model_id
        return self._inner.model_id

    def embed_image(self, image_bytes: bytes) -> np.ndarray:
        return self._ensure().embed_image(image_bytes)

    def embed_text(self, text: str) -> np.ndarray:
        return self._ensure().embed_text(text)
