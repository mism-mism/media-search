---
reviewer_role: architecture-reviewer
reviewer_id: architecture-review-subagent
---

# Architecture review: 001-media-asset-search-vertical-slice

## Verdict: PASS

Prior FAIL (Application → `adapters.media_probe` / `adapters.frame_cache`) is
resolved. Dependency direction now matches Ports & Adapters /
`docs/ARCHITECTURE.md`.

## Dependency evidence

### Application ↛ adapters — PASS (confirmed)

Grep of `src/media_search/application/**` for `media_search.adapters`: **no
matches**.

| Module | Depends on |
|--------|------------|
| `application/import_directory.py` | `domain.*`, `ports.{embedding,media_probe,search}`, `application.frame_paths` |
| `application/search_media.py` | `domain.*`, `ports.{embedding,search}` |
| `application/frame_paths.py` | stdlib only (pure path helper) |

### Domain ↛ Infrastructure — PASS

`src/media_search/domain/` has no sqlite / FastAPI / GCP / torch / open_clip /
Pillow / ffmpeg / subprocess imports. Entities remain `MediaAsset`-centric;
frame position rules live in `domain/frames.py`.

### Ports vs adapters — PASS

| Port | Adapter / wiring |
|------|------------------|
| `EmbeddingPort` | `OpenClipEmbedder` / `FakeEmbedder`; composed in `main.py` |
| `VectorSearchPort` | `SqliteVecSearch` / `InMemoryVectorSearch` |
| `MetadataRepositoryPort` | `SqliteMetadataRepository` / `InMemoryMetadataRepository` |
| `MediaProbePort` (`ports/media_probe.py`) | `LocalMediaProbe` (`adapters/media_probe.py`); injected into `ImportDirectory` from `main.py` |

Composition root only (`main.py`) imports Local adapters and wires
`media_probe=LocalMediaProbe()`. Delivery (`api/app.py`) uses FastAPI +
`application.frame_paths` — outer boundary, acceptable.

`adapters/frame_cache.py` deleted; path mapping is not an adapter concern.

### Video frames → MediaAsset collapse — PASS

- Index: one vector per frame via `VectorSearchPort.upsert_frame`.
- Query: `SearchMediaAssets` max-score collapse by `asset_id` →
  `AssetSearchHit(asset: MediaAsset, best_frame: FrameHit | None)`.
- Sampling policy: Application calls
  `domain.frames.representative_frame_positions`; extraction goes through
  `MediaProbePort.extract_frame_jpeg`.

### Non-blocking notes (do not affect PASS)

- Doc drift: `clarify.md` / `spec.md` still mention OpenCLIP `openai` weights;
  `plan.md` / `ARCHITECTURE.md` / `openclip_embedder.py` use
  `xlm-roberta-base-ViT-B-32` / `laion5b_s13b_b90k` — code matches Architecture
  intent.
- `plan.md` Contracts section still stale vs implemented HTTP shapes.
- `rules/architecture.md` enforcers remain `NOT_CONFIGURED` (SKIP).
- Residual module-level helpers in `adapters/media_probe.py` (e.g.
  `plan_video_frames`) are unused by Application; optional cleanup only.
