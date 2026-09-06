# Clarify: Product master + upload-time select

## Ambiguities

Human direction (2026-09-06): **manual select at upload**; **product master**
(not auto visual ID; not ref-image gallery). Round 1 locked same day.

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | Upload `product_id` | A **optional** select / B required | resolved → **A** |
| Q2 | Master fields (v1) | A **`product_id` + `name` only** / B + tags / C PIM-like | resolved → **A** |
| Q3 | Id / name mutability | A id immutable, name editable / B both editable | resolved → **A** (id fixed after create; name editable) |
| Q4 | Delete product | A soft-block / B cascade clear / C **forbid if in use** | resolved → **C** |
| Q5 | Storage | A **sqlite `products`** / B GCS JSON | resolved → **A** |
| Q6 | Profile | A **lean** / B full | resolved → **A** |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | Product master + upload select; no auto visual ID | Human | 2026-09-06 |
| D1 | Upload product select is **optional** | Human | 2026-09-06 |
| D2 | Fields: **`product_id` + `name`** | Human | 2026-09-06 |
| D3 | **`product_id` immutable** after create; **name editable** | Human | 2026-09-06 |
| D4 | **Delete forbidden** while any asset references the id | Human | 2026-09-06 |
| D5 | Persist in sqlite **`products`** table (same DB) | Human | 2026-09-06 |
| D6 | profile = **lean** | Human | 2026-09-06 |

## Unresolved items

None for Domain / Constraints / Acceptance Criteria.
