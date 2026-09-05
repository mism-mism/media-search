# Research: 004 Vertex embeddings evaluation

Date: 2026-09-05  
Project: `laperm-507708`  
Corpus: 18 images (`data/corpus-web`)  
Queries: 20 fixed JA+EN (`specs/004-vertex-eval/queries.md`)  
Harness: `scripts/vertex-eval` → `harness/eval/004-vertex-eval/results-*.json`

## Setup

| Pass | Embedder | Index | Notes |
|------|----------|-------|-------|
| Baseline | OpenCLIP `xlm-roberta-base-ViT-B-32` | sqlite-vec (local) | Current production path |
| Treatment | Vertex `multimodalembedding@001` dim=1408 | sqlite-vec (separate DB) | `us-central1`; google-genai `gemini-embedding-2` **404** in this project |

Clarify locks: embeddings-only (no Vector Search), offline script, OpenCLIP stays default, spend ≈ few USD.

## Results (hit@1 vs filename hint)

| Pass | hit@1 | import wall | search wall (20q) | API calls |
|------|-------|-------------|-------------------|-----------|
| OpenCLIP | **18/20 (0.90)** | 0.8s | 0.6s | 0 (local) |
| Vertex MM | **19/20 (0.95)** | 20.2s | 12.4s | 38 |

### Misses

| Pass | Query | Got |
|------|-------|-----|
| OpenCLIP | kitchen interior / キッチン | `20-market.jpg` |
| Vertex | 赤い車 | `10-bridge.jpg` |

## Cost / ops notes

- Vertex path billed per embedding call; this run ≈ 18 image + 20 text = 38 calls (small).
- Cold / interactive search on Cloud Run would pay **per query** for text embed (OpenCLIP is free after instance is warm, CPU only).
- `vertexai.vision_models` Multimodal Embedding APIs are **deprecated (remove by 2026-06-24)**; successor Gemini Embedding 2 was **not available** (`404`) on this project/region at eval time.
- Network dependency and region (`us-central1`) vs app region (`asia-northeast1`).

## Go / no-go

**No-go for production cutover or default switch (AC6).**

Reasons:

1. Quality gain on this tiny corpus is **marginal** (+1/20) and not a clear JA win.
2. Latency / ops cost for interactive search is **much worse** than in-process OpenCLIP.
3. Current Vertex multimodal embedding SDK path is **deprecated**; preferred Gemini Embedding 2 not yet usable here.
4. Production already satisfies natural-language search with OpenCLIP + IAP.

**Conditional follow-on (optional Feature later):** re-eval when `gemini-embedding-2` (or successor) is GA on Vertex for this project, with a clearer $/1k embedding price and JA benchmark. Keep the `EmbeddingPort` spike (`adapters/vertex_embedder.py`, `EMBEDDER=vertex`) as a non-default tool.

## Artifacts

- `harness/eval/004-vertex-eval/results-local.json`
- `harness/eval/004-vertex-eval/results-vertex.json`
- `src/media_search/adapters/vertex_embedder.py`
- `scripts/vertex-eval`
