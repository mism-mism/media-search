---
reviewer_role: architecture-reviewer
feature: 004-vertex-eval
verdict: PASS
---

# Architecture review: 004

Vertex access confined to `adapters/vertex_embedder.py` implementing
`EmbeddingPort`. Domain/Application unchanged. Eval harness uses a separate
sqlite-vec DB. Production default path untouched (`EMBEDDER=local`).
