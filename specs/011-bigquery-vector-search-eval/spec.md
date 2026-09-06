---
id: "011"
status: completed
profile: full
profile_reason: "Managed vector + embedding cost/architecture; may replace sqlite-vec path"
---

# Spec: BigQuery Vector Search evaluation

## Problem

OpenCLIP + sqlite-vec on Cloud Run (DB synced to GCS) is awkward at scale and
makes Import CPU-heavy. BigQuery `VECTOR_SEARCH` is a candidate durable path.

## Goal

Evaluate BigQuery Vector Search (+ embedding variants) vs baseline; write
**go/no-go**. No production default cutover in 011.

## User

Operator deciding investment in a BigQuery-backed vector path.

## Requirements

- R1. Eval only (D1).
- R2. Passes: (a) baseline OpenCLIP+sqlite-vec; (b) BYO OpenCLIP vectors in BQ
  + `VECTOR_SEARCH`; (c) BQ/Vertex embed path when APIs allow within spend (D2).
- R3. Record quality + search latency; interactive cutover needs p95 &lt;1s (D3).
- R4. No Vertex as Cloud Run interactive default (D4).
- R5. Corpus protocol D5; spend ceiling D6.
- R6. Research note; Domain free of BQ SDKs (adapters/scripts only).

## Acceptance Criteria

- AC1. Clarify Round 1 locked (D1–D7).
- AC2. Baseline numbers on locked protocol.
- AC3. BYO-BQ pass executed (or blocked with infra reason + retry notes).
- AC4. BQ/Vertex embed pass executed or **explicitly skipped** within D6/D4.
- AC5. `docs/research/011-bigquery-vector-search-eval.md` go/no-go; prod unchanged.
- AC6. Full-profile reviews PASS.

## Out of Scope

- Library UI rewrite onto BQ
- Silent sqlite removal
- Interactive Vertex default on Cloud Run
