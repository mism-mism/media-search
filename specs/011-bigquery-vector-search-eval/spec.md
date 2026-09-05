---
id: "011"
status: draft
profile: full
profile_reason: "Managed vector + embedding cost/architecture; may replace sqlite-vec path"
---

# Spec: BigQuery Vector Search evaluation

## Problem

Production search/index use **OpenCLIP + sqlite-vec** on Cloud Run with DB
synced to GCS. Import is CPU-heavy; scale and durable vector storage are
awkward. Google documents **BigQuery embeddings + `VECTOR_SEARCH`** (incl.
GCS / ObjectRef multimodal paths) as a managed alternative — worth an
explicit **eval + go/no-go**, not a silent rewrite.

## Goal

Offline / scripted evaluation of BigQuery Vector Search (and related
embedding generation) vs the current OpenCLIP + sqlite-vec path on a locked
corpus and latency/cost bar. **No production default cutover in 011.**

```text
Same product search contract (text / by-image / product_id filters)
        │
   ┌────┴─────────────────────────┐
   ▼                              ▼
OpenCLIP + sqlite-vec (baseline)  BigQuery VECTOR_SEARCH (+ embed path TBD)
```

## User

Operator deciding whether to invest in a BigQuery-backed vector path.

## Requirements

- R1. Evaluation Feature — no Cloud Run default switch in 011.
- R2. Compare quality (hit@k / Recall) and **warm search latency**, Import/
  embed cost notes vs baseline.
- R3. Clarify embedding source (Vertex via BQ ML vs bring-your-own OpenCLIP
  vectors into BQ) per Round 1.
- R4. Respect 004 (Vertex embed default no-go) unless Round 1 explicitly
  re-opens that decision for BQ-only batch.
- R5. Written go/no-go in `docs/research/011-bigquery-vector-search-eval.md`.
- R6. Ports & Adapters: Domain must not import BigQuery SDKs.

## Acceptance Criteria

- AC1. Clarify Round 1 locked; then `active`.
- AC2. Baseline OpenCLIP + sqlite-vec numbers on locked protocol.
- AC3. BigQuery path evaluated with same queries/corpus protocol.
- AC4. Research note with go/no-go (latency, quality, $); spend ceiling held.
- AC5. Production default unchanged; full-profile reviews PASS.

## Out of Scope

- Rewriting library UI onto BigQuery in 011
- Mandatory Vertex default on Cloud Run interactive path
- Dropping sqlite without a follow-on Feature

## Open Questions

See `clarify.md`.
