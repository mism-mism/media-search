# Cloud Run listens on $PORT
FROM python:3.12-slim-bookworm

RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

ARG INSTALL_SEMANTIC=0
ARG INSTALL_GCP=0
ARG PREWARM_OPENCLIP=0

# CPU torch only — default PyPI torch pulls CUDA wheels and OOMs on Cloud Run.
RUN pip install --no-cache-dir -e . \
  && if [ "$INSTALL_SEMANTIC" = "1" ]; then \
       pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
       && pip install --no-cache-dir "open-clip-torch>=2.24.0" "transformers>=4.40.0"; \
     fi \
  && if [ "$INSTALL_GCP" = "1" ]; then pip install --no-cache-dir -e ".[gcp]"; fi

# Bake OpenCLIP weights into the image so Cloud Run cold start skips HF download.
ENV HF_HOME=/opt/hf-cache \
    TRANSFORMERS_CACHE=/opt/hf-cache \
    HUGGINGFACE_HUB_CACHE=/opt/hf-cache/hub \
    TORCH_HOME=/opt/torch-cache \
    XDG_CACHE_HOME=/opt/xdg-cache \
    HOME=/root

RUN if [ "$INSTALL_SEMANTIC" = "1" ] && [ "$PREWARM_OPENCLIP" = "1" ]; then \
      mkdir -p /opt/hf-cache /opt/torch-cache /opt/xdg-cache /root/.cache/clip \
      && python -c "from media_search.adapters.openclip_embedder import get_shared_openclip_embedder; e=get_shared_openclip_embedder(); print(e.model_id, e.dimension)" \
      && du -sh /opt/hf-cache /root/.cache/clip 2>/dev/null || true; \
    fi

ENV MEDIA_SEARCH_DATA=/data \
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

# Cloud Run injects PORT; default 8080 for local parity.
CMD ["sh", "-c", "uvicorn media_search.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
