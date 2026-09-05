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
RUN pip install --no-cache-dir -e . \
  && if [ "$INSTALL_SEMANTIC" = "1" ]; then pip install --no-cache-dir -e ".[semantic]"; fi \
  && if [ "$INSTALL_GCP" = "1" ]; then pip install --no-cache-dir -e ".[gcp]"; fi

ENV MEDIA_SEARCH_DATA=/data \
    MEDIA_SEARCH_MEDIA_ROOT=/data/incoming \
    MEDIA_SEARCH_DB=/data/media-local-cos.db \
    MEDIA_SEARCH_WORK=/data/work \
    EMBEDDER=local \
    MEDIA_BACKEND=local \
    PYTHONUNBUFFERED=1 \
    PORT=8080

EXPOSE 8080

# Cloud Run injects PORT; default 8080 for local parity.
CMD ["sh", "-c", "uvicorn media_search.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
