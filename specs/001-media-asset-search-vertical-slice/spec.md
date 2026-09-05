---
id: "001"
status: active
profile: full
profile_reason: "First product Architecture feature — establishes Domain ports, Local adapters, API/container boundaries, and future GCP swap seams."
---

# Spec: Media Asset Search Vertical Slice (Local-first)

## Problem

Operators need to find image and video assets by **meaning**, with light
metadata filters, and preview the source file — without depending on GCP during
development. Premature cloud/platform choices obscure whether search itself
works.

## Goal

Deliver one **local-first** vertical slice:

```text
directory import → metadata → embed → local vector index
→ semantic search + mediaType/tags filters
→ mixed MediaAsset results → detail → HTTP preview
```

plus a **thin** reproducible container for that slice, and converge under
profile **full** (including required **semantic-real** gate).

GCP deployment is **out of scope** (Feature 002).

## User

Local single operator / developer (no authentication).

## Requirements

### Import & identity

- R1. Batch-import from a designated directory (watch/fs events not required).
- R2. Asset identity = relative path from import root; re-import is idempotent
  upsert (metadata / frames / embeddings updated).
- R3. Unsupported formats: SKIP + explicit warning + import summary + continue.
- R4. Guaranteed formats for AC: **JPEG, PNG, MP4 (H.264)**. Others best-effort
  only, not AC.

### Metadata

- R5. Auto-extract technical metadata: type/MIME, size, width/height, duration,
  basic EXIF, ffprobe-class media fields as available.
- R6. `tags` / `description` may come from fixtures or human input.
- R7. No AI caption/tag generation in this feature.

### Video → same vector space

- R8. Videos contribute **representative frames** embedded in the **same**
  space as images; search results remain **MediaAsset** (no VideoSegment
  domain).
- R9. `MAX_REPRESENTATIVE_FRAMES = 3`. Deterministic uniform sampling over
  duration when `duration >= 5s`.
- R10. If `duration < 5s`, use **one middle frame** only.
- R11. Video score = `max(frame scores)`; retain `bestFrame` as evidence.
- R12. Audio, subtitles, scene detection: out of scope.

### Search

- R13. Primary retrieval is **semantic search** (non-empty query required).
- R14. Filters: `mediaType` (`image`|`video`); `tags` with **AND** semantics
  when multiple tags are specified.
- R15. No keyword/path/description substring search; no fusion ranking of
  heterogeneous scorers.
- R16. Empty `q` → **400** / validation error (no filter-only browse).

### Embedding & index

- R17. `EmbeddingPort` with Fake (wiring/deterministic) and Real Local
  (semantic AC) implementations; config switch (e.g. `EMBEDDER=fake|local`).
- R18. Default product-like startup uses Real Local — not Fake.
- R19. Local vector engine: existing single-runtime engine via adapter; brand
  chosen in `plan.md` after ports (not in this spec).
- R20. No managed/distributed large-scale vector infrastructure.

### API / UI

- R21. HTTP API + minimal UI: search, filters, mixed results (asset, mediaType,
  score, thumbnail), detail, preview.
- R22. List thumbnails: image thumb; video thumb from **bestFrame** for the
  query (UI presentation only — not a domain search hit type).
- R23. Detail may expose optional `bestFrame` / matched-frame evidence.
- R24. Preview via MediaSource port → Local adapter → HTTP media endpoint
  (Range/full streaming server not required).
- R25. No admin/edit UI; no auth.

### Container & verify

- R26. Thin reproducible container: model prep (version pinned, cacheable) →
  compose up → fixture import → Real Local embed → semantic golden PASS.
  Models are **not** baked into the image; first download may need network.
  Full offline reproducibility is a **non-goal**.
- R27. Default `./scripts/verify` stays deterministic/Fake-capable and must not
  require huge model download by default.
- R28. **semantic-real** is a **separate but Required** gate for 001
  convergence: fixed model/version + golden Top-K. Cache miss → download →
  run; download failure → **FAIL** (no silent SKIP).
- R29. Fake results must never be treated as semantic-search PASS.

## Acceptance Criteria

- AC1. With no GCP credentials, the app starts locally (and via the thin
  container path) and serves API + minimal UI.
- AC2. Importing a fixture directory upserts JPEG/PNG/MP4(H.264) assets with
  technical metadata; unsupported files are skipped with an explicit summary.
- AC3. Re-importing the same relative paths does not duplicate assets.
- AC4. Semantic golden set: **8–12** `(query, expectedAssetId)` pairs covering
  **both** images and videos; with Real Local embedder,
  `expectedAssetId ∈ Top-5`.
- AC5. Filters `mediaType` and multi-tag **AND** restrict results as specified;
  empty `q` returns 400.
- AC6. Video hits appear as one MediaAsset; score reflects max frame score;
  list shows bestFrame-derived thumbnail; detail can show bestFrame evidence.
- AC7. Detail preview displays image / plays video via HTTP media endpoint.
- AC8. Deterministic verify (incl. Fake wiring) PASSes; **semantic-real**
  PASSes; required **full** profile reviews exist and PASS for convergence.
- AC9. Outer product review: human judges a small set of queries as “usable”
  (subjective; complements AC4 — no Recall@10 mandate).

## Out of Scope

- GCP deployment and concrete GCP service selection (→ 002)
- Managed/distributed vector infrastructure
- Custom ANN engine implementation
- AI captions/tags; keyword/path/description search; fusion ranking
- Filter-only browse; auth; VideoSegment domain; scene/ASR/subtitles
- Duration/size range filters; production-grade Range streaming
- Dual Local adapters solely to “prove” DIP

## Constraints

- Align with [`docs/PRODUCT.md`](../../docs/PRODUCT.md) and
  [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
- Local-first / GCP-second / Domain knows neither cloud.
- Do not add microservices, Kubernetes, complex IaC, Pub/Sub, or distributed
  job platforms “for later GCP”.
- **Runtime (locked):** Python 3.10+ / FastAPI (container target 3.12); OpenCLIP
  xlm-roberta-base-ViT-B-32 / laion5b_s13b_b90k (multilingual); SQLite +
  sqlite-vec — details in Architecture + this feature's plan.md.
  feature `plan.md`.
- **Multimodal embedding contract:** text and image (frame) vectors share one
  space/dimension; Fake must not satisfy semantic AC.
- **Index grain:** one vector per frame (image = one frame); query results
  collapse to MediaAsset by `asset_id`.
- Bootstrap prompt is summary only:
  [`docs/prompts/media-search-server-bootstrap.md`](../../docs/prompts/media-search-server-bootstrap.md)

## Open Questions

- None
