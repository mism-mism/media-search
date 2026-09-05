---
id: "004"
status: draft
profile: full
profile_reason: "Managed AI/vector adapters — architecture and cost risk."
---

# Spec: Vertex embeddings / Vector Search evaluation (draft)

## Problem

002 runs OpenCLIP + sqlite-vec on Cloud Run. Managed Vertex may reduce
ops cost at scale but was deferred until Local and GCP plumbing exist.

## Goal

Evaluate Vertex multimodal embeddings and/or Vertex AI Vector Search as
**adapter candidates** without Domain rewrite. Produce a go/no-go and, if go,
a follow-on implementation Feature.

## Constraints

- Depends on 002 merge; prefer after 003 IAP before broad exposure.
- Ports & Adapters; Domain remains GCP-agnostic.
- Fake ≠ semantic PASS still applies.

## Open Questions

TBD in clarify (model APIs, index hosting, cost, latency, JA quality vs OpenCLIP).

## Out of Scope (this draft)

- Immediate production cutover to Vertex
- Removing Local/OpenCLIP path
