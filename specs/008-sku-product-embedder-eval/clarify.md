# Clarify: SKU / product-retrieval embedder evaluation

## Ambiguities

007 hybrid is live: image search = visual similar; SKU = exact `product_id`.
OpenCLIP is weak for same-SKU identity. Feature **008** decides whether a
dedicated **product-retrieval** embedding path is worth a follow-on cutover —
mirroring 004’s eval-then-decide pattern (004 = Vertex NL embeddings; 008 =
SKU/product identity).

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | 008 scope | A **eval + go/no-go only** / B eval + optional non-default flag spike / C implement production cutover | unresolved → rec **A** |
| Q2 | Primary candidate class | A fashion/product CLIP family (e.g. OpenCLIP fine-tunes / Marqo-style product) / B commercial product API (Google Vision Product Search etc.) / C fine-tune our own on private SKUs / D pick after short bake-off of A+B | unresolved → rec **D** |
| Q3 | Labeled corpus | A use assets that already have `product_id` in GCS/library / B curated public product pairs / C synthetic duplicates only | unresolved → rec **A** (fallback B if too few SKUs) |
| Q4 | Go bar | A same-SKU Recall@K **clearly beats** OpenCLIP on locked set / B any improvement / C cost/latency only | unresolved → rec **A** |
| Q5 | After go | A follow-on Feature implements adapter + reindex; OpenCLIP stays until then / B auto-cutover if go | unresolved → rec **A** |
| Q6 | Where eval runs | A **offline scripts / local or one-off VM** (no prod cutover) / B Cloud Run flag | unresolved → rec **A** |
| Q7 | Spend ceiling | A **≤ few USD** + local GPU/CPU ok / B no cap / C local models only (no paid API) | unresolved → rec **A** |
| Q8 | Profile | A lean / B **full** | unresolved → rec **B** |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | 008 = **evaluation** Feature toward pixel-side SKU retrieval; not 007 rework | Spec draft | 2026-09-06 |

## Unresolved items

Agents must not implement until Round 1 (Q1–Q8) is locked.

Recommended package: **A D A A A A A B** → D1–D8 as:

- **D1** Eval + go/no-go only (no prod cutover)
- **D2** Short bake-off: open product-CLIP-class **and** one commercial option if cheap; pick winner for metrics
- **D3** Prefer library assets with `product_id`; supplement with public pairs if &lt; N SKUs (N in plan)
- **D4** Go requires clear same-SKU Recall@K win vs OpenCLIP
- **D5** Cutover only in a later Feature
- **D6** Offline / script harness
- **D7** Few-USD API ceiling; local models free
- **D8** profile = full
