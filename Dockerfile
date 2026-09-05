# syntax=docker/dockerfile:1
# Thin local runtime for Feature 001 — models are NOT baked in.
FROM python:3.12-slim-bookworm

RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

ARG INSTALL_SEMANTIC=0
RUN pip install --no-cache-dir -e . \
  && if [ "$INSTALL_SEMANTIC" = "1" ]; then pip install --no-cache-dir -e ".[semantic]"; fi

ENV MEDIA_SEARCH_DATA=/data \
    MEDIA_SEARCH_MEDIA_ROOT=/data/incoming \
    MEDIA_SEARCH_DB=/data/media-fake.db \
    MEDIA_SEARCH_WORK=/data/work \
    EMBEDDER=fake \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "media_search.main:app", "--host", "0.0.0.0", "--port", "8000"]
