from __future__ import annotations

"""Eval-only OpenCLIP variant (not production default)."""

import io
import os

import numpy as np
import torch
from PIL import Image


class OpenClipVariantEmbedder:
    """Configurable OpenCLIP for offline bake-off (008)."""

    def __init__(
        self,
        *,
        model_name: str,
        pretrained: str,
        device: str | None = None,
    ) -> None:
        import open_clip

        self._model_name = model_name
        self._pretrained = pretrained
        self._device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model, _, self._preprocess = open_clip.create_model_and_transforms(
            model_name,
            pretrained=pretrained,
            device=self._device,
        )
        self._tokenizer = open_clip.get_tokenizer(model_name)
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
            feat = self._model.encode_image(tensor)
            feat = feat / feat.norm(dim=-1, keepdim=True)
        return feat.squeeze(0).detach().cpu().numpy().astype(float)

    def embed_text(self, text: str) -> np.ndarray:
        tokens = self._tokenizer([text]).to(self._device)
        with torch.no_grad():
            feat = self._model.encode_text(tokens)
            feat = feat / feat.norm(dim=-1, keepdim=True)
        return feat.squeeze(0).detach().cpu().numpy().astype(float)


def build_eval_embedder(pass_name: str):
    """Factory for sku-embedder-eval passes."""
    if pass_name in {"local", "baseline", "openclip"}:
        from media_search.adapters.openclip_embedder import get_shared_openclip_embedder

        return get_shared_openclip_embedder()
    if pass_name in {"openai-vitb32", "product-open"}:
        return OpenClipVariantEmbedder(
            model_name=os.environ.get("SKU_EVAL_MODEL", "ViT-B-32"),
            pretrained=os.environ.get("SKU_EVAL_PRETRAINED", "openai"),
        )
    raise ValueError(f"unknown eval pass: {pass_name}")
