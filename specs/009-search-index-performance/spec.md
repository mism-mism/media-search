---
id: "009"
status: active
profile: full
profile_reason: "Runtime cost (min instances) + indexing throughput + query path changes"
---

# Spec: Search + index performance

## Problem

Production search feels **too slow** (often multi-second / cold-start heavy).
**Indexing / Import** is also slow (per-asset OpenCLIP on CPU in a single Job
writer). Operators reject the prior “few seconds warm is OK” bar for daily use.

## Goal

Make **warm search** and **Import indexing** acceptably fast for team use,
without weakening semantic quality or the 007 hybrid SKU contract.

## User

IAP operators using library upload + text/image search on Cloud Run.

## Requirements

- R1. Warm search p95 &lt;1s on a fixed query set (after warm).
- R2. Indexing ≥3× images/min vs measured baseline (same corpus sample).
- R3. Cloud Run service `min-instances=1` + eager OpenCLIP load at process start.
- R4. Query embedding LRU cache; text name/tag match via SQL (not full
  `list_all` scan).
- R5. Import: overlap materialize/embed work with a **single-writer** path to
  sqlite; tune Job CPU/memory.
- R6. Keep current OpenCLIP model identity (phase 1); no intentional semantic
  regression on smoke queries.
- R7. Document before/after in `docs/research/009-search-index-performance.md`.

## Acceptance Criteria

- AC1. Clarify Round 1 locked (D1–D8).
- AC2. Research note records baseline + after for search and Import sample.
- AC3. Warm search design/tests cover cache + SQL text path; deploy uses
  min-instances=1 and startup prewarm.
- AC4. Import concurrency/pipeline covered by tests; Job resources raised in
  deploy/Terraform.
- AC5. Out of Scope upheld (no 008 cutover; no multi-writer sqlite redesign).

## Out of Scope

- 008 SKU product-embedder bake-off
- API-key auth
- Smaller OpenCLIP cutover (phase 2 if needed)
- Sharded multi-writer index

## Constraints

- Revises 007 D3 latency posture for operators.
- 005 single-writer lock remains authoritative for sqlite mutations.
