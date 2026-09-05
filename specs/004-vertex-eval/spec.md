---
id: "004"
status: draft
profile: full
profile_reason: "Managed AI/vector adapters — architecture and cost risk."
---

# Spec: Vertex embeddings / Vector Search evaluation

## Problem

Production (002+003) runs **OpenCLIP + sqlite-vec** on Cloud Run behind IAP.
Natural-language semantic search already works. Managed **Vertex** may improve
ops, scale, or quality — or may not justify cost/complexity. That was deferred
until Local + GCP + IAP existed.

## Goal

Evaluate Vertex multimodal embeddings and/or Vertex AI Vector Search as
**adapter candidates** without Domain rewrite. Deliver:

1. A written comparison vs current OpenCLIP + sqlite-vec (quality / latency / cost)
2. An explicit **go / no-go** for a follow-on implementation Feature
3. If go: a thin adapter spike sketch (ports only; no production default switch
   in 004 unless clarify says otherwise)

```text
Same Domain / Application / Search contract (NL query + filters)
        │
   EmbeddingPort / VectorSearchPort
        │
   ┌────┴──────────────┐
   ▼                   ▼
OpenCLIP+sqlite-vec   Vertex adapters (eval)
(current default)     (candidate)
```

## User

Operator / implementer deciding whether to invest in Vertex for this product.

## Requirements

- R1. Ports & Adapters; Domain/Application must not import Vertex SDKs.
- R2. Product search contract unchanged: semantic `q` required; mediaType + tags AND.
- R3. Fake embedder never counts as semantic PASS.
- R4. OpenCLIP + Local/GCP path remains available after 004.
- R5. Eval uses real Vertex APIs only within the locked spend ceiling (clarify).
- R6. Document how to enable Vertex APIs in project `laperm-507708` (or noted
  project) without weakening IAP on the production Cloud Run service.
- R7. Comparison queries include Japanese and/or English per clarify.
- R8. Output artifact: `harness/reviews/004-vertex-eval/` or
  `docs/research/004-vertex-eval.md` with go/no-go and evidence.

## Acceptance Criteria

*(Locked after clarify Round 1 — placeholders until then.)*

- AC1. Clarify Q1–Q7 resolved; no open OQ blocking Domain/Constraints/AC.
- AC2. Baseline OpenCLIP results on the agreed corpus/queries are recorded.
- AC3. Vertex path under the chosen slice (Q1) produces comparable search
      evidence (or documented failure).
- AC4. Written go/no-go with quality, latency, and cost notes.
- AC5. Full-profile reviews PASS for the evaluation Feature scope.
- AC6. No silent production default switch to Vertex unless clarify D* allows it.

## Out of Scope

- Immediate production cutover to Vertex as the only path
- Removing Local/OpenCLIP
- Rewriting Domain for Vertex APIs
- Full CDN / multi-region Vector Search ops hardening
- Replacing IAP / auth model

## Constraints

- Prefer after 003 IAP (done).
- Smallest Vertex surface that answers go/no-go.
- Secrets never committed; use ADC / workload identity.
- Align with [`docs/PRODUCT.md`](../../docs/PRODUCT.md).

## Open Questions

See [`clarify.md`](clarify.md) — **unresolved until human lock**.
