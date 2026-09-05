# Clarify: Product name + similar-image search (API-oriented)

## Ambiguities

Operators want **product-name search** and **similar-image search**, with
acceptable warm latency, eventually as a stable **HTTP API**. Current stack is
text→image OpenCLIP + sqlite-vec; image→image is the same space but **not**
SKU-grade by itself.

Human Round 1 (2026-09-06). Round 2 locked after 006 library UI deploy
acknowledgment (2026-09-06).

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | “Same product” bar | A visual similar OK / B **same SKU-grade required** | resolved → **B** |
| Q2 | Product-name search | A semantic only / B **semantic + display_name/tags text match** | resolved → **B** |
| Q3 | Speed | A **warm p95 few seconds OK** / B warm p95 &lt;1s | resolved → **A** |
| Q4 | API auth (machine) | A **IAP for now** / B add API key/SA | resolved → **A** |
| Q5 | Timing | A **after 006 UI finish** / B start 007 immediately | resolved → **A** |
| Q6 | How to enforce SKU-grade | A require `product_id` metadata + exact match path / B switch to product-retrieval embedder / C **hybrid**: image KNN candidates + `product_id` when present; document OpenCLIP limits | resolved → **C** |
| Q7 | Image search API shape | A `POST /api/search/by-image` multipart / B base64 JSON only / C both | resolved → **A** |
| Q8 | Profile | A lean / B **full** | resolved → **B** |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D1 | Same-product bar is **SKU-grade** (not “looks similar” alone) | Human | 2026-09-06 |
| D2 | Name search = **semantic + display_name/tags string match** | Human | 2026-09-06 |
| D3 | Warm latency: **few seconds p95 OK** (OpenCLIP in-process acceptable) | Human | 2026-09-06 |
| D4 | Auth remains **IAP** for this Feature (no API-key cutover yet) | Human | 2026-09-06 |
| D5 | Implement **after 006 library UI** is finished | Human | 2026-09-06 |
| D6 | Hybrid SKU: keep OpenCLIP index; image→image KNN; optional `product_id` on assets; when `product_id` present (filter or on asset), same-SKU is **exact** on that field; bare image search is **visual similar** in API docs | Human | 2026-09-06 |
| D7 | Image search = `POST /api/search/by-image` (multipart file) | Human | 2026-09-06 |
| D8 | profile = **full** | Human | 2026-09-06 |

## Unresolved items

None for Domain / Constraints / Acceptance Criteria.
