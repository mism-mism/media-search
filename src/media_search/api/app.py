from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from media_search.application.frame_paths import frame_cache_path
from media_search.application.import_directory import ImportDirectory, ImportSummary
from media_search.application.search_media import EmptyQueryError, SearchMediaAssets
from media_search.domain.media_asset import MediaType
from media_search.ports.search import MetadataRepositoryPort, SearchQuery


def _ui_html(*, embedder_mode: str, embedder_id: str) -> str:
    warn = ""
    if embedder_mode == "fake":
        warn = (
            '<p style="color:#a40;font-weight:600">'
            "いまは EMBEDDER=fake です。意味検索の精度は出ません。"
            "精度確認は <code>docker compose --profile local up --build media-search-local</code> "
            "で再 import してください。"
            "</p>"
        )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>media-search</title>
  <style>
    :root {{ font-family: ui-sans-serif, system-ui, sans-serif; color: #102015; }}
    body {{ margin: 1.5rem; max-width: 920px; }}
    input, button, select {{ font: inherit; padding: 0.4rem 0.55rem; }}
    .row {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }}
    .hit {{ display: grid; grid-template-columns: 96px 1fr; gap: 0.75rem;
           border-top: 1px solid #d5ddd7; padding: 0.75rem 0; }}
    .hit img {{ width: 96px; height: 72px; object-fit: cover; background: #eef2ef; }}
    .muted {{ color: #5b6a60; font-size: 0.85rem; }}
    a {{ color: #0b5; }}
    code {{ font-size: 0.85em; }}
  </style>
</head>
<body>
  <h1>media-search</h1>
  <p class="muted">mode=<strong>{embedder_mode}</strong> · {embedder_id}</p>
  {warn}
  <p class="muted">semantic query + mediaType / tags (AND)</p>
  <div class="row">
    <input id="q" size="40" placeholder="例: 女性 / a woman outdoors" />
    <select id="mediaType">
      <option value="">any type</option>
      <option value="image">image</option>
      <option value="video">video</option>
    </select>
    <input id="tags" size="24" placeholder="tags comma-separated" />
    <button id="go">Search</button>
  </div>
  <div id="out"></div>
  <script>
    const out = document.getElementById('out');
    document.getElementById('go').onclick = async () => {{
      const q = document.getElementById('q').value;
      const mediaType = document.getElementById('mediaType').value;
      const tags = document.getElementById('tags').value.split(',').map(s => s.trim()).filter(Boolean);
      const params = new URLSearchParams({{ q }});
      if (mediaType) params.set('media_type', mediaType);
      tags.forEach(t => params.append('tags', t));
      const res = await fetch('/api/search?' + params.toString());
      const body = await res.json();
      if (!res.ok) {{ out.textContent = JSON.stringify(body); return; }}
      out.innerHTML = (body.results || []).map(r => `
        <div class="hit">
          <div>
            <img src="${{r.thumbnail_url}}" alt="" />
          </div>
          <div>
            <div><a href="/api/assets/${{encodeURI(r.asset_id)}}">${{r.asset_id}}</a></div>
            <div class="muted">${{r.media_type}} · score ${{r.score.toFixed(4)}}</div>
            <div class="muted">tags: ${{(r.tags || []).join(', ') || '—'}}</div>
            ${{r.best_frame_key
              ? `<div class="muted">bestFrame: ${{r.best_frame_key}}</div>`
              : ''}}
          </div>
        </div>`).join('') || '<p class="muted">no results</p>';
    }};
  </script>
</body>
</html>
"""


def thumbnail_url_for(*, media_type: str, asset_id: str, best_frame_key: str | None) -> str:
    if media_type == MediaType.VIDEO.value and best_frame_key:
        return f"/thumbnails/{quote(best_frame_key, safe='')}"
    return f"/media/{quote(asset_id, safe='/')}"


class SearchHitOut(BaseModel):
    asset_id: str
    media_type: str
    score: float
    tags: list[str] = Field(default_factory=list)
    best_frame_key: str | None = None
    thumbnail_url: str


class SearchResponse(BaseModel):
    results: list[SearchHitOut]


class ImportWarningOut(BaseModel):
    path: str
    reason: str


class ImportResponse(BaseModel):
    imported: list[str]
    updated: list[str]
    skipped: list[ImportWarningOut]


class AssetDetailOut(BaseModel):
    asset_id: str
    media_type: str
    mime_type: str
    size_bytes: int
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    tags: list[str] = Field(default_factory=list)
    description: str = ""
    media_url: str


def create_app(
    *,
    search: SearchMediaAssets,
    importer: ImportDirectory | None = None,
    metadata: MetadataRepositoryPort | None = None,
    media_root: Path | None = None,
    frame_root: Path | None = None,
    embedder_mode: str = "unknown",
    embedder_id: str = "unknown",
) -> FastAPI:
    app = FastAPI(title="media-search", version="0.1.0")

    @app.get("/", response_class=HTMLResponse)
    def ui() -> str:
        return _ui_html(embedder_mode=embedder_mode, embedder_id=embedder_id)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "embedder_mode": embedder_mode,
            "embedder_id": embedder_id,
        }

    @app.get("/api/search", response_model=SearchResponse)
    def api_search(
        q: str = Query(default=""),
        media_type: str | None = None,
        tags: list[str] = Query(default=[]),
        top_k: int = Query(default=5, ge=1, le=50),
    ) -> SearchResponse:
        mt: MediaType | None = None
        if media_type:
            try:
                mt = MediaType(media_type)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="invalid media_type") from exc
        try:
            hits = search.execute(
                SearchQuery(q=q, media_type=mt, tags=tuple(tags), top_k=top_k)
            )
        except EmptyQueryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        results: list[SearchHitOut] = []
        for h in hits:
            best_key = h.best_frame.frame_key if h.best_frame else None
            mt = h.asset.media_type.value
            results.append(
                SearchHitOut(
                    asset_id=h.asset.asset_id,
                    media_type=mt,
                    score=h.score,
                    tags=list(h.asset.tags),
                    best_frame_key=best_key,
                    thumbnail_url=thumbnail_url_for(
                        media_type=mt,
                        asset_id=h.asset.asset_id,
                        best_frame_key=best_key,
                    ),
                )
            )
        return SearchResponse(results=results)

    @app.post("/api/import", response_model=ImportResponse)
    def api_import(path: str = Query(..., description="Import directory path")) -> ImportResponse:
        if importer is None:
            raise HTTPException(status_code=501, detail="import not configured")
        root = Path(path)
        try:
            summary: ImportSummary = importer.execute(root)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return ImportResponse(
            imported=summary.imported,
            updated=summary.updated,
            skipped=[
                ImportWarningOut(path=s.path, reason=s.reason) for s in summary.skipped
            ],
        )

    @app.get("/api/assets/{asset_id:path}", response_model=AssetDetailOut)
    def api_asset_detail(asset_id: str) -> AssetDetailOut:
        if metadata is None:
            raise HTTPException(status_code=501, detail="metadata not configured")
        asset = metadata.get(asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="asset not found")
        return AssetDetailOut(
            asset_id=asset.asset_id,
            media_type=asset.media_type.value,
            mime_type=asset.mime_type,
            size_bytes=asset.size_bytes,
            width=asset.width,
            height=asset.height,
            duration_seconds=asset.duration_seconds,
            tags=list(asset.tags),
            description=asset.description,
            media_url=f"/media/{asset.asset_id}",
        )

    @app.get("/media/{asset_id:path}")
    def media_file(asset_id: str) -> FileResponse:
        if media_root is None or metadata is None:
            raise HTTPException(status_code=501, detail="media not configured")
        asset = metadata.get(asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="asset not found")
        root = media_root.resolve()
        path = (root / asset_id).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid asset path") from exc
        if not path.is_file():
            raise HTTPException(status_code=404, detail="media file missing")
        return FileResponse(path, media_type=asset.mime_type)

    @app.get("/thumbnails/{frame_key:path}")
    def thumbnail_file(frame_key: str) -> FileResponse:
        if frame_root is None:
            raise HTTPException(status_code=501, detail="thumbnails not configured")
        root = frame_root.resolve()
        path = frame_cache_path(root, frame_key).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid frame key") from exc
        if not path.is_file():
            raise HTTPException(status_code=404, detail="thumbnail missing")
        return FileResponse(path, media_type="image/jpeg")

    return app
