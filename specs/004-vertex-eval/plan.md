# Plan: 004 Vertex embeddings evaluation

## Approach

1. Fix a **query list** (JA+EN) and use `data/corpus-web` / GCS `incoming/` (~18).
2. **Baseline**: OpenCLIP (`EMBEDDER=local`) import + search → record top-k.
3. **Treatment**: Vertex multimodal embedding adapter implementing
   `EmbeddingPort` (same dimension handling / separate eval DB file).
4. Compare hit@1 / ranked lists, wall time, rough cost; write research note +
   go/no-go.
5. Full-profile Outer reviews for the eval Feature; do **not** change Cloud Run
   default embedder.

## Adapter seam

- Port: existing `EmbeddingPort` (`embed_image` / `embed_text` / `dimension`).
- New: `adapters/vertex_embedder.py` (or under `eval/`) used only by harness /
  optional `EMBEDDER=vertex`.
- Vectors: reuse sqlite-vec with a **separate DB path** so OpenCLIP and Vertex
  indexes do not clash.

## Risks

- Vertex multimodal model ID / region availability in the project
- Dimension mismatch vs OpenCLIP (expected — separate indexes)
- Spend creep → hard stop after ceiling
- JA quality unknown until measured

## Deliverables

| Artifact | Purpose |
|----------|---------|
| `scripts/vertex-eval` (or similar) | Run baseline + Vertex passes |
| `docs/research/004-vertex-eval.md` | Evidence + go/no-go |
| `harness/reviews/004-vertex-eval/*` | full profile |
| Optional adapter | Spike only; default remains local |
