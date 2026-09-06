# Plan: SKU product-embedder eval

## Protocol

1. **Corpus**: images with `product_id`; ≥2 images per SKU; hard negatives =
   other SKUs. Prefer live library export; else generate synthetic multi-view
   SKUs under `harness/eval/008-sku-product-embedder-eval/corpus/`.
2. **Task**: image→image; for each query, rank other gallery images by cosine;
   Recall@1 / Recall@5 = fraction of queries with ≥1 same-`product_id` in top-K
   (self excluded).
3. **Baseline**: production OpenCLIP (`xlm-roberta-base-ViT-B-32` / laion5b).
4. **Candidate (open)**: alternate OpenCLIP tower suited to product/vision
   (`ViT-B-32` / `openai`) via eval-only adapter — same `EmbeddingPort` shape.
5. **Candidate (commercial)**: Google Vision Product Search — **skip** unless
   Product Set already exists within ≤ few USD; record skip reason (D2/D7).
6. **Go**: candidate Recall@K clearly > baseline on locked corpus; else no-go.
7. Artifacts: `scripts/sku-embedder-eval`, JSON under
   `harness/eval/008-sku-product-embedder-eval/`, research markdown.

## Non-goals in code

No Cloud Run default switch; no Domain import of HF/OpenCLIP beyond adapters.
