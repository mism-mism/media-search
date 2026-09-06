---
id: "012"
status: completed
profile: full
profile_reason: "Import Job + GCS DB sync / search freshness; ops boundary"
---

# Spec: Import experience

## Problem

After upload, Import feels slow. 009 improved embed parallelism, but each Import
still cold-starts a Job, warms OpenCLIP, and touches the **full** media prefix.
Library uploads can also be skipped as `unchanged` because metadata is written
before embed — so vectors may never land.

## Goal

Make **upload → indexed / searchable** feel acceptably fast for typical adds,
with correct incremental indexing and fresh search after Job success.

## User

Operators uploading media in the Library UI and waiting for Import.

## Requirements

- R1. True incremental indexing: process assets that need vectors or changed
  content; avoid full-corpus materialize when unchanged+has vectors (D2).
- R2. Library upload path must result in embeddings (fix size-only skip) (D2).
- R3. Prefer scoped keys from upload enqueue when provided (single-add path) (D1/D3).
- R4. After successful Import Job, service reloads DB so search sees new vectors (D5).
- R5. Keep production OpenCLIP embedder (D4).
- R6. Hermetic evidence for ≥3× wall on single-image add vs full-scan baseline
  on same Job shape (D3); document residual Job cold start.

## Acceptance Criteria

- AC1. Clarify Round 1 locked (D0–D6).
- AC2. Hermetic tests: new library upload is not skipped as unchanged; missing
  vectors force re-embed; unchanged+has-vectors skips without re-embed;
  optional `only_keys` scopes work; DB reload after success is wired/testable.
- AC3. Measured/hermetic ≥3× class speedup for single-image incremental vs
  full materialize baseline (or research note with residual).
- AC4. Full-profile reviews PASS; model unchanged.

## Out of Scope

- BigQuery interactive search (011 no-go)
- Auto SKU from pixels
- 008 model cutover
- Search warm path redesign (009)
- GPU Job / smaller model (Q4=A)
- Job min-instances / warm pool (Q2=A)

## Constraints

- sqlite single-writer + GCS DB sync remain
- Domain free of Cloud Run SDK details (adapters)

## Open Questions

None (Round 1 locked).
