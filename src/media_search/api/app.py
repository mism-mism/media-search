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
    from html import escape

    warn = (
        '<p>検証用の埋め込みモデルです。意味検索の精度は評価できません。</p>'
        if embedder_mode == "fake" else ""
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#141618" />
  <title>暗室アーカイブ — media-search</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+JP:wght@400;500;600&family=Zen+Old+Mincho:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    :root {{
      color-scheme: dark;
      --bg: #141618; --surface: #1e2124; --text: #ece8e1; --muted: #9a958c;
      --accent: #e2a15a; --danger: #d9786a; --line: #373a3c;
      font-family: 'IBM Plex Sans JP', sans-serif; color: var(--text); background: var(--bg);
    }}
    * {{ box-sizing: border-box; }}
    [hidden] {{ display: none !important; }}
    body {{ margin: 0; min-width: 320px; }}
    body::before {{
      content: ''; position: fixed; inset: 0; pointer-events: none; z-index: -1; opacity: .12;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='grain'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Cpath fill='%23fff' filter='url(%23grain)' opacity='.25' d='M0 0h180v180H0z'/%3E%3C/svg%3E");
    }}
    button, input, select {{ font: inherit; font-size: .82rem; border-radius: 4px; }}
    button, select {{ cursor: pointer; }}
    button {{ min-height: 38px; padding: .5rem .75rem; color: var(--text); border: 1px solid var(--line); background: transparent; }}
    button:hover {{ background: #2b2e31; border-color: var(--muted); }}
    button:disabled {{ cursor: wait; opacity: .5; }}
    input, select {{ min-width: 0; min-height: 40px; padding: .55rem .7rem; color: var(--text); background: var(--bg); border: 1px solid var(--line); }}
    input::placeholder {{ color: var(--muted); opacity: 1; }}
    :focus-visible {{ outline: 2px solid var(--accent); outline-offset: 4px; }}
    a {{ color: inherit; text-decoration: none; }}
    a:hover {{ text-decoration: underline; text-underline-offset: 4px; }}
    h1, h2, p {{ margin: 0; }}
    code, .mono {{ font-family: ui-monospace, monospace; font-size: .7rem; overflow-wrap: anywhere; }}
    .muted {{ color: var(--muted); font-size: .78rem; line-height: 1.8; }}
    .sr-only {{ position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; border: 0; }}
    .skip-link {{ position: fixed; top: -80px; left: 16px; z-index: 10; padding: 12px; background: var(--surface); }}
    .skip-link:focus {{ top: 12px; }}
    .shell {{ width: min(1440px, calc(100% - 96px)); margin-inline: auto; }}
    .masthead {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; padding-block: 25px; border-bottom: 1px solid var(--line); }}
    .brand {{ display: flex; align-items: center; gap: 12px; font-size: .9rem; letter-spacing: .07em; }}
    .brand-mark {{ width: 22px; height: 26px; border: 1px solid var(--muted); padding: 4px; display: inline-flex; }}
    .brand-mark::after {{ content: ''; width: 100%; border: 1px solid var(--muted); }}
    .masthead-note {{ color: var(--muted); font-size: .72rem; letter-spacing: .1em; }}
    .hero {{ padding: 44px 0 26px; animation: hero-in .65s ease-out both; }}
    .eyebrow {{ color: var(--muted); font-size: .7rem; letter-spacing: .2em; margin-bottom: 13px; }}
    h1 {{ font-family: 'Zen Old Mincho', serif; font-weight: 400; font-size: clamp(2rem, 3.5vw, 3.25rem); letter-spacing: .09em; line-height: 1.45; }}
    .hero p:last-child {{ color: var(--muted); font-size: .82rem; margin-top: 14px; line-height: 1.9; }}
    .search-dock {{ position: relative; }}
    .search-dock::before {{ content: ''; position: absolute; inset: -180px 0 -40px; z-index: -1; pointer-events: none; background: radial-gradient(ellipse at 45% 60%, #e2a15a0c, transparent 68%); }}
    .search-form {{ display: flex; align-items: center; gap: 16px; padding: 9px 10px 9px 22px; background: var(--surface); border: 1px solid #71604c; border-radius: 6px; }}
    .search-form:focus-within {{ border-color: var(--accent); }}
    .search-icon {{ width: 20px; height: 20px; flex-shrink: 0; color: var(--accent); }}
    #q {{ flex: 1; width: 100%; padding: 12px 0; border: 0; background: transparent; font-size: 1rem; }}
    #mediaType {{ border: 0; border-left: 1px solid var(--line); border-radius: 0; background: transparent; padding-inline: 18px; }}
    #go {{ background: var(--accent); color: var(--bg); border-color: var(--accent); min-width: 106px; min-height: 48px; font-weight: 600; }}
    #go:hover {{ background: #edb87e; }}
    .status-line {{ min-height: 53px; display: flex; align-items: center; gap: 10px; padding: 12px 0; }}
    #status {{ font-size: .76rem; color: var(--muted); overflow-wrap: anywhere; }}
    #status::before {{ content: ''; display: inline-block; width: 5px; height: 5px; margin: 0 10px 2px 0; border-radius: 50%; background: currentColor; }}
    #status.busy::before {{ animation: status-pulse 1.4s ease-in-out infinite; }}
    #status.ok {{ color: var(--text); }}
    #status.err {{ color: var(--danger); }}
    .layout {{ display: grid; grid-template-columns: 228px minmax(0, 1fr); gap: 32px; border-top: 1px solid var(--line); min-height: 480px; }}
    .sidebar {{ padding: 27px 25px 32px 0; border-right: 1px solid var(--line); min-width: 0; }}
    .section-label {{ font-size: .72rem; font-weight: 500; color: var(--muted); letter-spacing: .12em; margin-bottom: 15px; }}
    .folder {{ display: flex; width: 100%; align-items: center; text-align: left; gap: 10px; border: 0; padding: 10px; margin-bottom: 3px; overflow-wrap: anywhere; }}
    .folder::before {{ content: ''; width: 14px; height: 11px; border: 1px solid var(--muted); border-radius: 2px; flex-shrink: 0; }}
    .folder.active {{ background: var(--surface); }}
    #folders {{ margin-top: 8px; }}
    #folders > p {{ padding: 8px 10px; }}
    .folder-create {{ display: flex; gap: 6px; margin-top: 19px; }}
    .folder-create input {{ width: 100%; }}
    .folder-create button {{ flex-shrink: 0; }}
    .products-section {{ margin-top: 30px; padding-top: 22px; border-top: 1px solid var(--line); }}
    summary {{ font-size: .8rem; cursor: pointer; padding: 5px 0; }}
    .products-section > p {{ margin: 12px 0; }}
    .product-form {{ display: grid; gap: 8px; margin: 16px 0; }}
    .product-row {{ border-top: 1px solid var(--line); padding: 14px 0; overflow-wrap: anywhere; }}
    .product-row code {{ display: block; color: var(--muted); margin-bottom: 4px; }}
    .product-row .actions {{ margin-top: 9px; }}
    .workspace {{ min-width: 0; padding: 14px 0 40px; }}
    .view-switch {{ display: flex; gap: 24px; border-bottom: 1px solid var(--line); }}
    .view-switch button {{ border: 0; border-radius: 0; padding: 13px 0 17px; color: var(--muted); }}
    .view-switch button[aria-pressed="true"] {{ color: var(--text); border-bottom: 2px solid var(--text); }}
    .view-switch button:hover {{ background: transparent; color: var(--text); }}
    .collection-heading {{ display: flex; align-items: baseline; justify-content: space-between; gap: 16px; margin: 24px 0 18px; }}
    #crumb {{ font-size: .95rem; font-weight: 500; line-height: 1.6; overflow-wrap: anywhere; }}
    #count {{ white-space: nowrap; }}
    .upload-toolbar {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px; padding: 13px; margin-bottom: 22px; background: var(--surface); border: 1px solid var(--line); border-radius: 4px; }}
    .file-picker {{ position: relative; flex-shrink: 0; }}
    .file-picker input {{ position: absolute; inset: 0; opacity: 0; width: 100%; cursor: pointer; }}
    .file-picker label {{ display: block; border: 1px solid var(--line); border-radius: 4px; padding: 10px 12px; font-size: .78rem; }}
    .file-picker:hover label {{ border-color: var(--muted); }}
    .file-picker:focus-within {{ outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 4px; }}
    #fileName {{ flex: 1 1 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    #uploadProduct {{ max-width: 190px; }}
    #upload {{ background: #34383b; }}
    .asset-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 24px 18px; }}
    .asset-card {{ min-width: 0; background: var(--surface); border: 1px solid var(--line); border-radius: 4px; overflow: hidden; }}
    #out .asset-card {{ animation: result-in .35s ease-out both; animation-delay: calc(var(--order, 0) * 45ms); }}
    .thumbnail {{ display: block; aspect-ratio: 4 / 3; background: #191b1e; border-bottom: 1px solid var(--line); overflow: hidden; }}
    .thumbnail img {{ display: block; width: 100%; height: 100%; object-fit: contain; color: var(--muted); font-size: .8rem; }}
    .thumbnail:focus-visible {{ outline-offset: -4px; }}
    .asset-info {{ padding: 13px 13px 8px; }}
    .asset-name {{ font-size: .87rem; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .asset-caption {{ margin-top: 6px; font-size: .7rem; color: var(--muted); overflow-wrap: anywhere; line-height: 1.8; }}
    .asset-id {{ display: block; margin-top: 4px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }}
    .actions button, .actions select {{ font-size: .7rem; min-height: 34px; padding: .35rem .45rem; }}
    .asset-actions {{ padding: 4px 12px 12px; }}
    .asset-actions select {{ flex: 1; width: 70px; }}
    .danger {{ color: var(--danger); }}
    .empty-state {{ grid-column: 1 / -1; display: grid; justify-items: center; align-content: center; min-height: 280px; padding: 35px 20px; border: 1px dashed var(--line); border-radius: 4px; text-align: center; }}
    .empty-mark {{ width: 48px; height: 40px; border: 1px solid #5a5c5d; box-shadow: 6px -6px 0 -1px var(--bg), 6px -6px 0 0 var(--line); margin-bottom: 25px; }}
    .empty-state h3 {{ margin: 0 0 10px; font-family: 'Zen Old Mincho', serif; font-size: 1.2rem; font-weight: 400; }}
    .empty-state p {{ color: var(--muted); font-size: .78rem; line-height: 1.9; max-width: 360px; }}
    footer {{ border-top: 1px solid var(--line); padding-block: 22px 30px; display: flex; flex-wrap: wrap; justify-content: space-between; gap: 12px; color: var(--muted); font-size: .7rem; }}
    footer .debug {{ text-align: right; max-width: 100%; overflow-wrap: anywhere; }}
    footer p {{ margin-top: 4px; }}
    @media (hover: hover) and (pointer: fine) {{
      .asset-actions {{ opacity: 0; }}
      .asset-card:hover .asset-actions, .asset-card:focus-within .asset-actions {{ opacity: 1; }}
    }}
    @media (min-width: 1500px) {{ .asset-grid {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }} }}
    @media (max-width: 1100px) {{
      .shell {{ width: calc(100% - 56px); }}
      .layout {{ grid-template-columns: 200px minmax(0, 1fr); gap: 24px; }}
      .sidebar {{ padding-right: 20px; }}
      .asset-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 720px) {{
      .shell {{ width: calc(100% - 32px); }}
      .masthead {{ padding-block: 20px; }}
      .masthead-note {{ font-size: .62rem; }}
      .hero {{ padding: 30px 0 22px; }}
      .hero p:last-child {{ font-size: .76rem; }}
      .search-dock {{ position: sticky; top: 0; z-index: 3; padding-block: 8px; background: var(--bg); }}
      .search-dock::before {{ display: none; }}
      .search-form {{ gap: 7px; padding: 7px; }}
      .search-icon {{ display: none; }}
      #q {{ font-size: 16px; padding-left: 4px; }}
      #mediaType {{ padding-inline: 6px; width: 73px; font-size: .75rem; }}
      #go {{ min-width: 58px; padding-inline: 10px; min-height: 44px; }}
      .layout {{ grid-template-columns: 1fr; gap: 0; }}
      .sidebar {{ padding: 20px 0; border-right: 0; border-bottom: 1px solid var(--line); }}
      #folders {{ display: flex; flex-wrap: wrap; gap: 5px; }}
      #folders .folder {{ width: auto; max-width: 100%; border: 1px solid var(--line); }}
      #rootBtn {{ width: auto; }}
      .folder-create {{ max-width: 360px; margin-top: 12px; }}
      .products-section {{ margin-top: 18px; padding-top: 14px; }}
      .asset-grid {{ gap: 12px; }}
      .asset-info {{ padding: 10px; }}
      .asset-actions {{ padding: 0 8px 10px; }}
      .asset-actions select {{ flex-basis: 100%; order: 3; }}
      .actions button, .actions select {{ min-height: 40px; }}
      #uploadProduct {{ flex: 1; max-width: none; width: 50%; }}
      footer .debug {{ text-align: left; }}
    }}
    @keyframes hero-in {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes result-in {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes status-pulse {{ 50% {{ opacity: .25; }} }}
    @media (prefers-reduced-motion: reduce) {{ *, *::before {{ animation: none !important; }} }}
  </style>
</head>
<body>
  <a class="skip-link" href="#workspace">ライブラリへ移動</a>
  <header class="masthead shell">
    <a class="brand" href="/" aria-label="media-search ホーム"><span class="brand-mark" aria-hidden="true"></span>media-search</a>
    <span class="masthead-note">写真と映像の保管室</span>
  </header>
  <section class="hero shell" aria-labelledby="hero-title">
    <p class="eyebrow">記憶をたどる、素材に出会う。</p>
    <h1 id="hero-title">暗室アーカイブ</h1>
    <p>色、情景、思い浮かぶ言葉から。探していた一枚を、ここで。</p>
  </section>
  <div class="search-dock shell">
    <form id="searchForm" class="search-form" role="search">
      <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg>
      <label class="sr-only" for="q">意味・名前で探す</label>
      <input id="q" type="search" placeholder="意味・名前で探す…" required autocomplete="off" />
      <label class="sr-only" for="mediaType">素材の種類</label>
      <select id="mediaType"><option value="">すべて</option><option value="image">画像</option><option value="video">動画</option></select>
      <button id="go" type="submit">検索</button>
    </form>
  </div>
  <div class="status-line shell"><p id="status" role="status" aria-live="polite" aria-atomic="true">素材を読み込んでいます…</p></div>
  <div class="layout shell">
    <aside class="sidebar" aria-label="ライブラリの管理">
      <h2 class="section-label">フォルダ</h2>
      <nav aria-label="フォルダを選択">
        <button id="rootBtn" class="folder active" aria-current="page">ホーム</button>
        <button id="parentBtn" class="folder" hidden>ひとつ上のフォルダ</button>
        <div id="folders"></div>
      </nav>
      <form id="folderForm" class="folder-create">
        <label class="sr-only" for="newFolder">新しいフォルダ名</label>
        <input id="newFolder" placeholder="新しいフォルダ" required />
        <button id="addFolder" type="submit" aria-label="フォルダを作成">＋ 作成</button>
      </form>
      <details class="products-section">
        <summary>商品管理</summary>
        <p class="muted">素材に紐づける商品を登録・編集します。</p>
        <form id="productForm" class="product-form">
          <label class="sr-only" for="newProductId">商品コード（SKU）</label>
          <input id="newProductId" placeholder="商品コード（SKU）" required />
          <label class="sr-only" for="newProductName">商品名</label>
          <input id="newProductName" placeholder="商品名" required />
          <button id="addProduct" type="submit">商品を登録</button>
        </form>
        <div id="products"></div>
      </details>
    </aside>
    <main id="workspace" class="workspace" tabindex="-1">
      <nav class="view-switch" aria-label="表示の切り替え">
        <button id="libraryTab" aria-pressed="true" aria-controls="assets">ライブラリ</button>
        <button id="searchTab" aria-pressed="false" aria-controls="out">検索結果</button>
      </nav>
      <div class="collection-heading"><h2 id="crumb">ホーム</h2><span id="count" class="muted"></span></div>
      <div id="uploadToolbar" class="upload-toolbar" role="group" aria-label="現在のフォルダに素材を追加">
        <div class="file-picker"><label for="file">＋ 素材を選ぶ</label><input id="file" type="file" accept=".jpg,.jpeg,.png,.mp4" multiple aria-describedby="fileName" /></div>
        <span id="fileName" class="muted">JPG・PNG・MP4</span>
        <label class="sr-only" for="uploadProduct">紐づける商品（任意）</label>
        <select id="uploadProduct"><option value="">商品を紐づける（任意）</option></select>
        <button id="upload">アップロード</button>
      </div>
      <div id="assets" class="asset-grid" aria-label="ライブラリの素材"></div>
      <div id="out" class="asset-grid" aria-label="検索結果" hidden></div>
    </main>
  </div>
  <footer class="shell">
    <span>暗室アーカイブ <span aria-hidden="true">／</span> media-search</span>
    <div class="debug"><span class="mono">mode={escape(embedder_mode)} · {escape(embedder_id)}</span>{warn}</div>
  </footer>
  <script>
    let currentFolder = null;
    let folderCache = [];
    let productCache = [];
    let busy = false;
    let activeView = 'library';
    let assetCount = 0;
    let resultCount = null;
    let lastQuery = '';
    let assetRequest = 0;
    let searchRequest = 0;
    const foldersEl = document.getElementById('folders');
    const assetsEl = document.getElementById('assets');
    const productsEl = document.getElementById('products');
    const out = document.getElementById('out');
    const statusEl = document.getElementById('status');
    const crumb = document.getElementById('crumb');
    const uploadBtn = document.getElementById('upload');
    const uploadProduct = document.getElementById('uploadProduct');
    const fileInput = document.getElementById('file');
    const rootBtn = document.getElementById('rootBtn');
    const parentBtn = document.getElementById('parentBtn');

    // API names and IDs are data, including when used in HTML attributes.
    function esc(value) {{
      return String(value ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}}[c]));
    }}
    function setStatus(msg, kind = '') {{
      statusEl.textContent = msg;
      statusEl.className = kind;
    }}
    async function requestJson(url, options) {{
      const res = await fetch(url, options);
      if (!res.ok) {{
        let detail = '';
        try {{
          const body = await res.json();
          if (typeof body.detail === 'string') detail = body.detail;
        }} catch (_) {{ /* Non-JSON failures still report their HTTP status. */ }}
        throw new Error(`操作に失敗しました（${{res.status}}）${{detail ? '：' + detail : '。もう一度お試しください。'}}`);
      }}
      return res.status === 204 ? null : res.json();
    }}
    async function runAction(action) {{
      try {{ await action(); }}
      catch (error) {{
        setStatus(error instanceof TypeError ? '通信できませんでした。接続を確認して、もう一度お試しください。' : error.message, 'err');
      }}
    }}
    function emptyState(title, message) {{
      return `<div class="empty-state"><span class="empty-mark" aria-hidden="true"></span><h3>${{esc(title)}}</h3><p>${{esc(message)}}</p></div>`;
    }}
    function folderPath() {{
      const names = [];
      const visited = new Set();
      let id = currentFolder;
      while (id && !visited.has(id)) {{
        visited.add(id);
        const folder = folderCache.find(f => f.folder_id === id);
        if (!folder) break;
        names.unshift(folder.name);
        id = folder.parent_id;
      }}
      return ['ホーム', ...names].join(' / ');
    }}
    function setView(view) {{
      activeView = view;
      const library = view === 'library';
      assetsEl.hidden = !library;
      out.hidden = library;
      document.getElementById('uploadToolbar').hidden = !library;
      document.getElementById('libraryTab').setAttribute('aria-pressed', String(library));
      document.getElementById('searchTab').setAttribute('aria-pressed', String(!library));
      crumb.textContent = library ? folderPath() : (lastQuery ? `「${{lastQuery}}」の検索結果` : '検索結果');
      document.getElementById('count').textContent = library ? `${{assetCount}} 点` : (resultCount === null ? '' : `${{resultCount}} 件 · 関連度順`);
    }}
    function updateFileLabel() {{
      const files = Array.from(fileInput.files || []);
      document.getElementById('fileName').textContent = files.length === 1 ? files[0].name : (files.length ? `${{files.length}} 件を選択中` : 'JPG・PNG・MP4');
    }}
    async function pollJob(id) {{
      for (;;) {{
        const body = await requestJson('/api/import/jobs/' + encodeURIComponent(id));
        const progress = body.processed != null && body.total != null ? ` ${{body.processed}}/${{body.total}}` : '';
        const label = {{queued: '開始を待っています', running: '検索用データを作成中', succeeded: '完了しました', failed: '失敗しました'}}[body.status] || '処理中';
        setStatus(`取り込み：${{label}}${{progress}}` + (body.error ? ' — ' + body.error : ''),
          body.status === 'failed' ? 'err' : (body.status === 'succeeded' ? 'ok' : 'busy'));
        if (body.status === 'succeeded' || body.status === 'failed') {{
          await refreshAssets();
          return body;
        }}
        await new Promise(resolve => setTimeout(resolve, 800));
      }}
    }}
    async function loadAllFolders() {{
      const body = await requestJson('/api/library/folders?all=1');
      folderCache = body.folders || [];
    }}
    function folderOptionsHtml(selected) {{
      return '<option value="">ホーム</option>' + folderCache.map(f =>
        `<option value="${{esc(f.folder_id)}}" ${{f.folder_id === selected ? 'selected' : ''}}>${{esc(f.name)}}</option>`
      ).join('');
    }}
    async function refreshFolders() {{
      const folder = currentFolder;
      const params = new URLSearchParams();
      if (folder) params.set('parent_id', folder);
      const body = await requestJson('/api/library/folders?' + params.toString());
      if (folder !== currentFolder) return;
      rootBtn.classList.toggle('active', !folder);
      if (folder) rootBtn.removeAttribute('aria-current');
      else rootBtn.setAttribute('aria-current', 'page');
      parentBtn.hidden = !folder;
      foldersEl.innerHTML = (body.folders || []).map(f =>
        `<button class="folder" data-id="${{esc(f.folder_id)}}">${{esc(f.name)}}</button>`
      ).join('') || '<p class="muted">子フォルダはありません</p>';
      foldersEl.querySelectorAll('.folder').forEach(el => {{
        el.onclick = () => runAction(async () => {{ currentFolder = el.dataset.id; await refreshAll(); }});
      }});
    }}
    function assetCard(asset, index, search = false) {{
      const name = asset.display_name || asset.asset_id;
      const url = '/api/assets/' + encodeURI(asset.asset_id);
      const caption = (asset.media_type === 'video' ? '動画' : '画像') + (asset.product_id ? ' · SKU ' + asset.product_id : '');
      return `<article class="asset-card" style="--order:${{Math.min(index, 8)}}">
        <a class="thumbnail" href="${{esc(url)}}" tabindex="-1" aria-hidden="true"><img src="${{esc(asset.thumbnail_url)}}" alt="" loading="lazy" /></a>
        <div class="asset-info">
          <div class="asset-name"><a href="${{esc(url)}}" title="${{esc(name)}}">${{esc(name)}}</a></div>
          <p class="asset-caption">${{esc(caption)}}${{search ? ' · 関連度 ' + Number(asset.score).toFixed(4) : ''}}</p>
          <code class="asset-id" title="${{esc(asset.asset_id)}}">${{esc(asset.asset_id)}}</code>
        </div>
        ${{search ? '' : `<div class="actions asset-actions">
          <button data-ren="${{esc(asset.asset_id)}}" aria-label="${{esc(name)}}の名前を変更">名前変更</button>
          <select data-mov="${{esc(asset.asset_id)}}" aria-label="${{esc(name)}}の移動先" title="移動先のフォルダ">${{folderOptionsHtml(asset.folder_id || '')}}</select>
          <button class="danger" data-del="${{esc(asset.asset_id)}}" aria-label="${{esc(name)}}を削除">削除</button>
        </div>`}}
      </article>`;
    }}
    async function refreshAssets() {{
      const request = ++assetRequest;
      const params = new URLSearchParams({{folder_id: currentFolder || ''}});
      const body = await requestJson('/api/library/assets?' + params.toString());
      if (request !== assetRequest) return;
      const assets = body.assets || [];
      assetCount = assets.length;
      assetsEl.innerHTML = assets.map((a, i) => assetCard(a, i)).join('') ||
        emptyState('まだ、素材のない保管室。', '「素材を選ぶ」から写真や動画を追加してください。取り込みが完了すると、言葉で探せるようになります。');
      setView(activeView);
      assetsEl.querySelectorAll('[data-del]').forEach(btn => {{
        btn.onclick = () => runAction(async () => {{
          if (!confirm('この素材を削除しますか？この操作は取り消せません。')) return;
          setStatus('削除中…', 'busy');
          await requestJson('/api/library/assets/' + encodeURIComponent(btn.dataset.del), {{method: 'DELETE'}});
          setStatus('素材を削除しました', 'ok');
          await refreshAssets();
        }});
      }});
      assetsEl.querySelectorAll('[data-ren]').forEach(btn => {{
        btn.onclick = () => runAction(async () => {{
          const asset = assets.find(a => a.asset_id === btn.dataset.ren);
          const name = prompt('新しい素材名', asset.display_name || asset.asset_id);
          if (!name || !name.trim()) return;
          setStatus('名前を変更中…', 'busy');
          await requestJson('/api/library/assets/' + encodeURIComponent(btn.dataset.ren), {{
            method: 'PATCH', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{display_name: name}})
          }});
          setStatus('素材名を変更しました', 'ok');
          await refreshAssets();
        }});
      }});
      assetsEl.querySelectorAll('select[data-mov]').forEach(sel => {{
        sel.onchange = () => runAction(async () => {{
          const asset = assets.find(a => a.asset_id === sel.dataset.mov);
          setStatus('移動中…', 'busy');
          try {{
            await requestJson('/api/library/assets/' + encodeURIComponent(sel.dataset.mov), {{
              method: 'PATCH', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{folder_id: sel.value || null}})
            }});
          }} catch (error) {{ sel.value = asset.folder_id || ''; throw error; }}
          setStatus('素材を移動しました', 'ok');
          await refreshAssets();
        }});
      }});
    }}
    async function refreshProducts() {{
      const body = await requestJson('/api/library/products');
      productCache = body.products || [];
      const selected = uploadProduct.value;
      uploadProduct.innerHTML = '<option value="">商品を紐づける（任意）</option>' + productCache.map(p =>
        `<option value="${{esc(p.product_id)}}">${{esc(p.name)}} (${{esc(p.product_id)}})</option>`
      ).join('');
      uploadProduct.value = productCache.some(p => p.product_id === selected) ? selected : '';
      productsEl.innerHTML = productCache.map(p =>
        `<div class="product-row"><code>${{esc(p.product_id)}}</code><span>${{esc(p.name)}}</span>
          <div class="actions"><button data-pname="${{esc(p.product_id)}}" aria-label="${{esc(p.name)}}の商品名を変更">名前変更</button>
          <button class="danger" data-pdel="${{esc(p.product_id)}}" aria-label="${{esc(p.name)}}を削除">削除</button></div></div>`
      ).join('') || '<p class="muted">登録された商品はありません</p>';
      productsEl.querySelectorAll('[data-pname]').forEach(btn => {{
        btn.onclick = () => runAction(async () => {{
          const product = productCache.find(p => p.product_id === btn.dataset.pname);
          const name = prompt('新しい商品名', product.name);
          if (!name || !name.trim()) return;
          await requestJson('/api/library/products/' + encodeURIComponent(btn.dataset.pname), {{
            method: 'PATCH', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{name}})
          }});
          setStatus('商品名を更新しました', 'ok');
          await refreshProducts();
        }});
      }});
      productsEl.querySelectorAll('[data-pdel]').forEach(btn => {{
        btn.onclick = () => runAction(async () => {{
          if (!confirm('この商品を削除しますか？')) return;
          await requestJson('/api/library/products/' + encodeURIComponent(btn.dataset.pdel), {{method: 'DELETE'}});
          setStatus('商品を削除しました', 'ok');
          await refreshProducts();
        }});
      }});
    }}
    async function refreshAll() {{
      setView('library');
      await loadAllFolders();
      await refreshFolders();
      await refreshProducts();
      await refreshAssets();
    }}
    rootBtn.onclick = () => runAction(async () => {{ currentFolder = null; await refreshAll(); }});
    parentBtn.onclick = () => runAction(async () => {{
      currentFolder = folderCache.find(f => f.folder_id === currentFolder)?.parent_id || null;
      await refreshAll();
    }});
    document.getElementById('libraryTab').onclick = () => setView('library');
    document.getElementById('searchTab').onclick = () => setView('search');
    fileInput.onchange = updateFileLabel;
    document.getElementById('folderForm').onsubmit = event => {{
      event.preventDefault();
      runAction(async () => {{
        const input = document.getElementById('newFolder');
        const name = input.value.trim();
        if (!name) return;
        await requestJson('/api/library/folders', {{
          method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{name, parent_id: currentFolder}})
        }});
        input.value = '';
        setStatus('フォルダを作成しました', 'ok');
        await loadAllFolders();
        await refreshFolders();
        await refreshAssets();
      }});
    }};
    document.getElementById('productForm').onsubmit = event => {{
      event.preventDefault();
      runAction(async () => {{
        const product_id = document.getElementById('newProductId').value.trim();
        const name = document.getElementById('newProductName').value.trim();
        if (!product_id || !name) {{ setStatus('商品コードと商品名を入力してください', 'err'); return; }}
        await requestJson('/api/library/products', {{
          method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify({{product_id, name}})
        }});
        document.getElementById('newProductId').value = '';
        document.getElementById('newProductName').value = '';
        setStatus('商品を追加しました', 'ok');
        await refreshProducts();
      }});
    }};
    uploadBtn.onclick = () => runAction(async () => {{
      const files = Array.from(fileInput.files || []);
      if (!files.length) {{ setStatus('アップロードするファイルを選んでください', 'err'); fileInput.focus(); return; }}
      if (busy) return;
      busy = true;
      uploadBtn.disabled = true;
      fileInput.disabled = true;
      uploadProduct.disabled = true;
      try {{
        setStatus(`アップロード中 0/${{files.length}}…`, 'busy');
        const fd = new FormData();
        files.forEach(f => fd.append('files', f));
        if (currentFolder) fd.append('folder_id', currentFolder);
        if (uploadProduct.value) fd.append('product_id', uploadProduct.value);
        const body = await requestJson('/api/library/upload', {{method: 'POST', body: fd}});
        const n = (body.assets || []).length || (body.asset ? 1 : 0);
        setStatus(`${{n}} 件アップロード完了。検索用データを作成します…`, 'busy');
        fileInput.value = '';
        updateFileLabel();
        await refreshAssets();
        if (body.job && body.job.job_id) await pollJob(body.job.job_id);
        else setStatus(`${{n}} 件アップロード完了`, 'ok');
      }} finally {{
        busy = false;
        uploadBtn.disabled = false;
        fileInput.disabled = false;
        uploadProduct.disabled = false;
      }}
    }});
    document.getElementById('searchForm').onsubmit = event => {{
      event.preventDefault();
      runAction(async () => {{
        const q = document.getElementById('q').value.trim();
        if (!q) return;
        const request = ++searchRequest;
        const mediaType = document.getElementById('mediaType').value;
        const params = new URLSearchParams({{q}});
        if (mediaType) params.set('media_type', mediaType);
        lastQuery = q;
        resultCount = null;
        out.innerHTML = emptyState('素材を探しています…', '言葉に近い写真や動画を探しています。');
        setView('search');
        setStatus('検索中…', 'busy');
        out.setAttribute('aria-busy', 'true');
        try {{
          const body = await requestJson('/api/search?' + params.toString());
          if (request !== searchRequest) return;
          const hits = body.results || [];
          resultCount = hits.length;
          out.innerHTML = hits.map((r, i) => assetCard(r, i, true)).join('') ||
            emptyState('見つかりませんでした。', '別の言葉で探すか、素材の種類を「すべて」にしてお試しください。');
          setView(activeView);
          setStatus(`検索結果 ${{hits.length}} 件`, 'ok');
        }} catch (error) {{
          if (request !== searchRequest) return;
          out.innerHTML = emptyState('検索できませんでした。', '接続や検索条件を確認して、もう一度検索してください。');
          throw error;
        }} finally {{
          if (request === searchRequest) out.removeAttribute('aria-busy');
        }}
      }});
    }};
    out.innerHTML = emptyState('探していた一枚に、もう一度。', '上の検索欄に情景や名前を入力すると、ここに検索結果が並びます。');
    runAction(async () => {{
      await refreshAll();
      if (!statusEl.className) setStatus('素材を選ぶか、言葉で検索してください');
    }});
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
    on_db_reload: Callable[[], None] | None = None,
    embedder_mode: str = "unknown",
    embedder_id: str = "unknown",
) -> FastAPI:
    storage = media_storage
    if storage is None and media_root is not None:
        storage = LocalMediaStorage(media_root)

    if frame_store is None and frame_root is not None:
        from media_search.adapters.local_frame_store import LocalFrameStore

        frame_store = LocalFrameStore(frame_root)

    reloaded_jobs: set[str] = set()

    def _maybe_reload_db(job) -> None:
        if on_db_reload is None or job is None:
            return
        status = job.status
        if isinstance(status, ImportJobStatus):
            ok = status == ImportJobStatus.SUCCEEDED
        else:
            ok = str(status) == ImportJobStatus.SUCCEEDED.value
        if ok and job.job_id not in reloaded_jobs:
            on_db_reload()
            reloaded_jobs.add(job.job_id)

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
        _maybe_reload_db(job)
        return _job_out(job)

    @app.get("/api/import/status", response_model=ImportJobOut)
    def api_import_status() -> ImportJobOut:
        if import_jobs is None:
            raise HTTPException(status_code=501, detail="import jobs not configured")
        job = import_jobs.latest()
        if job is None:
            raise HTTPException(status_code=404, detail="no import jobs")
        _maybe_reload_db(job)
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
