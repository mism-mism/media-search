from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel, Field

from media_search.adapters.local_media_storage import LocalMediaStorage
from media_search.application.import_directory import ImportDirectory
from media_search.application.library import LibraryService
from media_search.application.search_media import EmptyQueryError, SearchMediaAssets
from media_search.domain.media_asset import MediaType
from media_search.ports.frame_store import FrameStorePort
from media_search.ports.import_job import ImportJobPort, ImportJobStatus
from media_search.ports.import_lock import ImportLockBusy
from media_search.ports.media_storage import MediaStoragePort
from media_search.ports.search import MetadataRepositoryPort, SearchQuery


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
  </style>
</head>
<body>
  <h1>media-search</h1>
  <p class="muted">mode=<strong>{embedder_mode}</strong> · {embedder_id}</p>
  {warn}
  <div class="row">
    <input id="q" size="36" placeholder="意味検索…" />
    <select id="mediaType">
      <option value="">any</option>
      <option value="image">image</option>
      <option value="video">video</option>
    </select>
    <button id="go">Search</button>
    <span id="job" class="muted"></span>
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
        <input id="file" type="file" accept=".jpg,.jpeg,.png,.mp4" />
        <button id="upload">Upload</button>
      </div>
      <div id="assets"></div>
      <div id="out"></div>
    </div>
  </div>
  <script>
    let currentFolder = null;
    const foldersEl = document.getElementById('folders');
    const assetsEl = document.getElementById('assets');
    const out = document.getElementById('out');
    const jobEl = document.getElementById('job');
    const crumb = document.getElementById('crumb');

    async function pollJob(id) {{
      for (;;) {{
        const res = await fetch('/api/import/jobs/' + encodeURIComponent(id));
        const body = await res.json();
        if (!res.ok) {{ jobEl.textContent = JSON.stringify(body); return; }}
        const p = body.processed != null && body.total != null ? ` ${{body.processed}}/${{body.total}}` : '';
        jobEl.textContent = `import ${{body.status}}${{p}}`;
        if (body.status === 'succeeded' || body.status === 'failed') {{
          await refreshAssets();
          return;
        }}
        await new Promise(r => setTimeout(r, 800));
      }}
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
            <div class="muted">${{a.media_type}} · <code>${{a.asset_id}}</code></div>
          </div>
          <div>
            <button data-ren="${{a.asset_id}}">Rename</button>
            <button data-mov="${{a.asset_id}}">Move</button>
            <button data-del="${{a.asset_id}}">Delete</button>
          </div>
        </div>`).join('') || '<p class="muted">empty folder</p>';
      assetsEl.querySelectorAll('[data-del]').forEach(btn => {{
        btn.onclick = async () => {{
          if (!confirm('Delete?')) return;
          await fetch('/api/library/assets/' + encodeURIComponent(btn.dataset.del), {{ method: 'DELETE' }});
          refreshAssets();
        }};
      }});
      assetsEl.querySelectorAll('[data-ren]').forEach(btn => {{
        btn.onclick = async () => {{
          const name = prompt('New name');
          if (!name) return;
          await fetch('/api/library/assets/' + encodeURIComponent(btn.dataset.ren), {{
            method: 'PATCH', headers: {{'Content-Type':'application/json'}},
            body: JSON.stringify({{ display_name: name }})
          }});
          refreshAssets();
        }};
      }});
      assetsEl.querySelectorAll('[data-mov]').forEach(btn => {{
        btn.onclick = async () => {{
          const fid = prompt('Target folder_id (empty = root)', currentFolder || '');
          await fetch('/api/library/assets/' + encodeURIComponent(btn.dataset.mov), {{
            method: 'PATCH', headers: {{'Content-Type':'application/json'}},
            body: JSON.stringify({{ folder_id: fid === null ? undefined : (fid || null) }})
          }});
          refreshAssets();
        }};
      }});
    }}

    async function refreshAll() {{
      crumb.textContent = 'folder: ' + (currentFolder || '(root)');
      await refreshFolders();
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
      refreshFolders();
    }};
    document.getElementById('upload').onclick = async () => {{
      const file = document.getElementById('file').files[0];
      if (!file) return;
      const fd = new FormData();
      fd.append('file', file);
      if (currentFolder) fd.append('folder_id', currentFolder);
      const res = await fetch('/api/library/upload', {{ method: 'POST', body: fd }});
      const body = await res.json();
      if (!res.ok) {{ jobEl.textContent = JSON.stringify(body); return; }}
      jobEl.textContent = 'uploaded ' + body.asset.display_name;
      if (body.job && body.job.job_id) await pollJob(body.job.job_id);
      else await refreshAssets();
    }};
    document.getElementById('go').onclick = async () => {{
      const q = document.getElementById('q').value;
      const mediaType = document.getElementById('mediaType').value;
      const params = new URLSearchParams({{ q }});
      if (mediaType) params.set('media_type', mediaType);
      const res = await fetch('/api/search?' + params.toString());
      const body = await res.json();
      if (!res.ok) {{ out.textContent = JSON.stringify(body); return; }}
      out.innerHTML = '<h3>Search</h3>' + ((body.results || []).map(r => `
        <div class="hit">
          <img src="${{r.thumbnail_url}}" alt="" />
          <div>
            <div><a href="/api/assets/${{encodeURI(r.asset_id)}}">${{r.asset_id}}</a></div>
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


class SearchResponse(BaseModel):
    results: list[SearchHitOut]


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


class LibraryAssetsOut(BaseModel):
    assets: list[LibraryAssetOut]


class AssetPatchIn(BaseModel):
    display_name: str | None = None
    folder_id: str | None = None


class UploadOut(BaseModel):
    asset: LibraryAssetOut
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
                )
            )
        return SearchResponse(results=results)

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
        )

    @app.get("/api/library/folders", response_model=FolderListOut)
    def api_list_folders(parent_id: str | None = None) -> FolderListOut:
        if library is None:
            raise HTTPException(status_code=501, detail="library not configured")
        folders = library.list_folders(parent_id)
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
        file: UploadFile = File(...),
        folder_id: str | None = Form(default=None),
    ) -> UploadOut:
        if library is None:
            raise HTTPException(status_code=501, detail="library not configured")
        data = await file.read()
        try:
            asset, job = library.upload(
                filename=file.filename or "upload.bin",
                data=data,
                folder_id=folder_id or None,
                content_type=file.content_type,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ImportLockBusy as exc:
            raise HTTPException(
                status_code=409, detail={"error": "import_busy", "holder": exc.holder}
            ) from exc
        return UploadOut(
            asset=_library_asset_out(asset),
            job=_job_out(job) if job else None,
        )

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
