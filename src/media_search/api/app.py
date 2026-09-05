from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from media_search.adapters.local_media_storage import LocalMediaStorage
from media_search.application.frame_paths import frame_cache_path
from media_search.application.import_directory import ImportDirectory
from media_search.application.search_media import EmptyQueryError, SearchMediaAssets
from media_search.domain.media_asset import MediaType
from media_search.ports.media_storage import MediaStoragePort
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
    .row {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; align-items: center; }}
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
  <p id="indexInfo" class="muted">インデックス: 読み込み中…</p>
  {warn}
  <p class="muted">検索だけなら Import 不要（インデックスは GCS に永続化）。新規メディア追加時だけ Import。</p>
  <div class="row">
    <input id="q" size="40" placeholder="例: 女性 / a woman outdoors" />
    <select id="mediaType">
      <option value="">any type</option>
      <option value="image">image</option>
      <option value="video">video</option>
    </select>
    <input id="tags" size="24" placeholder="tags comma-separated" />
    <button id="go">Search</button>
    <button id="imp" type="button">Import（差分）</button>
    <button id="impForce" type="button" title="既存も再埋め込み（高コスト）">再インデックス</button>
  </div>
  <p id="status" class="muted"></p>
  <div id="out"></div>
  <script>
    const out = document.getElementById('out');
    const status = document.getElementById('status');
    const indexInfo = document.getElementById('indexInfo');

    async function refreshStats() {{
      try {{
        const res = await fetch('/api/stats');
        const body = await res.json();
        if (!res.ok) {{
          indexInfo.textContent = 'インデックス: 取得失敗';
          return;
        }}
        indexInfo.textContent =
          `インデックス済み: ${{body.indexed_assets}} 件` +
          (body.media_keys_known != null
            ? ` · ストレージ上のメディア: ${{body.media_keys_known}} 件`
            : '') +
          ' · Import は未登録分だけ処理します';
      }} catch (e) {{
        indexInfo.textContent = 'インデックス: 取得エラー';
      }}
    }}
    refreshStats();

    document.getElementById('go').onclick = async () => {{
      const q = document.getElementById('q').value.trim();
      if (!q) {{
        status.textContent = 'クエリを入力してください（空の検索は 400 です）';
        out.textContent = '';
        return;
      }}
      status.textContent = '検索中…（初回はモデル読み込みで数十秒かかることがあります）';
      const mediaType = document.getElementById('mediaType').value;
      const tags = document.getElementById('tags').value.split(',').map(s => s.trim()).filter(Boolean);
      const params = new URLSearchParams({{ q }});
      if (mediaType) params.set('media_type', mediaType);
      tags.forEach(t => params.append('tags', t));
      try {{
        const res = await fetch('/api/search?' + params.toString());
        const body = await res.json();
        if (!res.ok) {{
          status.textContent = '検索失敗';
          out.textContent = JSON.stringify(body);
          return;
        }}
        status.textContent = `ヒット: ${{(body.results || []).length}}`;
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
      }} catch (e) {{
        status.textContent = '検索エラー（コールドスタート／タイムアウトの可能性）: ' + e;
        out.textContent = '';
      }}
    }};

    async function runImport(force) {{
      status.textContent = force
        ? '再インデックス中…（全件埋め込み・高コスト。ページを閉じないでください）'
        : '差分 Import 中…（未登録のみ。ページを閉じないでください）';
      out.textContent = '';
      try {{
        const url = force ? '/api/import?force=true' : '/api/import';
        const res = await fetch(url, {{ method: 'POST' }});
        const body = await res.json();
        if (!res.ok) {{
          status.textContent = 'Import 失敗';
          out.textContent = JSON.stringify(body);
          return;
        }}
        const n = (body.imported || []).length;
        const u = (body.updated || []).length;
        const c = (body.unchanged || []).length;
        const s = (body.skipped || []).length;
        status.textContent =
          `Import 完了: imported=${{n}} updated=${{u}} unchanged=${{c}} skipped=${{s}}`;
        out.textContent = JSON.stringify(body, null, 2);
        await refreshStats();
      }} catch (e) {{
        status.textContent = 'Import エラー: ' + e;
      }}
    }}
    document.getElementById('imp').onclick = () => runImport(false);
    document.getElementById('impForce').onclick = () => {{
      if (!confirm('既存アセットも再埋め込みします。時間がかかり課金も増えます。続行しますか？')) return;
      runImport(true);
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
    unchanged: list[str] = Field(default_factory=list)
    skipped: list[ImportWarningOut]


class StatsOut(BaseModel):
    indexed_assets: int
    media_keys_known: int | None = None
    embedder_mode: str
    embedder_id: str


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
    media_storage: MediaStoragePort | None = None,
    frame_root: Path | None = None,
    on_after_import: Callable[[], None] | None = None,
    embedder_mode: str = "unknown",
    embedder_id: str = "unknown",
) -> FastAPI:
    storage = media_storage
    if storage is None and media_root is not None:
        storage = LocalMediaStorage(media_root)

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

    @app.get("/api/stats", response_model=StatsOut)
    def api_stats() -> StatsOut:
        indexed = len(metadata.list_all()) if metadata is not None else 0
        keys: int | None = None
        if storage is not None:
            try:
                keys = len(storage.list_media_keys())
            except Exception:  # noqa: BLE001
                keys = None
        return StatsOut(
            indexed_assets=indexed,
            media_keys_known=keys,
            embedder_mode=embedder_mode,
            embedder_id=embedder_id,
        )

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
    def api_import(
        path: str = Query(
            default="",
            description="Local import directory; empty uses configured media storage",
        ),
        force: bool = Query(
            default=False,
            description="If true, re-embed assets already in the index (expensive)",
        ),
    ) -> ImportResponse:
        if importer is None:
            raise HTTPException(status_code=501, detail="import not configured")
        try:
            if path.strip():
                from media_search.adapters.local_media_storage import LocalMediaStorage

                root = Path(path)
                if not root.is_dir():
                    raise FileNotFoundError(f"import root not found: {root}")
                summary = importer.execute_storage(
                    LocalMediaStorage(root), force=force
                )
            else:
                if storage is None:
                    raise HTTPException(
                        status_code=400, detail="path required when media storage unset"
                    )
                summary = importer.execute_storage(storage, force=force)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if on_after_import is not None:
            on_after_import()
        return ImportResponse(
            imported=summary.imported,
            updated=summary.updated,
            unchanged=summary.unchanged,
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
    def media_file(asset_id: str):
        if storage is None or metadata is None:
            raise HTTPException(status_code=501, detail="media not configured")
        asset = metadata.get(asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="asset not found")
        if not storage.exists(asset_id):
            raise HTTPException(status_code=404, detail="media file missing")
        try:
            # Reject traversal-style keys before streaming.
            parts = [p for p in asset_id.replace("\\", "/").split("/") if p]
            if any(p == ".." for p in parts):
                raise HTTPException(status_code=400, detail="invalid asset path")
        except HTTPException:
            raise
        stream = storage.open_stream(asset_id)
        return StreamingResponse(stream, media_type=asset.mime_type)

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
