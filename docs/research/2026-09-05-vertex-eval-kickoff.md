# Vertex eval kickoff (Issue #5)

Draft starting point for Feature 004.

## Compare (to fill)

| Axis | OpenCLIP on Cloud Run (002) | Vertex embeddings | Vertex Vector Search |
|------|-----------------------------|-------------------|----------------------|
| Ops | Self-manage model cold start | Managed API | Managed ANN |
| Cost | Always-on / CPU-RAM heavy | Per-call | Index + query |
| JA quality | xlm-roberta CLIP known-good in 001 | TBD measure | n/a |
| DIP | Local adapter today | New EmbeddingPort adapter | New VectorSearchPort adapter |

## Next

- Grill go/no-go criteria
- Spike: embed 001 golden set via Vertex vs OpenCLIP Top-K
