---
id: "005"
status: active
profile: full
profile_reason: "Async ingest, concurrency, GCS thumbs, Cloud Run Job — cross-boundary ops"
---

# Spec: Scale media ingest (10k + video)

## Problem

The live stack works for a tiny corpus (~tens of assets) with synchronous
Import. Creative teams need on the order of **~10k images and videos**,
imported via the **UI on demand**, without request timeouts or lost
thumbnails after scale-to-zero. Search may stay “a few seconds.”

## Goal

Make import and index durability suitable for a **~10k mixed image/video**
corpus with **team UI ingest**, keeping the 001 search contract and
**OpenCLIP + representative video frames**.

## User

Team operators (IAP allowlist) who upload/import media through the web UI and
search by meaning + `mediaType` / tags.

## Requirements

- R1. Support a corpus on the order of **~10k** MediaAssets (**images and
  videos**), indexed with existing embedding grain (one vector per image
  frame; videos → representative frames → collapse to asset).
- R2. **UI-triggered Import** works for team use via **async Cloud Run Job**
  (HTTP enqueues; does not run the full corpus embed in one request).
- R3. Import remains **differential** (skip unchanged; report added/updated/
  skipped).
- R4. **best-frame / thumbnail** bytes survive Cloud Run scale-to-zero via
  **GCS**.
- R5. Concurrent Import does not corrupt the vector/metadata store
  (**single-writer** lock / serialize).
- R6. Search contract unchanged: semantic `q` + `mediaType` + tags AND;
  latency bar = **few seconds OK**.
- R7. Embedder default remains **OpenCLIP**.
- R8. Operators can see Import **progress / status** (and failure reason).

## Acceptance Criteria

- AC1. Documented path to ingest ~10k-scale mixed corpus (images + videos)
  via UI-started async job without HTTP timeout failure of the enqueue path.
- AC2. After Import Job completes, semantic search returns expected assets for
  a fixed smoke query set (images and at least one video with `bestFrame`).
- AC3. Killing / scaling to zero the web service does **not** 404 durable
  thumbnails for previously imported video best-frames.
- AC4. Two overlapping Import attempts are safe (second waits, rejects, or
  queues — no DB corruption).
- AC5. Differential Import stats remain visible (added/updated/skipped +
  totals).
- AC6. Out of Scope upheld: no Vertex default cutover; no fine-grained video
  timeline index; no pgvector/Vertex VS.

## Out of Scope

- Switching default embedder to Vertex / Gemini Embedding
- Native video embedding APIs or second-level timeline search
- Managed Vector Search / custom ANN engine / pgvector
- Sub-second search latency redesign
- Multi-region active-active writers
- Public (non-IAP) access

## Constraints

- Keep Domain / Application free of GCP SDK leakage (ports + adapters).
- Prefer extending 002/003 adapters over a platform rewrite.
- Cost: scale-to-zero web OK; Jobs bill only while running.
- Clarify D1–D10 locked.

## Open Questions

- None
