# Clarify: Vertex embeddings / Vector Search evaluation

## Ambiguities

002/003 production path is **OpenCLIP + sqlite-vec on Cloud Run + IAP**.
Natural-language semantic search already works there. Feature **004** decides
whether managed **Vertex** adapters are worth a follow-on implementation — not
whether NL search exists.

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | What to evaluate in 004? | A embeddings API only / B Vector Search only / C both / D research-doc only | resolved → **A** |
| Q2 | Production default after 004? | A OpenCLIP default; Vertex flag / B switch if go / C follow-on only | resolved → **A** |
| Q3 | Comparison corpus | A ~18 corpus + fixed JA/EN queries / B larger private / C synthetic | resolved → **A** |
| Q4 | Languages in eval | A EN / B JA+EN / C JA | resolved → **B** |
| Q5 | Go/no-go bar | A quality ≥ OpenCLIP + cost/latency / B cost only / C demo only | resolved → **A** |
| Q6 | Eval spend ceiling | A ≤ few USD / B no cap / C mock only | resolved → **A** |
| Q7 | Where Vertex runs in eval | A offline/script (no prod cutover) / B flag on Cloud Run | resolved → **A** |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | 004 = **evaluation** Feature; no immediate production cutover | Spec draft | 2026-09-05 |
| D1 | Keep Local/OpenCLIP path; do not remove in 004 | Spec draft | 2026-09-05 |
| D2 | Domain stays GCP-agnostic (Ports & Adapters) | Spec draft | 2026-09-05 |
| D3 | 002+003 merged; IAP before broad exposure — satisfied to start eval | Human | 2026-09-05 |
| D4 | Eval slice = **Vertex multimodal embeddings API only**; keep sqlite-vec | Human (rec) | 2026-09-05 |
| D5 | Production default stays **OpenCLIP**; Vertex behind flag / follow-on | Human (rec) | 2026-09-05 |
| D6 | Corpus = current ~18 GCS/Unsplash set + fixed JA+EN query list | Human (rec) | 2026-09-05 |
| D7 | Go/no-go requires quality evidence vs OpenCLIP **and** cost/latency notes | Human (rec) | 2026-09-05 |
| D8 | Spend ceiling ≈ **few USD**; stop if exceeded | Human (rec) | 2026-09-05 |
| D9 | Run eval via **scripts / offline harness** — do not cut over prod Cloud Run | Human (rec) | 2026-09-05 |
| D10 | Clarify Round 1 locked (all recommended) | Human | 2026-09-05 |

## Unresolved items

- None
