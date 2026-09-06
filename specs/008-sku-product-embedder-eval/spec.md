---
id: "008"
status: completed
profile: full
profile_reason: "Eval may change default embedder / index space — architecture + cost risk"
---

# Spec: SKU / product-retrieval embedder evaluation

## Problem

007 image search is **visual similar**; SKU-grade needs `product_id`. OpenCLIP
alone does not reliably mean same SKU. Need evidence whether a product-retrieval
embedder is worth a follow-on cutover.

## Goal

Offline **eval + go/no-go** of candidate product/SKU retrieval embeddings vs
OpenCLIP baseline on a labeled same-SKU corpus. No production default switch.

## User

Operator deciding investment in a product-retrieval embedder.

## Requirements

- R1. Eval only — no Cloud Run default cutover (D1).
- R2. Ports & Adapters; eval adapters/scripts only outside Domain.
- R3. Production remains OpenCLIP + 007 hybrid until a later Feature (D5).
- R4. Corpus: `product_id` multi-image SKUs + hard negatives (D3).
- R5. Metrics: same-SKU Recall@K (and notes on latency/cost) (D4).
- R6. Bake-off open product-CLIP-class; commercial only if ≤ few USD (D2, D7).
- R7. Offline script harness (D6); research note with go/no-go.
- R8. profile = full (D8).

## Acceptance Criteria

- AC1. Clarify Round 1 locked (D1–D8).
- AC2. OpenCLIP baseline Recall@K on locked protocol/corpus.
- AC3. ≥1 candidate evaluated with the same protocol.
- AC4. `docs/research/008-sku-product-embedder-eval.md` with go/no-go + evidence;
  commercial skipped with reason if over ceiling/setup.
- AC5. Full-profile reviews PASS; production default unchanged.

## Out of Scope

- Production cutover / silent OpenCLIP replacement
- API-key Feature
- Guaranteeing SKU from pixels without go evidence
- Managed vector DB migration

## Constraints

- 004 Vertex NL eval no-go is separate; do not re-litigate NL quality here.
- 009 performance already shipped.
