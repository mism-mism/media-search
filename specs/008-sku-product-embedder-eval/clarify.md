# Clarify: SKU / product-retrieval embedder evaluation

## Ambiguities

007 hybrid is live: image search = visual similar; SKU = exact `product_id`.
OpenCLIP is weak for same-SKU identity. Feature **008** decides whether a
dedicated **product-retrieval** embedding path is worth a follow-on cutover.

009 performance is merged; Round 1 locked 2026-09-06.

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | 008 scope | A **eval + go/no-go only** / B eval + optional non-default flag spike / C implement production cutover | resolved → **A** |
| Q2 | Primary candidate class | A fashion/product CLIP family / B commercial product API / C fine-tune private / D **bake-off A+B** | resolved → **D** |
| Q3 | Labeled corpus | A **library `product_id` assets** / B public pairs / C synthetic only | resolved → **A** (+ B fallback) |
| Q4 | Go bar | A **Recall@K clearly beats OpenCLIP** / B any improvement / C cost only | resolved → **A** |
| Q5 | After go | A **follow-on Feature** / B auto-cutover | resolved → **A** |
| Q6 | Where eval runs | A **offline scripts** / B Cloud Run flag | resolved → **A** |
| Q7 | Spend ceiling | A **≤ few USD** + local OK / B no cap / C local only | resolved → **A** |
| Q8 | Profile | A lean / B **full** | resolved → **B** |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | 008 = evaluation toward pixel-side SKU retrieval | Spec | 2026-09-06 |
| D0b | Start after 009 merge | Human | 2026-09-06 |
| D1 | Eval + go/no-go only — no production cutover | Human | 2026-09-06 |
| D2 | Bake-off: open product-CLIP-class + commercial only if ≤ few USD / easy; else document commercial skip | Human | 2026-09-06 |
| D3 | Prefer `product_id` library assets; public/synthetic pairs if too few SKUs | Human | 2026-09-06 |
| D4 | Go requires clear same-SKU Recall@K win vs OpenCLIP | Human | 2026-09-06 |
| D5 | Cutover only in a later Feature | Human | 2026-09-06 |
| D6 | Offline / script harness | Human | 2026-09-06 |
| D7 | Few-USD API ceiling; local models free | Human | 2026-09-06 |
| D8 | profile = full | Human | 2026-09-06 |

## Unresolved items

None for Domain / Constraints / Acceptance Criteria.
