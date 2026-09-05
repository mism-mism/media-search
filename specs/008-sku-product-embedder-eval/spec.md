---
id: "008"
status: draft
profile: full
profile_reason: "Eval may change default embedder / index space — architecture + cost risk"
---

# Spec: SKU / product-retrieval embedder evaluation

## Problem

Feature **007** delivers image→image search as **visual similar** and SKU-grade
only via exact `product_id` metadata. OpenCLIP cosine alone does **not**
reliably mean “same SKU.” Operators still want pixel-side same-product
retrieval when metadata is missing or incomplete.

## Goal

**Evaluate** (not cut over) candidate **product / SKU retrieval** embedding
approaches against today’s OpenCLIP baseline on a labeled same-SKU corpus.
Deliver an explicit **go / no-go** for a follow-on implementation Feature
(adapter + reindex + API labeling change).

```text
Same Domain / Application / Search contract
        │
   EmbeddingPort (image↔image primary for SKU eval)
        │
   ┌────┴─────────────────┐
   ▼                      ▼
OpenCLIP (baseline)   Candidate product-retrieval model(s)
+ sqlite-vec          + sqlite-vec (separate eval DB / namespace)
```

## User

Operator / product owner deciding whether to invest in a product-retrieval
embedder for media-search.

## Requirements

- R1. Evaluation Feature first — **no production default cutover** in 008.
- R2. Ports & Adapters; Domain/Application must not import candidate SDKs
  except behind eval adapters / scripts.
- R3. Keep OpenCLIP + 007 hybrid (`product_id` exact + visual similar) as
  production behavior until a later go Feature.
- R4. Corpus includes **same `product_id` / SKU** with multiple images (and
  hard negatives) per clarify Round 1.
- R5. Metrics: same-SKU retrieval quality (e.g. Recall@K / mAP) vs OpenCLIP,
  plus latency and cost notes.
- R6. Written go/no-go in `docs/research/008-sku-product-embedder-eval.md`.
- R7. Profile and spend / run locus per clarify.

## Acceptance Criteria

- AC1. Clarify Round 1 locked; `status: active` only after that.
- AC2. OpenCLIP baseline recorded on the locked corpus + protocol.
- AC3. ≥1 candidate embedder evaluated with the same protocol.
- AC4. Written go/no-go with quality vs OpenCLIP, latency, cost; stop if
  spend ceiling hit.
- AC5. Full-profile reviews PASS for evaluation scope.
- AC6. Production Cloud Run default remains OpenCLIP; no silent switch.

## Out of Scope

- Replacing OpenCLIP as Cloud Run default inside 008
- Guaranteeing SKU from pixels without eval evidence
- API-key / machine-auth Feature (separate)
- Managed vector DB migration unless clarify explicitly expands

## Constraints

- Builds on 007 hybrid honesty: visual ≠ SKU until proven.
- 004 Vertex multimodal eval was **no-go** for default cutover — do not
  re-litigate Vertex as “NL search better”; this Feature is **SKU/product
  identity** from images.

## Open Questions

See `clarify.md` Round 1 (Q1–Q8).
