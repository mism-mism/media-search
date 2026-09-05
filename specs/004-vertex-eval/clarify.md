# Clarify: Vertex embeddings / Vector Search evaluation

## Ambiguities

002/003 production path is **OpenCLIP + sqlite-vec on Cloud Run + IAP**.
Natural-language semantic search already works there. Feature **004** decides
whether managed **Vertex** adapters are worth a follow-on implementation — not
whether NL search exists.

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | What to evaluate in 004? | A **embeddings API only** (Vertex embed → keep sqlite-vec) / B Vertex AI Vector Search index only / C both (embed + managed index) / D research-doc only (no API calls) | unresolved (rec → **A**) |
| Q2 | Production default after 004? | A keep OpenCLIP default; Vertex behind flag / B switch default to Vertex if go / C decide only in follow-on Feature | unresolved (rec → **A**) |
| Q3 | Comparison corpus | A same ~18 Unsplash/GCS corpus + fixed JA/EN queries / B larger private set / C synthetic only | unresolved (rec → **A**) |
| Q4 | Languages in eval | A EN only / B JA+EN / C JA only | unresolved (rec → **B**) |
| Q5 | Go/no-go bar | A quality ≥ OpenCLIP on agreed queries + cost/latency note / B cost/latency only / C subjective demo only | unresolved (rec → **A**) |
| Q6 | Eval spend ceiling | A ≤ few USD / hard stop / B no cap / C local-mock only (no Vertex bill) | unresolved (rec → **A**) |
| Q7 | Where Vertex runs in eval | A offline/script against APIs (not production Cloud Run cutover) / B optional flag on Cloud Run behind IAP | unresolved (rec → **A**) |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | 004 = **evaluation** Feature; no immediate production cutover | Spec draft | 2026-09-05 |
| D1 | Keep Local/OpenCLIP path; do not remove in 004 | Spec draft | 2026-09-05 |
| D2 | Domain stays GCP-agnostic (Ports & Adapters) | Spec draft | 2026-09-05 |
| D3 | 002+003 merged; IAP before broad exposure — satisfied to start eval | Human context | 2026-09-05 |

## Unresolved items

Agents must not guess answers for Q1–Q7 (affect Goal, Constraints, AC).
**Stop for human lock** (accept recommendations or override).

-
