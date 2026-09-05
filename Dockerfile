# syntax=docker/dockerfile:1
# Multi-stage: keep torch/OpenCLIP + HF weights cached when only app code changes.
# Cloud Run listens on $PORT.

ARG PYTHON_IMAGE=python:3.12-slim-bookworm

# ----- base OS bits -----
FROM ${PYTHON_IMAGE} AS base
RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# ----- Python deps (invalidate only when pyproject / install flags change) -----
FROM base AS deps
ARG INSTALL_SEMANTIC=0
ARG INSTALL_GCP=0

COPY pyproject.toml README.md ./
# Minimal package so `pip install -e .` resolves without copying all of src.
RUN mkdir -p src/media_search/adapters src/media_search/ports \
  && printf '%s\n' '"""media-search package stub for Docker deps layer."""' > src/media_search/__init__.py \
  && touch src/media_search/adapters/__init__.py \
  && touch src/media_search/ports/__init__.py

# CPU torch only — default PyPI torch pulls CUDA wheels and OOMs on Cloud Run.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e . \
    && if [ "$INSTALL_SEMANTIC" = "1" ]; then \
         pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
         && pip install --no-cache-dir "open-clip-torch>=2.24.0" "transformers>=4.40.0"; \
       fi \
    && if [ "$INSTALL_GCP" = "1" ]; then pip install --no-cache-dir -e ".[gcp]"; fi

# ----- OpenCLIP weight bake (invalidate when embedder or deps change) -----
FROM deps AS models
ARG INSTALL_SEMANTIC=0
ARG PREWARM_OPENCLIP=0

ENV HF_HOME=/opt/hf-cache \
    TRANSFORMERS_CACHE=/opt/hf-cache \
    HUGGINGFACE_HUB_CACHE=/opt/hf-cache/hub \
    TORCH_HOME=/opt/torch-cache \
    XDG_CACHE_HOME=/opt/xdg-cache \
    HOME=/root

COPY src/media_search/adapters/openclip_embedder.py src/media_search/adapters/openclip_embedder.py

RUN if [ "$INSTALL_SEMANTIC" = "1" ] && [ "$PREWARM_OPENCLIP" = "1" ]; then \
      mkdir -p /opt/hf-cache /opt/torch-cache /opt/xdg-cache /root/.cache/clip \
      && python -c "from media_search.adapters.openclip_embedder import get_shared_openclip_embedder; e=get_shared_openclip_embedder(); print(e.model_id, e.dimension)" \
      && du -sh /opt/hf-cache /root/.cache/clip 2>/dev/null || true; \
    else \
      mkdir -p /opt/hf-cache /opt/torch-cache /opt/xdg-cache; \
    fi

# ----- runtime -----
FROM base AS runtime
ARG INSTALL_SEMANTIC=0

COPY --from=deps /usr/local /usr/local
COPY --from=models /opt/hf-cache /opt/hf-cache
COPY --from=models /opt/torch-cache /opt/torch-cache
COPY --from=models /opt/xdg-cache /opt/xdg-cache

COPY pyproject.toml README.md ./
COPY src ./src
# Refresh editable install against full sources without re-resolving deps.
RUN pip install --no-cache-dir --no-deps -e .

ENV HF_HOME=/opt/hf-cache \
    TRANSFORMERS_CACHE=/opt/hf-cache \
    HUGGINGFACE_HUB_CACHE=/opt/hf-cache/hub \
    TORCH_HOME=/opt/torch-cache \
    XDG_CACHE_HOME=/opt/xdg-cache \
    HOME=/root \
    MEDIA_SEARCH_DATA=/data \
    MEDIA_SEARCH_MEDIA_ROOT=/data/incoming \
    MEDIA_SEARCH_DB=/data/media-local-cos.db \
    MEDIA_SEARCH_WORK=/data/work \
    EMBEDDER=local \
    MEDIA_BACKEND=local \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

EXPOSE 8080

# Service: HTTP. Job overrides command to `python -m media_search.worker_import`.
CMD ["sh", "-c", "uvicorn media_search.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
