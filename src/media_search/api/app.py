from __future__ import annotations

from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel, Field

from media_search.adapters.local_media_storage import LocalMediaStorage
from media_search.application.import_directory import ImportDirectory
from media_search.application.library import LibraryService
from media_search.application.search_media import (
    EmptyImageError,
    EmptyQueryError,
    SearchMediaAssets,
)
from media_search.domain.media_asset import MediaType
from media_search.ports.frame_store import FrameStorePort
from media_search.ports.import_job import ImportJobPort, ImportJobStatus
from media_search.ports.import_lock import ImportLockBusy
from media_search.ports.media_storage import MediaStoragePort
from media_search.ports.search import ImageSearchQuery, MetadataRepositoryPort, SearchQuery


def _ui_html(*, embedder_mode: str, embedder_id: str) -> str:
    warn = ""
    if embedder_mode == "fake":
        warn = (
            '<p style="color:#a40;font-weight:600">'
            "EMBEDDER=fake — semantic quality is off. Use local OpenCLIP for real search."
            "</p>"
        )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>media-search library</title>
  <style>
    :root {{ font-family: ui-sans-serif, system-ui, sans-serif; color: #102015; }}
    body {{ margin: 1.25rem; max-width: 1100px; }}
    input, button, select {{ font: inherit; padding: 0.35rem 0.5rem; }}
    .row {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.75rem; align-items: center; }}
    .layout {{ display: grid; grid-template-columns: 220px 1fr; gap: 1rem; }}
    @media (max-width: 720px) {{ .layout {{ grid-template-columns: 1fr; }} }}
    .panel {{ border: 1px solid #d5ddd7; padding: 0.75rem; min-height: 12rem; }}
    .hit {{ display: grid; grid-template-columns: 96px 1fr auto; gap: 0.75rem;
           border-top: 1px solid #d5ddd7; padding: 0.65rem 0; align-items: center; }}
    .hit img {{ width: 96px; height: 72px; object-fit: cover; background: #eef2ef; }}
    .muted {{ color: #5b6a60; font-size: 0.85rem; }}
    .folder {{ display:block; padding: 0.25rem 0; cursor: pointer; }}
    .folder.active {{ font-weight: 700; }}
    a {{ color: #0b5; }}
    #status {{
      border: 1px solid #c5d0c8; background: #f4f7f5; padding: 0.65rem 0.75rem;
      margin-bottom: 0.75rem; min-height: 2.5rem;
    }}
    #status.busy {{ border-color: #c9a227; background: #fff8e6; }}
    #status.ok {{ border-color: #8bbb8b; background: #eef8ee; }}
    #status.err {{ border-color: #c97a7a; background: #fbeeee; }}
    .actions {{ display: flex; gap: 0.35rem; flex-wrap: wrap; align-items: center; }}
    .actions select {{ max-width: 10rem; }}
  </style>
</head>
<body>
  <h1>media-search</h1>
  <p class="muted">mode=<strong>{embedder_mode}</strong> · {embedder_id}</p>
  {warn}
  <div id="status" class="muted">待機中</div>
  <div class="row">
    <input id="q" size="36" placeholder="意味検索…" />
    <select id="mediaType">
      <option value="">any</option>
      <option value="image">image</option>
      <option value="video">video</option>
    </select>
    <button id="go">Search</button>
  </div>
  <div class="layout">
    <div class="panel">
      <div class="row">
        <strong>Folders</strong>
        <button id="rootBtn">/</button>
      </div>
      <div id="folders"></div>
      <div class="row">
        <input id="newFolder" size="12" placeholder="new folder" />
        <button id="addFolder">Add</button>
      </div>
    </div>
    <div class="panel">
      <div class="row">
        <span id="crumb" class="muted">folder: (root)</span>
        <select id="uploadProduct" title="Product (optional)">
          <option value="">(no product)</option>
        </select>
        <input id="file" type="file" accept=".jpg,.jpeg,.png,.mp4" multiple />
        <button id="upload">Upload</button>
      </div>
      <div class="row">
        <strong>Products</strong>
        <input id="newProductId" size="10" placeholder="SKU id" />
        <input id="newProductName" size="14" placeholder="name" />
        <button id="addProduct">Add product</button>
      </div>
      <div id="products" class="muted"></div>
      <div id="assets"></div>
      <div id="out"></div>
    </div>
  </div>
  <script>
    let currentFolder = null;
    let folderCache = [];
    let productCache = [];
    let busy = false;
    const foldersEl = document.getElementById('folders');
    const assetsEl = document.getElementById('assets');
    const productsEl = document.getElementById('products');
    const out = document.getElementById('out');
    const statusEl = document.getElementById('status');
    const crumb = document.getElementById('crumb');
    const uploadBtn = document.getElementById('upload');
    const uploadProduct = document.getElementById('uploadProduct');

    function setStatus(msg, kind) {{
      statusEl.textContent = msg;
      statusEl.className = kind || 'muted';
    }}

    async function pollJob(id) {{
      for (;;) {{
        const res = await fetch('/api/import/jobs/' + encodeURIComponent(id));
        const body = await res.json();
        if (!res.ok) {{
          setStatus('Import 状態取得失敗: ' + JSON.stringify(body), 'err');
          return body;
        }}
        const p = body.processed != null && body.total != null
          ? ` ${{body.processed}}/${{body.total}}` : '';
        const label = body.status === 'queued' ? 'キュー待ち'
          : body.status === 'running' ? 'インデックス処理中'
          : body.status === 'succeeded' ? '完了'
          : body.status === 'failed' ? '失敗'
          : body.status;
        setStatus(`Import: ${{label}}${{p}}` + (body.error ? ' — ' + body.error : ''),
          body.status === 'failed' ? 'err'
            : (body.status === 'succeeded' ? 'ok' : 'busy'));
        if (body.status === 'succeeded' || body.status === 'failed') {{
          await refreshAssets();
          return body;
        }}
        await new Promise(r => setTimeout(r, 800));
      }}
    }}

    async function loadAllFolders() {{
      const res = await fetch('/api/library/folders?all=1');
      const body = await res.json();
      folderCache = body.folders || [];
      return folderCache;
    }}

    function folderOptionsHtml(selected) {{
      const opts = ['<option value="">(root)</option>']
        .concat(folderCache.map(f =>
          `<option value="${{f.folder_id}}" ${{f.folder_id === selected ? 'selected' : ''}}>${{f.name}}</option>`
        ));
      return opts.join('');
    }}

    async function refreshFolders() {{
      const params = new URLSearchParams();
      if (currentFolder) params.set('parent_id', currentFolder);
      const res = await fetch('/api/library/folders?' + params.toString());
      const body = await res.json();
      foldersEl.innerHTML = (body.folders || []).map(f =>
        `<a class="folder" data-id="${{f.folder_id}}">${{f.name}}</a>`
      ).join('') || '<p class="muted">no subfolders</p>';
      foldersEl.querySelectorAll('.folder').forEach(el => {{
        el.onclick = () => {{ currentFolder = el.dataset.id; refreshAll(); }};
      }});
    }}

    async function refreshAssets() {{
      const params = new URLSearchParams();
      if (currentFolder) params.set('folder_id', currentFolder);
      else params.set('folder_id', '');
      const res = await fetch('/api/library/assets?' + params.toString());
      const body = await res.json();
      assetsEl.innerHTML = (body.assets || []).map(a => `
        <div class="hit">
          <img src="${{a.thumbnail_url}}" alt="" />
          <div>
            <div><a href="/api/assets/${{encodeURI(a.asset_id)}}">${{a.display_name || a.asset_id}}</a></div>
            <div class="muted">${{a.media_type}} · ${{a.product_id ? ('SKU ' + a.product_id + ' · ') : ''}}<code>${{a.asset_id}}</code></div>
          </div>
          <div class="actions">
            <button data-ren="${{a.asset_id}}">Rename</button>
            <select data-mov="${{a.asset_id}}" title="Move to folder">
              ${{folderOptionsHtml(a.folder_id || '')}}
            </select>
            <button data-del="${{a.asset_id}}">Delete</button>
          </div>
        </div>`).join('') || '<p class="muted">empty folder</p>';
      assetsEl.querySelectorAll('[data-del]').forEach(btn => {{
        btn.onclick = async () => {{
          if (!confirm('Delete?')) return;
          setStatus('削除中…', 'busy');
          await fetch('/api/library/assets/' + encodeURIComponent(btn.dataset.del), {{ method: 'DELETE' }});
          setStatus('削除しました', 'ok');
          refreshAssets();
        }};
      }});
      assetsEl.querySelectorAll('[data-ren]').forEach(btn => {{
        btn.onclick = async () => {{
          const name = prompt('New name');
          if (!name) return;
          setStatus('リネーム中…', 'busy');
          await fetch('/api/library/assets/' + encodeURIComponent(btn.dataset.ren), {{
            method: 'PATCH', headers: {{'Content-Type':'application/json'}},
            body: JSON.stringify({{ display_name: name }})
          }});
          setStatus('リネームしました', 'ok');
          refreshAssets();
        }};
      }});
      assetsEl.querySelectorAll('select[data-mov]').forEach(sel => {{
        sel.onchange = async () => {{
          const fid = sel.value || null;
          setStatus('移動中…', 'busy');
          const res = await fetch('/api/library/assets/' + encodeURIComponent(sel.dataset.mov), {{
            method: 'PATCH', headers: {{'Content-Type':'application/json'}},
            body: JSON.stringify({{ folder_id: fid }})
          }});
          if (!res.ok) {{
            setStatus('移動失敗: ' + await res.text(), 'err');
            return;
          }}
          setStatus('移動しました', 'ok');
          refreshAssets();
        }};
      }});
    }}

    async function refreshProducts() {{
      const res = await fetch('/api/library/products');
      const body = await res.json();
      productCache = body.products || [];
      uploadProduct.innerHTML = '<option value="">(no product)</option>' +
        productCache.map(p =>
          `<option value="${{p.product_id}}">${{p.name}} (${{p.product_id}})</option>`
        ).join('');
      productsEl.innerHTML = productCache.map(p =>
        `<div class="row"><code>${{p.product_id}}</code> ${{p.name}}
          <button data-pname="${{p.product_id}}">Rename</button>
          <button data-pdel="${{p.product_id}}">Delete</button></div>`
      ).join('') || '<p class="muted">no products yet</p>';
      productsEl.querySelectorAll('[data-pname]').forEach(btn => {{
        btn.onclick = async () => {{
          const name = prompt('New product name');
          if (!name) return;
          const res = await fetch('/api/library/products/' + encodeURIComponent(btn.dataset.pname), {{
            method: 'PATCH', headers: {{'Content-Type':'application/json'}},
            body: JSON.stringify({{ name }})
          }});
          if (!res.ok) {{ setStatus('商品名変更失敗: ' + await res.text(), 'err'); return; }}
          setStatus('商品名を更新しました', 'ok');
          refreshProducts();
        }};
      }});
      productsEl.querySelectorAll('[data-pdel]').forEach(btn => {{
        btn.onclick = async () => {{
          if (!confirm('Delete product?')) return;
          const res = await fetch('/api/library/products/' + encodeURIComponent(btn.dataset.pdel), {{
            method: 'DELETE'
          }});
          if (!res.ok) {{ setStatus('商品削除失敗: ' + await res.text(), 'err'); return; }}
          setStatus('商品を削除しました', 'ok');
          refreshProducts();
        }};
      }});
    }}

    async function refreshAll() {{
      crumb.textContent = 'folder: ' + (currentFolder || '(root)');
      await loadAllFolders();
      await refreshFolders();
      await refreshProducts();
      await refreshAssets();
      out.innerHTML = '';
    }}

    document.getElementById('rootBtn').onclick = () => {{ currentFolder = null; refreshAll(); }};
    document.getElementById('addFolder').onclick = async () => {{
      const name = document.getElementById('newFolder').value.trim();
      if (!name) return;
      await fetch('/api/library/folders', {{
        method: 'POST', headers: {{'Content-Type':'application/json'}},
        body: JSON.stringify({{ name, parent_id: currentFolder }})
      }});
      document.getElementById('newFolder').value = '';
      await loadAllFolders();
      refreshFolders();
    }};
    document.getElementById('addProduct').onclick = async () => {{
      const product_id = document.getElementById('newProductId').value.trim();
      const name = document.getElementById('newProductName').value.trim();
      if (!product_id || !name) {{
        setStatus('product_id と name を入力してください', 'err');
        return;
      }}
      const res = await fetch('/api/library/products', {{
        method: 'POST', headers: {{'Content-Type':'application/json'}},
        body: JSON.stringify({{ product_id, name }})
      }});
      if (!res.ok) {{ setStatus('商品追加失敗: ' + await res.text(), 'err'); return; }}
      document.getElementById('newProductId').value = '';
      document.getElementById('newProductName').value = '';
      setStatus('商品を追加しました', 'ok');
      refreshProducts();
    }};
    uploadBtn.onclick = async () => {{
      const input = document.getElementById('file');
      const files = Array.from(input.files || []);
      if (!files.length) {{
        setStatus('ファイルを選んでください', 'err');
        return;
      }}
      if (busy) return;
      busy = true;
      uploadBtn.disabled = true;
      try {{
        setStatus(`アップロード中 0/${{files.length}}…`, 'busy');
        const fd = new FormData();
        files.forEach(f => fd.append('files', f));
        if (currentFolder) fd.append('folder_id', currentFolder);
        if (uploadProduct.value) fd.append('product_id', uploadProduct.value);
        const res = await fetch('/api/library/upload', {{ method: 'POST', body: fd }});
        const body = await res.json();
        if (!res.ok) {{
          setStatus('アップロード失敗: ' + JSON.stringify(body), 'err');
          return;
        }}
        const n = (body.assets || []).length || (body.asset ? 1 : 0);
        setStatus(`${{n}} 件アップロード完了。インデックス開始…`, 'busy');
        input.value = '';
        await refreshAssets();
        const job = body.job;
        if (job && job.job_id) {{
          await pollJob(job.job_id);
        }} else {{
          setStatus(`${{n}} 件アップロード完了（Import ジョブなし）`, 'ok');
        }}
      }} finally {{
        busy = false;
        uploadBtn.disabled = false;
      }}
    }};
    document.getElementById('go').onclick = async () => {{
      const q = document.getElementById('q').value;
      const mediaType = document.getElementById('mediaType').value;
      const params = new URLSearchParams({{ q }});
      if (mediaType) params.set('media_type', mediaType);
      setStatus('検索中…', 'busy');
      const res = await fetch('/api/search?' + params.toString());
      const body = await res.json();
      if (!res.ok) {{
        setStatus('検索失敗', 'err');
        out.textContent = JSON.stringify(body);
        return;
      }}
      const hits = body.results || [];
      setStatus(`検索結果 ${{hits.length}} 件`, 'ok');
      out.innerHTML = '<h3>Search</h3>' + (hits.map(r => `
        <div class="hit">
          <img src="${{r.thumbnail_url}}" alt="" />
          <div>
            <div><a href="/api/assets/${{encodeURI(r.asset_id)}}">${{r.display_name || r.asset_id}}</a></div>
            <div class="muted">${{r.media_type}} · score ${{r.score.toFixed(4)}}</div>
          </div>
          <div></div>
        </div>`).join('') || '<p class="muted">no results</p>');
    }};
    refreshAll();
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
    display_name: str = ""
    product_id: str | None = None
    match_kinds: list[str] = Field(
        default_factory=list,
        description="semantic | text | visual (bare image KNN is visual similar, not SKU)",
    )


class SearchResponse(BaseModel):
    results: list[SearchHitOut]
    mode: str = Field(
        default="text",
        description="text | visual_similar (image search without SKU claim)",
    )


class TextSearchIn(BaseModel):
    q: str
    media_type: str | None = None
    tags: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=50)
    product_id: str | None = Field(
        default=None,
        description="When set, exact SKU filter on asset.product_id",
    )


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
    display_name: str = ""
    folder_id: str | None = None
    product_id: str | None = None


class FolderOut(BaseModel):
    folder_id: str
    name: str
    parent_id: str | None = None


class FolderCreateIn(BaseModel):
    name: str
    parent_id: str | None = None


class FolderListOut(BaseModel):
    folders: list[FolderOut]


class LibraryAssetOut(BaseModel):
    asset_id: str
    display_name: str
    media_type: str
    folder_id: str | None = None
    thumbnail_url: str
    product_id: str | None = None


class LibraryAssetsOut(BaseModel):
    assets: list[LibraryAssetOut]


class AssetPatchIn(BaseModel):
    display_name: str | None = None
    folder_id: str | None = None
    product_id: str | None = None


class ProductOut(BaseModel):
    product_id: str
    name: str


class ProductCreateIn(BaseModel):
    product_id: str
    name: str


class ProductPatchIn(BaseModel):
    name: str


class ProductListOut(BaseModel):
    products: list[ProductOut]


class ImportWarningOut(BaseModel):
    path: str
    reason: str


class ImportResponse(BaseModel):
    imported: list[str]
    updated: list[str]
    skipped: list[ImportWarningOut]


class ImportJobOut(BaseModel):
    job_id: str
    status: str
    holder: str
    processed: int = 0
    total: int | None = None
    imported: list[str] = Field(default_factory=list)
    updated: list[str] = Field(default_factory=list)
    skipped: list[ImportWarningOut] = Field(default_factory=list)
    error: str | None = None
    created_at: str = ""
    updated_at: str = ""


class StatsOut(BaseModel):
    assets: int
    images: int
    videos: int
    latest_job: ImportJobOut | None = None


class UploadOut(BaseModel):
    asset: LibraryAssetOut | None = None
    assets: list[LibraryAssetOut] = Field(default_factory=list)
    job: ImportJobOut | None = None


def _job_out(job) -> ImportJobOut:
    return ImportJobOut(
        job_id=job.job_id,
        status=job.status.value if isinstance(job.status, ImportJobStatus) else str(job.status),
        holder=job.holder,
        processed=job.processed,
        total=job.total,
        imported=list(job.imported),
        updated=list(job.updated),
        skipped=[ImportWarningOut(path=s.path, reason=s.reason) for s in job.skipped],
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _parse_media_type(media_type: str | None) -> MediaType | None:
    if not media_type:
        return None
    try:
        return MediaType(media_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid media_type") from exc


def _hits_out(hits) -> list[SearchHitOut]:
    results: list[SearchHitOut] = []
    for h in hits:
        best_key = h.best_frame.frame_key if h.best_frame else None
        mt_s = h.asset.media_type.value
        results.append(
            SearchHitOut(
                asset_id=h.asset.asset_id,
                media_type=mt_s,
                score=h.score,
                tags=list(h.asset.tags),
                best_frame_key=best_key,
                thumbnail_url=thumbnail_url_for(
                    media_type=mt_s,
                    asset_id=h.asset.asset_id,
                    best_frame_key=best_key,
                ),
                display_name=h.asset.display_name or h.asset.asset_id,
                product_id=h.asset.product_id,
                match_kinds=list(h.match_kinds),
            )
        )
    return results


def _run_text_search(
    search: SearchMediaAssets,
    *,
    q: str,
    media_type: str | None,
    tags: list[str],
    top_k: int,
    product_id: str | None,
) -> SearchResponse:
    mt = _parse_media_type(media_type)
    try:
        hits = search.execute(
            SearchQuery(
                q=q,
                media_type=mt,
                tags=tuple(tags),
                top_k=top_k,
                product_id=product_id or None,
            )
        )
    except EmptyQueryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SearchResponse(results=_hits_out(hits), mode="text")


def create_app(
    *,
    search: SearchMediaAssets,
    importer: ImportDirectory | None = None,
    import_jobs: ImportJobPort | None = None,
    library: LibraryService | None = None,
    metadata: MetadataRepositoryPort | None = None,
    media_root: Path | None = None,
    media_storage: MediaStoragePort | None = None,
    frame_root: Path | None = None,
    frame_store: FrameStorePort | None = None,
    on_after_import: Callable[[], None] | None = None,
    embedder_mode: str = "unknown",
    embedder_id: str = "unknown",
) -> FastAPI:
    storage = media_storage
    if storage is None and media_root is not None:
        storage = LocalMediaStorage(media_root)

    if frame_store is None and frame_root is not None:
        from media_search.adapters.local_frame_store import LocalFrameStore

        frame_store = LocalFrameStore(frame_root)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        # After PORT is bound: load OpenCLIP so the first user query is warm.
        search.warm()
        yield

    app = FastAPI(title="media-search", version="0.1.0", lifespan=lifespan)

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

    @app.get(
        "/api/search",
        response_model=SearchResponse,
        summary="Text search (semantic + display_name/tags)",
    )
    def api_search(
        q: str = Query(default=""),
        media_type: str | None = None,
        tags: list[str] = Query(default=[]),
        top_k: int = Query(default=5, ge=1, le=50),
        product_id: str | None = Query(
            default=None,
            description="Exact SKU filter when set",
        ),
    ) -> SearchResponse:
        return _run_text_search(
            search,
            q=q,
            media_type=media_type,
            tags=tags,
            top_k=top_k,
            product_id=product_id,
        )

    @app.post(
        "/api/search",
        response_model=SearchResponse,
        summary="Text search (JSON body)",
    )
    def api_search_post(body: TextSearchIn) -> SearchResponse:
        return _run_text_search(
            search,
            q=body.q,
            media_type=body.media_type,
            tags=body.tags,
            top_k=body.top_k,
            product_id=body.product_id,
        )

    @app.post(
        "/api/search/by-image",
        response_model=SearchResponse,
        summary="Visual-similar image search (not SKU unless product_id filter)",
    )
    async def api_search_by_image(
        file: UploadFile = File(...),
        media_type: str | None = Form(default=None),
        tags: list[str] = Form(default=[]),
        top_k: int = Form(default=5),
        product_id: str | None = Form(default=None),
    ) -> SearchResponse:
        if top_k < 1 or top_k > 50:
            raise HTTPException(status_code=400, detail="top_k must be 1..50")
        mt = _parse_media_type(media_type)
        data = await file.read()
        try:
            hits = search.execute_image(
                ImageSearchQuery(
                    image_bytes=data,
                    media_type=mt,
                    tags=tuple(tags),
                    top_k=top_k,
                    product_id=product_id or None,
                )
            )
        except EmptyImageError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return SearchResponse(results=_hits_out(hits), mode="visual_similar")

    @app.post("/api/import")
    def api_import(
        path: str = Query(
            default="",
            description="Local import directory override (sync). Empty → async job",
        ),
    ):
        if path.strip():
            if importer is None:
                raise HTTPException(status_code=501, detail="import not configured")
            try:
                root = Path(path)
                if not root.is_dir():
                    raise FileNotFoundError(f"import root not found: {root}")
                summary = importer.execute_storage(LocalMediaStorage(root))
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            if on_after_import is not None:
                on_after_import()
            return ImportResponse(
                imported=summary.imported,
                updated=summary.updated,
                skipped=[
                    ImportWarningOut(path=s.path, reason=s.reason) for s in summary.skipped
                ],
            )

        if import_jobs is not None:
            try:
                job = import_jobs.enqueue()
            except ImportLockBusy as exc:
                raise HTTPException(
                    status_code=409, detail={"error": "import_busy", "holder": exc.holder}
                ) from exc
            return _job_out(job)

        if importer is None:
            raise HTTPException(status_code=501, detail="import not configured")
        if storage is None:
            raise HTTPException(
                status_code=400, detail="path required when media storage unset"
            )
        summary = importer.execute_storage(storage)
        if on_after_import is not None:
            on_after_import()
        return ImportResponse(
            imported=summary.imported,
            updated=summary.updated,
            skipped=[
                ImportWarningOut(path=s.path, reason=s.reason) for s in summary.skipped
            ],
        )

    @app.get("/api/import/jobs/{job_id}", response_model=ImportJobOut)
    def api_import_job(job_id: str) -> ImportJobOut:
        if import_jobs is None:
            raise HTTPException(status_code=501, detail="import jobs not configured")
        job = import_jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return _job_out(job)

    @app.get("/api/import/status", response_model=ImportJobOut)
    def api_import_status() -> ImportJobOut:
        if import_jobs is None:
            raise HTTPException(status_code=501, detail="import jobs not configured")
        job = import_jobs.latest()
        if job is None:
            raise HTTPException(status_code=404, detail="no import jobs")
        return _job_out(job)

    @app.get("/api/stats", response_model=StatsOut)
    def api_stats() -> StatsOut:
        if metadata is None:
            raise HTTPException(status_code=501, detail="metadata not configured")
        assets = metadata.list_all()
        images = sum(1 for a in assets if a.media_type == MediaType.IMAGE)
        videos = sum(1 for a in assets if a.media_type == MediaType.VIDEO)
        latest = import_jobs.latest() if import_jobs is not None else None
        return StatsOut(
            assets=len(assets),
            images=images,
            videos=videos,
            latest_job=_job_out(latest) if latest else None,
        )

    def _library_asset_out(asset) -> LibraryAssetOut:
        return LibraryAssetOut(
            asset_id=asset.asset_id,
            display_name=asset.display_name or asset.asset_id,
            media_type=asset.media_type.value,
            folder_id=asset.folder_id,
            thumbnail_url=thumbnail_url_for(
                media_type=asset.media_type.value,
                asset_id=asset.asset_id,
                best_frame_key=None,
            ),
            product_id=asset.product_id,
        )

    @app.get("/api/library/folders", response_model=FolderListOut)
    def api_list_folders(
        parent_id: str | None = None,
        list_all: bool = Query(default=False, alias="all"),
    ) -> FolderListOut:
        if library is None:
            raise HTTPException(status_code=501, detail="library not configured")
        folders = library.list_all_folders() if list_all else library.list_folders(parent_id)
        return FolderListOut(
            folders=[
                FolderOut(folder_id=f.folder_id, name=f.name, parent_id=f.parent_id)
                for f in folders
            ]
        )

    @app.post("/api/library/folders", response_model=FolderOut)
    def api_create_folder(body: FolderCreateIn) -> FolderOut:
        if library is None:
            raise HTTPException(status_code=501, detail="library not configured")
        try:
            folder = library.create_folder(name=body.name, parent_id=body.parent_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return FolderOut(
            folder_id=folder.folder_id, name=folder.name, parent_id=folder.parent_id
        )

    @app.delete("/api/library/folders/{folder_id}")
    def api_delete_folder(folder_id: str) -> dict[str, str]:
        if library is None:
            raise HTTPException(status_code=501, detail="library not configured")
        try:
            library.delete_folder(folder_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"status": "deleted"}

    @app.get("/api/library/assets", response_model=LibraryAssetsOut)
    def api_library_assets(
        folder_id: str | None = Query(default=None),
    ) -> LibraryAssetsOut:
        if library is None:
            raise HTTPException(status_code=501, detail="library not configured")
        # Explicit empty string means root (null folder).
        fid: str | None
        if folder_id is None:
            fid = None
        elif folder_id == "":
            fid = None
        else:
            fid = folder_id
        assets = library.list_assets(fid)
        return LibraryAssetsOut(assets=[_library_asset_out(a) for a in assets])

    @app.post("/api/library/upload", response_model=UploadOut)
    async def api_library_upload(
        files: list[UploadFile] | None = File(default=None),
        file: UploadFile | None = File(default=None),
        folder_id: str | None = Form(default=None),
        product_id: str | None = Form(default=None),
    ) -> UploadOut:
        if library is None:
            raise HTTPException(status_code=501, detail="library not configured")
        uploads: list[UploadFile] = list(files or [])
        if file is not None:
            uploads.append(file)
        if not uploads:
            raise HTTPException(status_code=400, detail="no files")
        try:
            items: list[tuple[str, bytes, str | None]] = []
            for uf in uploads:
                data = await uf.read()
                items.append((uf.filename or "upload.bin", data, uf.content_type))
            if len(items) == 1:
                asset, job = library.upload(
                    filename=items[0][0],
                    data=items[0][1],
                    folder_id=folder_id or None,
                    content_type=items[0][2],
                    product_id=product_id or None,
                )
                out_asset = _library_asset_out(asset)
                return UploadOut(
                    asset=out_asset,
                    assets=[out_asset],
                    job=_job_out(job) if job else None,
                )
            assets, job = library.upload_many(
                items=items,
                folder_id=folder_id or None,
                product_id=product_id or None,
            )
            outs = [_library_asset_out(a) for a in assets]
            return UploadOut(
                asset=outs[0] if outs else None,
                assets=outs,
                job=_job_out(job) if job else None,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ImportLockBusy as exc:
            raise HTTPException(
                status_code=409, detail={"error": "import_busy", "holder": exc.holder}
            ) from exc

    @app.get("/api/library/products", response_model=ProductListOut)
    def api_list_products() -> ProductListOut:
        if library is None:
            raise HTTPException(status_code=501, detail="library not configured")
        return ProductListOut(
            products=[
                ProductOut(product_id=p.product_id, name=p.name)
                for p in library.list_products()
            ]
        )

    @app.post("/api/library/products", response_model=ProductOut)
    def api_create_product(body: ProductCreateIn) -> ProductOut:
        if library is None:
            raise HTTPException(status_code=501, detail="library not configured")
        try:
            product = library.create_product(
                product_id=body.product_id, name=body.name
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return ProductOut(product_id=product.product_id, name=product.name)

    @app.patch("/api/library/products/{product_id}", response_model=ProductOut)
    def api_patch_product(product_id: str, body: ProductPatchIn) -> ProductOut:
        if library is None:
            raise HTTPException(status_code=501, detail="library not configured")
        try:
            product = library.rename_product(product_id, body.name)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return ProductOut(product_id=product.product_id, name=product.name)

    @app.delete("/api/library/products/{product_id}")
    def api_delete_product(product_id: str) -> dict[str, str]:
        if library is None:
            raise HTTPException(status_code=501, detail="library not configured")
        try:
            library.delete_product(product_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "deleted"}

    @app.patch("/api/library/assets/{asset_id:path}", response_model=LibraryAssetOut)
    def api_patch_asset(asset_id: str, body: AssetPatchIn) -> LibraryAssetOut:
        if library is None:
            raise HTTPException(status_code=501, detail="library not configured")
        try:
            asset = None
            if body.display_name is not None:
                asset = library.rename(asset_id, body.display_name)
            if "folder_id" in body.model_fields_set:
                asset = library.move(asset_id, body.folder_id)
            if "product_id" in body.model_fields_set:
                asset = library.set_product_id(asset_id, body.product_id)
            if asset is None:
                raise HTTPException(status_code=400, detail="no changes")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _library_asset_out(asset)

    @app.delete("/api/library/assets/{asset_id:path}")
    def api_delete_asset(asset_id: str) -> dict[str, str]:
        if library is None:
            raise HTTPException(status_code=501, detail="library not configured")
        try:
            library.delete_asset(asset_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"status": "deleted"}

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
            display_name=asset.display_name or asset.asset_id,
            folder_id=asset.folder_id,
            product_id=asset.product_id,
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
        parts = [p for p in asset_id.replace("\\", "/").split("/") if p]
        if any(p == ".." for p in parts):
            raise HTTPException(status_code=400, detail="invalid asset path")
        stream = storage.open_stream(asset_id)
        return StreamingResponse(stream, media_type=asset.mime_type)

    @app.get("/thumbnails/{frame_key:path}")
    def thumbnail_file(frame_key: str):
        if frame_store is None:
            raise HTTPException(status_code=501, detail="thumbnails not configured")
        try:
            stream = frame_store.open_stream(frame_key)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="thumbnail missing") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid frame key") from exc
        data = stream.read()
        stream.close()
        return Response(content=data, media_type="image/jpeg")

    return app
