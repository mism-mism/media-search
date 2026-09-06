# Research: 008 SKU / product-retrieval embedder evaluation

Date: 2026-09-06  
Clarify: D1–D8 locked  
Harness: `scripts/sku-embedder-eval`  
Artifacts: `harness/eval/008-sku-product-embedder-eval/`

## Protocol

| Item | Choice |
|------|--------|
| Task | Image→image leave-one-out; same-`product_id` Recall@1 / @5 |
| Corpus | Synthetic multi-view SKUs (4 SKUs × 3 views + 4 negatives) — fallback per D3 (no dense `product_id` library export in this run) |
| Baseline | Production OpenCLIP `xlm-roberta-base-ViT-B-32` / `laion5b_s13b_b90k` |
| Open candidate | `ViT-B-32` / `openai` (eval-only adapter) |
| Commercial | **Skipped** — Vision Product Search needs Product Set setup; exceeds ≤ few USD / quick bake-off (D2/D7). See `commercial-skip.json` |
| Go bar | Candidate R@1 ≥ baseline + 0.05 absolute |

## Results

| Pass | R@1 | R@5 | n_queries | embed wall |
|------|-----|-----|-----------|------------|
| OpenCLIP (prod) | 0.667 | 0.917 | 12 | ~0.4s |
| openai ViT-B-32 | **1.000** | **1.000** | 12 | ~0.4s |

`summary.json` verdict helper: **go-candidate** (openai-vitb32 clearly > baseline on this corpus).

## Interpretation

- On **synthetic** color/crop/brightness views, the English OpenAI CLIP tower
  separates same-SKU views more cleanly than the production multilingual
  OpenCLIP default.
- This does **not** prove SKU identity on real product photography, packaging
  variants, or marketplace images.
- Commercial product APIs were not exercised (cost/setup).

## Go / no-go

**Conditional go for a follow-on Feature** (not a production cutover in 008).

Reasons to proceed to a later implementation Feature:

1. Locked open bake-off shows a clear Recall@K win vs current default on the
   protocol corpus.
2. Adapter shape (`OpenClipVariantEmbedder` / `EmbeddingPort`) is cheap to keep.

**Blockers before any default switch:**

1. Re-run the same harness on **real library assets with `product_id`** (D3
   preferred corpus).
2. Measure JA text search regression if swapping the text tower (openai CLIP is
   EN-centric; production uses xlm-roberta for JA).
3. Cost/latency on Cloud Run for the larger or alternate weights.
4. No silent cutover in 008 (D1/D5) — production remains OpenCLIP multilingual +
   007 hybrid.

**No-go for immediate production default change.**

## Artifacts

- `scripts/sku-embedder-eval`
- `src/media_search/eval/sku_retrieval.py` / `sku_corpus.py`
- `src/media_search/adapters/openclip_variant_embedder.py`
- `harness/eval/008-sku-product-embedder-eval/results-*.json`
- `harness/eval/008-sku-product-embedder-eval/summary.json`
- `tests/test_sku_eval_008.py`
