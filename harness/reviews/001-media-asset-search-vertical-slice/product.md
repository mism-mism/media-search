---
reviewer_role: product-reviewer
reviewer_id: product-review-subagent
---

# Product review: 001-media-asset-search-vertical-slice

## Verdict

**PASS**

Observable product behavior matches Goal / AC1–AC8 for the local-first vertical
slice. AC9 (human “usable” judgment) is **not claimed** here — it remains a
human Outer step. Residual UX/test gaps below do not overturn the PASS.

## Scope checked

- `specs/001-media-asset-search-vertical-slice/spec.md` (+ `clarify.md`)
- `docs/PRODUCT.md`
- Implementation: `src/media_search/`, `tests/`, `scripts/semantic-real`,
  `fixtures/golden/`, `docker-compose.yml`
- Sibling Inner evidence: unit **19 passed / 1 skipped**; semantic-real
  **12/12 PASS** (`open_clip` `xlm-roberta-base-ViT-B-32` /
  `laion5b_s13b_b90k`)

## AC-by-AC

| AC | Verdict | Evidence |
|----|---------|----------|
| **AC1** Start locally / thin container; API + minimal UI; no GCP creds | **PASS** | No GCP SDK/creds in `src/`; `main.py` builds FastAPI app; `/` UI + `/health` + `/api/*`; `docker-compose.yml` services `media-search` (fake smoke) and `media-search-local` (profile `local`, Real Local). Docs: `docs/run-docker.md`. |
| **AC2** Fixture import JPEG/PNG/MP4 + technical metadata; unsupported SKIP + summary | **PASS** | `classify_path` allows `.jpg/.jpeg/.png/.mp4`; `build_asset` probes MIME/size/w/h/(duration); import SKIP + `ImportWarning` + continue (`import_directory.py`); covered by import tests. Golden fixtures: PNG + MP4(H.264). **Note:** basic EXIF (R5) not extracted — soft “as available”; JPEG capability present though golden set is PNG-heavy. |
| **AC3** Re-import upsert, no duplicates | **PASS** | Identity = relative path; `metadata.upsert` + frame delete/reindex; `test_reimport_is_upsert` asserts single asset + `updated`. |
| **AC4** Golden 8–12 pairs, images **and** videos; Real Local → expected ∈ Top-5 | **PASS** | `fixtures/golden/golden.json` = **12** cases (10 image / 2 video expectations); `./scripts/semantic-real` forces `EMBEDDER=local`, imports fixtures, asserts Top-K; reported **12/12 PASS**. Fake path is separate and must not count as semantic PASS (R29) — upheld by script design. |
| **AC5** `mediaType` + multi-tag **AND**; empty `q` → 400 | **PASS** | Empty/whitespace `q` → `EmptyQueryError` → HTTP 400 (API + use-case tests). Tags AND: `_tags_include_all` + `test_tags_filter_is_and`. `media_type` filter in `SearchMediaAssets` + UI select + API query param. **Residual:** no automated test that exercises `media_type=image\|video` (impl + UI present). |
| **AC6** Video → one MediaAsset; max frame score; list bestFrame thumb; detail can show evidence | **PASS** | Collapse-by-`asset_id` keeping max score + `best_frame` (`search_media.py`; unit test). List: `thumbnail_url` → `/thumbnails/{frame_key}` for video; UI `<img src=thumbnail_url>`; API returns `best_frame_key`. Detail JSON does **not** echo bestFrame (R23 “may”); list/search path satisfies “can show”. |
| **AC7** Detail preview image / play video via HTTP media endpoint | **PASS** | Detail exposes `media_url`; `GET /media/{asset_id}` streams file with asset MIME (`FileResponse`); image path tested. Same endpoint serves video MIME. **Residual:** minimal UI links detail to JSON `/api/assets/…` rather than an HTML `<img>`/`<video>` player — still HTTP-preview capable; list thumbs already render media. |
| **AC8** Deterministic verify + semantic-real; full-profile reviews for convergence | **PASS** (product/gates) | Default verify runs Fake-capable pytest (R27); semantic-real separate Required gate PASS (R28). `EMBEDDER` default **local** in `main.py`; compose default fake for light smoke. Fake ≠ semantic PASS. At write time: `test.md` + `code-quality.md` PASS present; this `product.md`; other full Outer artifacts (`architecture` / `security` / `final` / `analyze`) may still be concurrent — **feature completeness gate** must still see the full set. |
| **AC9** Human judges small query set “usable” | **OPEN** | Spec/clarify: Outer **human** complements AC4. Golden Top-K is necessary but not sufficient. **Do not treat this artifact as AC9 PASS.** |

## Out of scope check

| Out of scope | Respected? |
|--------------|------------|
| GCP deployment / concrete GCP services | **Yes** — no `specs/002-*`; no GCP adapters/SDKs in product code |
| Managed/distributed vector infra; custom ANN engine | **Yes** — SQLite + sqlite-vec local adapter |
| AI captions/tags; keyword/path/description search; fusion | **Yes** — sidecar tags only; semantic + filters only |
| Filter-only browse; auth; VideoSegment; scene/ASR | **Yes** — empty `q` invalid; no auth; MediaAsset collapse only |
| Duration/size filters; production Range streaming | **Yes** |
| Dual Local adapters solely to prove DIP | **Yes** |

Aligns with `docs/PRODUCT.md`: local-first semantic + filters + detail/preview;
Fake for wiring; Real Local for semantic AC; container thin; GCP deferred.

## Product intent / silent invention

No silent invention of keyword search, auth, GCP, or captioning. Multilingual
OpenCLIP default (vs older “openai” ViT-B-32 note in clarify plan-time line)
is a model pin choice that **supports** JA golden queries and AC4; not a scope
expansion.

## Residual risks (non-blocking for this PASS)

1. Human AC9 still required for full Outer convergence.
2. `mediaType` filter untested automatically.
3. Detail UI is API/JSON-thin (no embedded player).
4. Compose E2E not in default `./scripts/verify` (intentional vs R27).
5. Full-profile review set completeness is a harness gate beyond this role alone.

## Recommendation

Ship product behavior for 001 local slice **subject to** human AC9 sign-off and
remaining full-profile Outer reviews / `FEATURE=… ./scripts/verify` completeness.
