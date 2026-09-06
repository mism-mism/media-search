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
  <meta name="theme-color" content="#f4f5f7" />
  <title>メディアライブラリ — media-search</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+JP:wght@400;500;600&family=Fraunces:wght@500;600&display=swap" rel="stylesheet" />
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f5f7; --surface: #ffffff; --text: #1a1d21; --muted: #5c6570;
      --line: #e2e5ea; --accent: #126b5f; --accent-soft: #e6f3f0; --warn: #9a6700; --danger: #b42318;
      font-family: 'IBM Plex Sans JP', sans-serif; color: var(--text); background: var(--bg);
    }}
    * {{ box-sizing: border-box; }}
    [hidden] {{ display: none !important; }}
    body {{ margin: 0; min-width: 320px; }}
    button, input, select {{ font: inherit; font-size: .875rem; border-radius: 6px; }}
    button, select {{ cursor: pointer; }}
    button {{ min-height: 40px; padding: .55rem .85rem; color: var(--text); border: 1px solid var(--line); background: var(--surface); }}
    button:hover {{ border-color: var(--muted); background: var(--bg); }}
    button:disabled, input:disabled, select:disabled {{ cursor: wait; opacity: .55; }}
    button.primary {{ background: var(--accent); color: white; border-color: var(--accent); font-weight: 500; }}
    button.primary:hover {{ background: #0d574d; }}
    input, select {{ min-width: 0; min-height: 42px; padding: .6rem .75rem; color: var(--text); background: var(--surface); border: 1px solid var(--line); }}
    input::placeholder {{ color: var(--muted); opacity: 1; }}
    :focus-visible {{ outline: 2px solid var(--accent); outline-offset: 3px; }}
    a {{ color: inherit; text-decoration: none; }}
    a:hover {{ text-decoration: underline; text-underline-offset: 4px; }}
    h1, h2, p {{ margin: 0; }}
    h1 {{ font-size: 1.45rem; font-weight: 600; letter-spacing: .025em; }}
    h2 {{ font-size: 1.15rem; font-weight: 600; overflow-wrap: anywhere; }}
    .muted {{ color: var(--muted); font-size: .8rem; line-height: 1.8; }}
    .sr-only {{ position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; border: 0; }}
    .skip-link {{ position: fixed; top: -80px; left: 16px; z-index: 30; padding: 12px; background: var(--surface); }}
    .skip-link:focus {{ top: 12px; }}
    .shell {{ width: min(1600px, calc(100% - 64px)); margin-inline: auto; }}
    .header {{ position: sticky; top: 0; z-index: 20; background: var(--surface); border-bottom: 1px solid var(--line); }}
    .masthead {{ display: flex; align-items: center; justify-content: space-between; gap: 40px; min-height: 86px; padding-block: 16px; }}
    .brand {{ display: inline-flex; align-items: center; gap: 12px; flex-shrink: 0; font: 600 1.45rem 'Fraunces', 'IBM Plex Sans JP', serif; letter-spacing: -.045em; }}
    .brand-mark {{ display: grid; place-items: center; width: 34px; height: 34px; border-radius: 8px; background: var(--accent-soft); color: var(--accent); }}
    .brand-mark svg {{ width: 23px; height: 23px; }}
    .search-form {{ display: flex; flex: 0 1 740px; align-items: center; gap: 10px; padding: 5px 6px 5px 16px; background: var(--bg); border: 1px solid var(--line); border-radius: 8px; }}
    .search-form:focus-within {{ border-color: var(--accent); }}
    .search-icon {{ width: 19px; height: 19px; flex-shrink: 0; color: var(--muted); }}
    #q {{ flex: 1; width: 100%; border: 0; padding: 7px 0; background: transparent; }}
    #mediaType {{ max-width: 115px; min-height: 36px; border: 0; border-left: 1px solid var(--line); border-radius: 0; background: transparent; padding-inline: 10px; font-size: .8rem; }}
    #go {{ min-width: 72px; }}
    .page-heading {{ padding-block: 30px 23px; }}
    .page-heading p {{ margin-top: 7px; }}
    .view-bar {{ display: flex; align-items: center; justify-content: space-between; gap: 24px; border-bottom: 1px solid var(--line); }}
    .view-switch {{ display: flex; gap: 28px; }}
    .view-switch button {{ position: relative; border: 0; border-radius: 0; padding: 13px 2px 16px; font-weight: 500; color: var(--muted); background: transparent; }}
    .view-switch button[aria-selected="true"] {{ color: var(--accent); }}
    .view-switch button[aria-selected="true"]::after {{ content: ''; position: absolute; bottom: -1px; left: 0; right: 0; height: 3px; background: var(--accent); border-radius: 2px 2px 0 0; }}
    .status-line {{ display: flex; align-items: baseline; gap: 8px; min-width: 0; font-size: .75rem; color: var(--muted); }}
    .status-line > span {{ white-space: nowrap; }}
    #status {{ overflow-wrap: anywhere; }}
    #status.ok {{ color: var(--accent); }}
    #status.err {{ color: var(--danger); }}
    #status.busy {{ color: var(--warn); }}
    .import-banner {{ display: flex; align-items: center; gap: 14px; padding: 16px 20px; margin-top: 20px; border: 1px solid #e8d8b2; border-radius: 8px; color: var(--warn); background: #fff8e8; }}
    .import-banner.ok {{ color: var(--accent); background: var(--accent-soft); border-color: #badbd3; }}
    .import-banner.err {{ color: var(--danger); background: #fff0ee; border-color: #f0c8c3; }}
    .import-dot {{ width: 8px; height: 8px; border-radius: 50%; background: currentColor; flex-shrink: 0; }}
    .import-banner.busy .import-dot {{ animation: status-pulse 1.4s ease-in-out infinite; }}
    .import-copy {{ flex: 1; min-width: 0; }}
    .import-copy strong {{ display: block; font-size: .85rem; font-weight: 500; }}
    #importStatus {{ margin-top: 3px; font-size: .8rem; overflow-wrap: anywhere; }}
    #dismissImport {{ color: inherit; background: transparent; border-color: currentColor; }}
    .view-panel {{ animation: view-in .16s ease-out; }}
    .library-layout {{ display: grid; grid-template-columns: 228px minmax(0, 1fr); min-height: 520px; }}
    .sidebar {{ padding: 28px 20px 32px 0; border-right: 1px solid var(--line); min-width: 0; }}
    .section-label {{ font-size: .8rem; font-weight: 600; margin-bottom: 16px; }}
    .folder {{ display: flex; width: 100%; align-items: center; text-align: left; gap: 10px; border: 0; padding: 10px 12px; margin-bottom: 4px; background: transparent; overflow-wrap: anywhere; }}
    .folder::before {{ content: ''; width: 15px; height: 12px; border: 1.5px solid currentColor; border-radius: 2px; flex-shrink: 0; }}
    .folder.active {{ color: var(--accent); background: var(--accent-soft); font-weight: 500; }}
    #folders {{ margin-top: 5px; }}
    #folders > p {{ padding: 10px 12px; }}
    .folder-create {{ display: grid; gap: 8px; padding-top: 20px; margin-top: 20px; border-top: 1px solid var(--line); }}
    .folder-create label {{ font-size: .75rem; color: var(--muted); }}
    .folder-create input {{ width: 100%; }}
    .folder-create button {{ text-align: left; color: var(--accent); }}
    .workspace {{ min-width: 0; padding: 28px 0 40px 28px; }}
    .collection-heading {{ display: flex; align-items: baseline; justify-content: space-between; gap: 16px; margin-bottom: 20px; }}
    .collection-heading > div {{ min-width: 0; }}
    #crumb {{ font-size: .95rem; font-weight: 500; line-height: 1.6; overflow-wrap: anywhere; }}
    .count {{ white-space: nowrap; font-variant-numeric: tabular-nums; }}
    .upload-toolbar {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px; padding: 16px; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; }}
    #upload {{ display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 44px; }}
    #upload svg {{ width: 18px; height: 18px; }}
    .file-picker {{ position: relative; flex-shrink: 0; }}
    .file-picker input {{ position: absolute; inset: 0; opacity: 0; width: 100%; cursor: pointer; }}
    .file-picker label {{ display: block; border: 1px solid var(--line); border-radius: 6px; padding: 11px 12px; font-size: .8rem; }}
    .file-picker:hover label {{ border-color: var(--muted); }}
    .file-picker:focus-within {{ outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 6px; }}
    #fileName {{ flex: 1 1 110px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    #uploadProduct {{ max-width: 215px; }}
    .upload-hint {{ margin: 9px 0 24px; font-size: .75rem; }}
    .asset-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px; }}
    .asset-card {{ position: relative; min-width: 0; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 1px 2px rgb(0 0 0 / 6%); }}
    .asset-card:focus-within {{ border-color: var(--accent); }}
    .thumbnail {{ display: block; aspect-ratio: 1 / 1; background: #edf0f2; border-bottom: 1px solid var(--line); border-radius: 7px 7px 0 0; overflow: hidden; }}
    .thumbnail img {{ display: block; width: 100%; height: 100%; object-fit: contain; color: var(--muted); font-size: .8rem; }}
    .asset-info {{ padding: 14px; }}
    .asset-name {{ font-size: .85rem; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .asset-caption {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px; margin-top: 8px; font-size: .7rem; color: var(--muted); line-height: 1.7; overflow-wrap: anywhere; }}
    .type-badge {{ padding: 1px 6px; border-radius: 4px; background: var(--bg); }}
    .card-menu {{ position: absolute; right: 9px; top: 9px; }}
    .card-menu[open] {{ z-index: 5; }}
    .card-menu summary {{ display: grid; place-items: center; width: 34px; height: 34px; border: 1px solid var(--line); border-radius: 6px; background: var(--surface); cursor: pointer; list-style: none; font-size: 1.4rem; line-height: 1; }}
    .card-menu summary::-webkit-details-marker {{ display: none; }}
    .card-menu summary:hover {{ border-color: var(--accent); color: var(--accent); }}
    .menu-content {{ position: absolute; right: 0; top: 40px; width: 190px; display: grid; gap: 5px; padding: 8px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }}
    .menu-content button {{ text-align: left; border: 0; }}
    .menu-content label {{ color: var(--muted); font-size: .75rem; padding: 7px 8px 0; }}
    .menu-content select {{ width: 100%; font-size: .8rem; }}
    .menu-content .danger {{ color: var(--danger); border-top: 1px solid var(--line); border-radius: 0; margin-top: 3px; }}
    .empty-state {{ grid-column: 1 / -1; display: grid; justify-items: center; align-content: center; min-height: 300px; padding: 36px 24px; border: 1px dashed #c9d0d8; border-radius: 8px; text-align: center; }}
    .empty-mark {{ display: grid; place-items: center; width: 56px; height: 56px; border-radius: 12px; color: var(--accent); background: var(--accent-soft); margin-bottom: 20px; }}
    .empty-mark svg {{ width: 28px; height: 28px; }}
    .empty-state h3 {{ margin: 0 0 10px; font-size: 1.05rem; font-weight: 500; }}
    .empty-state p {{ color: var(--muted); font-size: .8rem; line-height: 1.9; max-width: 440px; }}
    .empty-state button {{ margin-top: 20px; }}
    .standalone-panel {{ padding-block: 28px 40px; min-height: 520px; }}
    .standalone-panel .collection-heading p {{ margin-top: 7px; }}
    .product-form {{ display: flex; align-items: end; flex-wrap: wrap; gap: 16px; padding: 24px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); margin-bottom: 24px; }}
    .product-field {{ display: grid; gap: 8px; flex: 1 1 220px; }}
    .product-field label {{ font-size: .8rem; font-weight: 500; }}
    .product-field input {{ width: 100%; }}
    #addProduct {{ min-height: 43px; }}
    .product-list {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }}
    .product-row {{ position: relative; min-width: 0; padding: 22px 54px 22px 20px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); box-shadow: 0 1px 2px rgb(0 0 0 / 6%); overflow-wrap: anywhere; }}
    .product-row .product-name {{ display: block; font-size: .95rem; font-weight: 500; }}
    .product-row .product-code {{ display: block; color: var(--muted); font-size: .75rem; margin-top: 8px; }}
    footer {{ border-top: 1px solid var(--line); padding-block: 22px 28px; display: flex; flex-wrap: wrap; justify-content: space-between; gap: 12px; color: var(--muted); font-size: .7rem; }}
    footer .debug {{ text-align: right; max-width: 100%; overflow-wrap: anywhere; }}
    footer .mono {{ font-family: ui-monospace, monospace; }}
    footer p {{ margin-top: 4px; }}
    @media (max-width: 1250px) {{ .asset-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}
    @media (max-width: 1000px) {{
      .shell {{ width: calc(100% - 40px); }}
      .masthead {{ gap: 24px; }}
      .library-layout {{ grid-template-columns: 190px minmax(0, 1fr); }}
      .sidebar {{ padding-right: 16px; }}
      .workspace {{ padding-left: 20px; }}
      .asset-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }}
      .product-list {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 720px) {{
      .shell {{ width: calc(100% - 32px); }}
      .masthead {{ flex-wrap: wrap; gap: 12px; padding-block: 12px; }}
      .brand {{ font-size: 1.25rem; }}
      .brand-mark {{ width: 29px; height: 29px; }}
      .search-form {{ flex-basis: 100%; gap: 6px; padding-left: 10px; }}
      .search-icon {{ display: none; }}
      #q, input, select {{ font-size: 16px; }}
      #mediaType {{ width: 78px; padding-inline: 5px; font-size: .75rem; }}
      #go {{ min-width: 54px; padding-inline: 10px; }}
      .page-heading {{ padding-block: 24px 16px; }}
      h1 {{ font-size: 1.25rem; }}
      .view-bar {{ flex-wrap: wrap; gap: 0; }}
      .view-switch {{ width: 100%; gap: 26px; }}
      .status-line {{ padding-block: 12px; }}
      .library-layout {{ grid-template-columns: 1fr; }}
      .sidebar {{ padding: 20px 0; border-right: 0; border-bottom: 1px solid var(--line); }}
      .section-label {{ margin-bottom: 10px; }}
      .folder-nav, #folders {{ display: flex; flex-wrap: wrap; gap: 5px; }}
      #folders {{ margin: 0; }}
      .folder {{ width: auto; max-width: 100%; margin: 0; }}
      #folders > p {{ padding: 8px; }}
      .folder-create {{ grid-template-columns: minmax(0, 1fr) auto; gap: 8px; margin-top: 14px; padding-top: 14px; }}
      .folder-create label {{ grid-column: 1 / -1; }}
      .workspace {{ padding: 22px 0 32px; }}
      .upload-toolbar {{ padding: 12px; gap: 10px; }}
      #upload {{ flex: 1; }}
      #uploadProduct {{ max-width: none; width: 50%; flex: 1; font-size: .8rem; }}
      #fileName {{ flex-basis: 140px; }}
      .asset-grid {{ gap: 12px; }}
      .asset-info {{ padding: 11px; }}
      .asset-name {{ font-size: .8rem; }}
      .card-menu {{ right: 6px; top: 6px; }}
      .card-menu summary {{ width: 40px; height: 40px; }}
      .menu-content {{ top: 44px; width: min(190px, 42vw); }}
      .menu-content button, .menu-content select {{ min-height: 44px; }}
      .product-form {{ padding: 16px; }}
      .product-list {{ grid-template-columns: 1fr; }}
      .import-banner {{ padding: 14px; flex-wrap: wrap; }}
      footer .debug {{ text-align: left; }}
    }}
    @keyframes view-in {{ from {{ opacity: .5; }} to {{ opacity: 1; }} }}
    @keyframes status-pulse {{ 50% {{ opacity: .25; }} }}
    @media (prefers-reduced-motion: reduce) {{ *, *::before {{ animation: none !important; }} }}
  </style>
</head>
<body>
  <a class="skip-link" href="#workspace">メイン画面へ移動</a>
  <header class="header">
    <div class="masthead shell">
      <a class="brand" href="/" aria-label="media-search ホーム"><span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="9" r="2"/><path d="m3 18 5-5 4 4 4-6 5 7"/></svg></span>media-search</a>
      <form id="searchForm" class="search-form" role="search">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg>
        <label class="sr-only" for="q">キーワード・意味で検索</label>
        <input id="q" type="search" placeholder="キーワード・意味で検索…" required autocomplete="off" />
        <label class="sr-only" for="mediaType">素材の種類</label>
        <select id="mediaType"><option value="">すべて</option><option value="image">画像</option><option value="video">動画</option></select>
        <button id="go" class="primary" type="submit">検索</button>
      </form>
    </div>
  </header>
  <main id="workspace" class="shell" tabindex="-1">
    <div class="page-heading"><h1>メディアライブラリ</h1><p class="muted">画像・動画をまとめて管理。フォルダで整理し、言葉で検索。</p></div>
    <div class="view-bar">
      <nav class="view-switch" role="tablist" aria-label="表示の切り替え">
        <button id="libraryTab" role="tab" aria-selected="true" aria-controls="libraryPanel">ライブラリ</button>
        <button id="searchTab" role="tab" aria-selected="false" aria-controls="searchPanel" tabindex="-1">検索結果</button>
        <button id="productsTab" role="tab" aria-selected="false" aria-controls="productsPanel" tabindex="-1">商品</button>
      </nav>
      <div class="status-line"><span>状態:</span><p id="status" role="status" aria-live="polite" aria-atomic="true">読み込み中…</p></div>
    </div>
    <section id="importBanner" class="import-banner" role="status" aria-live="polite" aria-atomic="true" aria-label="取り込み状況" hidden>
      <span class="import-dot" aria-hidden="true"></span><div class="import-copy"><strong>ファイルの取り込み</strong><p id="importStatus"></p></div>
      <button id="dismissImport" type="button" hidden>閉じる</button>
    </section>
    <section id="libraryPanel" class="view-panel library-layout" role="tabpanel" aria-labelledby="libraryTab">
      <aside class="sidebar" aria-label="フォルダの管理">
        <h2 class="section-label">フォルダ</h2>
        <nav class="folder-nav" aria-label="フォルダを選択">
          <button id="rootBtn" class="folder active" aria-current="page">ライブラリ直下</button>
          <button id="parentBtn" class="folder" hidden>ひとつ上へ</button>
          <div id="folders"></div>
        </nav>
        <form id="folderForm" class="folder-create">
          <label for="newFolder">現在の場所にフォルダを作成</label>
          <input id="newFolder" placeholder="新しいフォルダ名" required />
          <button id="addFolder" type="submit">＋ 新規フォルダ</button>
        </form>
      </aside>
      <div class="workspace">
        <div class="collection-heading"><h2 id="crumb">ライブラリ / 直下</h2><span id="count" class="muted count"></span></div>
        <div id="uploadToolbar" class="upload-toolbar" role="group" aria-label="現在のフォルダに素材を追加">
          <button id="upload" class="primary"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6"/></svg>アップロード</button>
          <label class="sr-only" for="uploadProduct">紐づける商品（任意）</label>
          <select id="uploadProduct"><option value="">商品を選ぶ（任意）</option></select>
          <div class="file-picker"><label for="file">ファイルを選択</label><input id="file" type="file" accept=".jpg,.jpeg,.png,.mp4" multiple aria-describedby="fileName uploadHint" /></div>
          <span id="fileName" class="muted">未選択</span>
        </div>
        <p id="uploadHint" class="muted upload-hint">JPG・PNG・MP4 ／ 複数選択できます。商品を紐づけて、現在のフォルダにアップロード。</p>
        <div id="assets" class="asset-grid" aria-label="ライブラリの素材" aria-busy="true"></div>
      </div>
    </section>
    <section id="searchPanel" class="view-panel standalone-panel" role="tabpanel" aria-labelledby="searchTab" hidden>
      <div class="collection-heading"><div><h2 id="searchHeading">検索結果</h2><p class="muted">ライブラリ全体から、入力した言葉に近い素材を表示します。</p></div><span id="searchCount" class="muted count"></span></div>
      <div id="out" class="asset-grid" aria-label="検索結果"></div>
    </section>
    <section id="productsPanel" class="view-panel standalone-panel" role="tabpanel" aria-labelledby="productsTab" hidden>
      <div class="collection-heading"><div><h2>商品</h2><p class="muted">素材に紐づける商品を管理します。登録した商品はアップロード時に選べます。</p></div><span id="productCount" class="muted count"></span></div>
      <form id="productForm" class="product-form">
        <div class="product-field"><label for="newProductId">商品コード（SKU）</label><input id="newProductId" placeholder="例：BAG-001" required /></div>
        <div class="product-field"><label for="newProductName">商品名</label><input id="newProductName" placeholder="例：キャンバストート" required /></div>
        <button id="addProduct" class="primary" type="submit">＋ 商品を登録</button>
      </form>
      <div id="products" class="product-list" aria-label="登録済みの商品"></div>
    </section>
  </main>
  <footer class="shell">
    <span>media-search <span aria-hidden="true">／</span> メディアライブラリ</span>
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
    const views = ['library', 'search', 'products'];

    // API names and IDs are data, including when used in HTML attributes.
    function esc(value) {{
      return String(value ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}}[c]));
    }}
    function setStatus(msg, kind = '') {{
      statusEl.textContent = msg;
      statusEl.className = kind;
    }}
    function setImportStatus(msg, kind) {{
      const banner = document.getElementById('importBanner');
      banner.hidden = false;
      banner.className = 'import-banner ' + kind;
      document.getElementById('importStatus').textContent = msg;
      document.getElementById('dismissImport').hidden = kind === 'busy';
      setStatus(kind === 'busy' ? '取り込み中' : (kind === 'err' ? '取り込みに失敗' : '取り込み完了'), kind);
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
    function emptyState(title, message, action = '', label = '') {{
      return `<div class="empty-state"><span class="empty-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="9" r="2"/><path d="m3 18 5-5 4 4 4-6 5 7"/></svg></span><h3>${{esc(title)}}</h3><p>${{esc(message)}}</p>${{action ? `<button class="primary" data-empty-action="${{esc(action)}}">${{esc(label)}}</button>` : ''}}</div>`;
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
      return ['ライブラリ', ...(names.length ? names : ['直下'])].join(' / ');
    }}
    function setView(view) {{
      activeView = view;
      views.forEach(name => {{
        const selected = name === view;
        document.getElementById(name + 'Panel').hidden = !selected;
        const tab = document.getElementById(name + 'Tab');
        tab.setAttribute('aria-selected', String(selected));
        tab.tabIndex = selected ? 0 : -1;
      }});
      crumb.textContent = folderPath();
      document.getElementById('count').textContent = `${{assetCount}} 点`;
      document.getElementById('searchHeading').textContent = lastQuery ? `「${{lastQuery}}」の検索結果` : '検索結果';
      document.getElementById('searchCount').textContent = resultCount === null ? '' : `${{resultCount}} 件 · 関連度順`;
      document.getElementById('productCount').textContent = `${{productCache.length}} 件`;
    }}
    function updateFileLabel() {{
      const files = Array.from(fileInput.files || []);
      document.getElementById('fileName').textContent = files.length === 1 ? files[0].name : (files.length ? `${{files.length}} 件を選択中` : '未選択');
    }}
    async function pollJob(id) {{
      for (;;) {{
        const body = await requestJson('/api/import/jobs/' + encodeURIComponent(id));
        const progress = body.processed != null && body.total != null ? ` ${{body.processed}}/${{body.total}}` : '';
        const label = {{queued: '開始を待っています', running: '検索用データを作成中', succeeded: '完了しました', failed: '失敗しました'}}[body.status] || '処理中';
        setImportStatus(`取り込み：${{label}}${{progress}}` + (body.error ? ' — ' + body.error : ''),
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
      return '<option value="">ライブラリ直下</option>' + folderCache.map(f =>
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
      ).join('') || '<p class="muted">フォルダを作成して素材を整理できます。</p>';
      foldersEl.querySelectorAll('.folder').forEach(el => {{
        el.onclick = () => runAction(async () => {{ currentFolder = el.dataset.id; await refreshAll(); }});
      }});
    }}
    function assetCard(asset, search = false) {{
      const name = asset.display_name || asset.asset_id;
      const url = '/api/assets/' + encodeURIComponent(asset.asset_id);
      const product = productCache.find(p => p.product_id === asset.product_id);
      const productLabel = product ? product.name : asset.product_id;
      return `<article class="asset-card">
        <a class="thumbnail" href="${{esc(url)}}" tabindex="-1" aria-hidden="true"><img src="${{esc(asset.thumbnail_url)}}" alt="" loading="lazy" /></a>
        <div class="asset-info">
          <div class="asset-name"><a href="${{esc(url)}}" title="${{esc(name)}}">${{esc(name)}}</a></div>
          <p class="asset-caption"><span class="type-badge">${{asset.media_type === 'video' ? '動画' : '画像'}}</span>${{asset.product_id ? `<span data-product-caption="${{esc(asset.product_id)}}">${{esc(productLabel)}}</span>` : ''}}${{search ? '<span>関連度 ' + Number(asset.score).toFixed(4) + '</span>' : ''}}</p>
        </div>
        ${{search ? '' : `<details class="card-menu"><summary aria-label="${{esc(name)}}の操作">⋯</summary><div class="menu-content">
          <button data-ren="${{esc(asset.asset_id)}}" aria-label="${{esc(name)}}の名前を変更">名前変更</button>
          <label>フォルダへ移動<select data-mov="${{esc(asset.asset_id)}}" aria-label="${{esc(name)}}の移動先">${{folderOptionsHtml(asset.folder_id || '')}}</select></label>
          <button class="danger" data-del="${{esc(asset.asset_id)}}" aria-label="${{esc(name)}}を削除">削除</button>
        </div></details>`}}
      </article>`;
    }}
    async function refreshAssets() {{
      const request = ++assetRequest;
      const params = new URLSearchParams({{folder_id: currentFolder || ''}});
      const body = await requestJson('/api/library/assets?' + params.toString());
      if (request !== assetRequest) return;
      const assets = body.assets || [];
      assetCount = assets.length;
      assetsEl.innerHTML = assets.map(a => assetCard(a)).join('') ||
        emptyState('まだ画像がありません', 'ファイルを選択して「アップロード」を押してください。取り込みが完了すると、画像や動画を言葉で検索できます。', 'upload', '＋ ファイルを選んで追加');
      assetsEl.removeAttribute('aria-busy');
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
      document.querySelectorAll('[data-product-caption]').forEach(caption => {{
        const id = caption.dataset.productCaption;
        caption.textContent = productCache.find(p => p.product_id === id)?.name || id;
      }});
      const selected = uploadProduct.value;
      uploadProduct.innerHTML = '<option value="">商品を選ぶ（任意）</option>' + productCache.map(p =>
        `<option value="${{esc(p.product_id)}}">${{esc(p.name)}} (${{esc(p.product_id)}})</option>`
      ).join('');
      uploadProduct.value = productCache.some(p => p.product_id === selected) ? selected : '';
      productsEl.innerHTML = productCache.map(p =>
        `<article class="product-row"><span class="product-name">${{esc(p.name)}}</span><span class="product-code">商品コード：${{esc(p.product_id)}}</span>
          <details class="card-menu"><summary aria-label="${{esc(p.name)}}の商品操作">⋯</summary><div class="menu-content"><button data-pname="${{esc(p.product_id)}}" aria-label="${{esc(p.name)}}の商品名を変更">名前変更</button>
          <button class="danger" data-pdel="${{esc(p.product_id)}}" aria-label="${{esc(p.name)}}を削除">削除</button></div></details></article>`
      ).join('') || emptyState('商品がまだ登録されていません', '商品コードと商品名を登録しましょう。ライブラリでアップロードする際に、素材と紐づけられます。', 'product', '最初の商品を登録');
      setView(activeView);
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
    views.forEach((view, index) => {{
      const tab = document.getElementById(view + 'Tab');
      tab.onclick = () => setView(view);
      tab.onkeydown = event => {{
        let next;
        if (event.key === 'ArrowRight') next = (index + 1) % views.length;
        else if (event.key === 'ArrowLeft') next = (index + views.length - 1) % views.length;
        else if (event.key === 'Home') next = 0;
        else if (event.key === 'End') next = views.length - 1;
        else return;
        event.preventDefault();
        setView(views[next]);
        document.getElementById(views[next] + 'Tab').focus();
      }};
    }});
    document.getElementById('dismissImport').onclick = () => {{ document.getElementById('importBanner').hidden = true; }};
    document.addEventListener('click', event => {{
      document.querySelectorAll('.card-menu[open]').forEach(menu => {{
        if (!menu.contains(event.target)) menu.open = false;
      }});
      const action = event.target.closest('[data-empty-action]')?.dataset.emptyAction;
      if (action === 'upload') {{
        setView('library');
        if (!busy) {{ fileInput.focus(); fileInput.click(); }}
      }} else if (action === 'search') document.getElementById('q').focus();
      else if (action === 'product') document.getElementById('newProductId').focus();
    }});
    document.addEventListener('keydown', event => {{
      if (event.key !== 'Escape') return;
      document.querySelectorAll('.card-menu[open]').forEach(menu => {{
        if (menu.contains(document.activeElement)) menu.querySelector('summary').focus();
        menu.open = false;
      }});
    }});
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
        setImportStatus(`${{files.length}} 件のファイルをアップロード中…`, 'busy');
        const fd = new FormData();
        files.forEach(f => fd.append('files', f));
        if (currentFolder) fd.append('folder_id', currentFolder);
        if (uploadProduct.value) fd.append('product_id', uploadProduct.value);
        const body = await requestJson('/api/library/upload', {{method: 'POST', body: fd}});
        const n = (body.assets || []).length || (body.asset ? 1 : 0);
        setImportStatus(`${{n}} 件アップロード完了。検索用データを作成します…`, 'busy');
        fileInput.value = '';
        updateFileLabel();
        await refreshAssets();
        if (body.job && body.job.job_id) await pollJob(body.job.job_id);
        else setImportStatus(`${{n}} 件アップロード完了`, 'ok');
      }} catch (error) {{
        setImportStatus(error instanceof TypeError ? '通信できませんでした。接続を確認して再度お試しください。' : error.message, 'err');
        throw error;
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
          out.innerHTML = hits.map(r => assetCard(r, true)).join('') ||
            emptyState('一致する素材がありません', '別の言葉で検索するか、素材の種類を「すべて」にしてお試しください。', 'search', '検索条件を変更');
          setView(activeView);
          setStatus(`検索結果 ${{hits.length}} 件`, 'ok');
        }} catch (error) {{
          if (request !== searchRequest) return;
          out.innerHTML = emptyState('検索できませんでした', '接続や検索条件を確認して、もう一度検索してください。', 'search', '検索欄へ戻る');
          throw error;
        }} finally {{
          if (request === searchRequest) out.removeAttribute('aria-busy');
        }}
      }});
    }};
    out.innerHTML = emptyState('言葉で素材を探しましょう', '上の検索欄に「海辺の風景」「赤いバッグ」などの言葉を入力してください。ここに検索結果が表示されます。', 'search', '検索欄に入力');
    assetsEl.innerHTML = emptyState('ライブラリを読み込み中…', '画像・動画とフォルダを取得しています。');
    runAction(async () => {{
      try {{
        await refreshAll();
        if (!statusEl.className) setStatus('待機中');
      }} catch (error) {{
        assetsEl.innerHTML = emptyState('ライブラリを読み込めませんでした', '接続を確認して、ページを再読み込みしてください。');
        throw error;
      }} finally {{ assetsEl.removeAttribute('aria-busy'); }}
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
