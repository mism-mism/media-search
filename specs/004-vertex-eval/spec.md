---
id: "004"
status: completed
profile: full
profile_reason: "Managed AI/vector adapters — architecture and cost risk."
---

# Spec: Vertex embeddings / Vector Search evaluation

## Problem

Production (002+003) runs **OpenCLIP + sqlite-vec** on Cloud Run behind IAP.
Natural-language semantic search already works. Managed **Vertex** may improve
ops, scale, or quality — or may not justify cost/complexity.

## Goal

Evaluate **Vertex multimodal embeddings** as an `EmbeddingPort` adapter
candidate (keep **sqlite-vec** for vectors in this Feature). Deliver:

1. Comparison vs OpenCLIP on the agreed corpus + JA/EN queries
   (quality / latency / cost)
2. Explicit **go / no-go** for a follow-on implementation Feature
3. Optional thin adapter spike behind a non-default flag — **no production
   default switch** in 004

```text
Same Domain / Application / Search contract (NL query + filters)
        │
   EmbeddingPort
        │
   ┌────┴────────┐
   ▼             ▼
OpenCLIP      Vertex embeddings (eval)
+ sqlite-vec  + sqlite-vec (same index shape)
```

## User

Operator deciding whether to invest in Vertex for this product.

## Requirements

- R1. Ports & Adapters; Domain/Application must not import Vertex SDKs.
- R2. Product search contract unchanged: semantic `q` required; mediaType + tags AND.
- R3. Fake embedder never counts as semantic PASS.
- R4. OpenCLIP + Local/GCP path remains the production default after 004.
- R5. Eval uses real Vertex embedding APIs within ≈ few USD spend ceiling.
- R6. Document enabling Vertex APIs for the eval project without weakening IAP
  on production Cloud Run.
- R7. Comparison queries include **Japanese and English**.
- R8. Output: `docs/research/004-vertex-eval.md` (and reviews under
  `harness/reviews/004-vertex-eval/`) with go/no-go + evidence.
- R9. Eval harness is **script / offline** (clarify D9) — not a prod cutover.
- R10. Vertex AI Vector Search (managed index) is **out of scope for 004**
  (deferred; may be a later Feature if embeddings go).

## Acceptance Criteria

- AC1. Clarify Round 1 locked (Q1–Q7) — done in `clarify.md`.
- AC2. Baseline OpenCLIP top-k results recorded for the fixed JA+EN query set
  on the ~18-image corpus.
- AC3. Vertex embedding path indexes the same corpus into sqlite-vec (or
  equivalent eval DB) and records top-k for the same queries.
- AC4. Written go/no-go covering quality vs OpenCLIP, latency, and cost;
  stop cleanly if spend ceiling hit.
- AC5. Full-profile reviews PASS for evaluation scope.
- AC6. Production Cloud Run default remains OpenCLIP; no silent Vertex switch.

## Out of Scope

- Vertex AI Vector Search managed index (004 = embeddings only)
- Immediate production cutover / removing OpenCLIP
- Rewriting Domain for Vertex APIs
- Broad Cloud Run flag rollout (optional spike OK; default stays OpenCLIP)

## Constraints

- 003 IAP is in place for any shared GCP project exposure.
- Smallest Vertex surface that answers go/no-go.
- Secrets never committed; ADC / user credentials for scripts.
- Align with [`docs/PRODUCT.md`](../../docs/PRODUCT.md).

## Open Questions

None — see [`clarify.md`](clarify.md).
