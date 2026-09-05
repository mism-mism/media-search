---
reviewer_role: code-quality-reviewer
feature: 007-product-search-api
verdict: PASS
---

# Code quality review — 007-product-search-api

**Verdict: PASS**

Scope: local maintainability of the 007 diff focus
(`application/search_media.py`, `ports/search.py`, `domain/media_asset.py`,
`api/app.py` search surface, `adapters/sqlite_store.py` `product_id`,
`tests/test_product_search.py`) against `rules/code-quality.md`.

Axes: Correctness / Understandability / Changeability / Simplicity.  
Architecture / dependency-direction findings are out of scope except where they
affect local readability or error locality.

Mechanical enforcers (format/lint/type/complexity/dead-code): N/A —
`NOT_CONFIGURED` in rules; judgment review only.

---

## Correctness — PASS

| Evidence | Assessment |
|----------|------------|
| Text path merges semantic KNN with `display_name`/`tags` substring (`_text_matches`); text-only hits get `TEXT_MATCH_FLOOR`; existing hits keep best score and add `"text"` | Matches R1 / AC1; covered by `test_text_merge_*` |
| Image path embeds bytes → same `_knn_best_by_asset` → `match_kinds={"visual"}`; API `mode="visual_similar"` | Bare image search does not claim SKU (R2/R3/AC2) |
| `product_id` filter in `_finalize`: exact match; missing asset `product_id` treated as `""` so it does not pass a set filter | Hybrid SKU rule (D6/AC3); `test_product_id_filter_exact` + API miss path |
| `EmptyQueryError` / `EmptyImageError` raised in use case; mapped to HTTP 400 at API with `from exc` | Explicit failure paths; not swallowed |
| SQLite: column on CREATE + `ALTER` migration + upsert/read via `_row_to_asset` | Persistence of optional `product_id` is consistent |
| API empty `product_id` coerced with `product_id or None` before `SearchQuery` / `ImageSearchQuery` | Boundary does not treat `""` as an active filter |

Non-blocking: unused import `MediaType` in `search_media.py` (dead code smell only).  
Non-blocking: whitespace-only `product_id` query is truthy and would filter literally — unlikely client case; library `set_product_id` already strips.

---

## Understandability — PASS

| Evidence | Assessment |
|----------|------------|
| Domain names: `product_id`, `ImageSearchQuery`, `match_kinds`, `visual_similar`, `EmptyImageError` | Intent readable; no `utils` / `helpers` / `manager` |
| OpenAPI field descriptions on `SearchHitOut.match_kinds`, `TextSearchIn.product_id`, by-image summary | Hybrid SKU contract visible at the HTTP edge |
| Shared finalize (`media_type` / `tags` / `product_id` filters) lives in one `_finalize` | Readers see one filter story for text and image |
| `_HitAcc` is a private mutable merge accumulator with clear slots | Local, not a vague “manager” |

Non-blocking: `TEXT_MATCH_FLOOR = 0.15` names the role but has no WHY comment (why that floor vs semantic scores).  
Non-blocking: `match_kinds` are free strings (`semantic`/`text`/`visual`) rather than a small enum — documented in OpenAPI; fine at this size.

---

## Changeability — PASS

| Evidence | Assessment |
|----------|------------|
| `SearchQuery` / `ImageSearchQuery` + ports unchanged in shape except optional `product_id` | Filter extension without rewriting adapters |
| KNN collapse extracted to `_knn_best_by_asset`; filters centralized in `_finalize` | Text vs image modes share seams; new filter has one place to land |
| `create_app` DI + hermetic `test_product_search.py` (fakes + `TestClient`) | Use case and API behaviors are independently testable |
| Sqlite migration follows existing `display_name` / `folder_id` ALTER pattern | Schema evolution stays local to the adapter |

Non-blocking: `SearchQuery` and `ImageSearchQuery` duplicate filter fields — intentional parallel DTOs; a shared base would be speculative until a third mode appears (rules: do not abstract mere similarity).

---

## Simplicity — PASS

| Evidence | Assessment |
|----------|------------|
| No new framework, plugin registry, or speculative retrieval stack | OpenCLIP + optional exact `product_id` matches D6 hybrid |
| `_HitAcc` + two execute methods; not a generic “search pipeline” DSL | Accidental complexity kept low |
| Text substring via `list_all` + `_text_matches` | Appropriate for current corpus / warm-latency constraint; no premature FTS layer |
| GET/POST text share `_run_text_search`; by-image is a thin multipart adapter | Boundary duplication is mechanical, not conceptual |

Non-blocking: by-image `top_k` validated manually while text uses FastAPI `ge`/`le` — slight API asymmetry, still clear.

---

## Required follow-ups

None (PASS). Optional nits (dead `MediaType` import, WHY on `TEXT_MATCH_FLOOR`, `pytest.raises` in `test_empty_image_raises`) may be cleaned opportunistically; they do not fail any axis.

## Summary

007’s search changes stay cohesive: hybrid text merge and visual image KNN share KNN/filter seams, SKU filtering is exact and boundary-explicit, and tests cover the acceptance paths without speculative abstraction. Axes hold.
