---
reviewer_role: security-reviewer
feature: 007-product-search-api
verdict: PASS
---

# Security review: 007-product-search-api

## Verdict: PASS

Focus areas checked against Spec R5/AC5, D4/D6/D7, and existing path/auth posture.

### Multipart `POST /api/search/by-image` (size)

- Handler reads the entire upload into memory: `data = await file.read()` then
  `ImageSearchQuery(image_bytes=data)` (`src/media_search/api/app.py`).
- Empty body → `EmptyImageError` → HTTP 400 (covered by tests).
- **No app-level max size** on this endpoint (same unbounded `UploadFile.read()`
  pattern as existing `/api/library/upload` from 006).
- Acceptable for 007 given **IAP-only** operator surface (D4) and platform
  request limits; residual DoS/memory risk if a trusted allowlisted caller
  posts a huge body.

### Path traversal (unchanged)

- by-image does not take filesystem paths; query image is bytes only.
- `/media/{asset_id:path}` still rejects `..` path segments and resolves via
  metadata + storage existence checks.
- `LocalMediaStorage._resolve` / `LocalFrameStore._path` still use
  `resolve()` + `relative_to(root)` (and frame keys are sanitized in
  `frame_cache_path`). 007 does not weaken these guards.

### Auth: IAP only (no new API keys)

- No API-key / Bearer / app-level auth added in app or adapters.
- Spec Out of Scope / AC5 / D4 upheld: machine auth remains a future Feature;
  edge IAP posture from 003 unchanged; app stays auth-agnostic.

### `product_id` injection surface (filter only)

- Search uses `product_id` only as **exact Python equality** in
  `SearchMediaAssets._finalize` (`(asset.product_id or "") != query.product_id`).
- Not interpolated into SQL/vector queries; metadata upsert/get remain
  parameterized (`?` placeholders).
- Library `set_product_id` stores stripped string metadata only — not a
  command/path sink.
- Hybrid contract: bare image hits are `match_kinds=["visual"]` /
  `mode=visual_similar`; SKU narrowing requires the filter (tests cover exact /
  miss).

### Other

- No new secrets committed; no new destructive ops beyond existing library
  delete/import paths.

## Residual

- Add an explicit multipart/body size cap (and preferably streaming/chunked
  read) on by-image (and ideally library upload) to harden against
  allowlisted-client DoS / OOM.
