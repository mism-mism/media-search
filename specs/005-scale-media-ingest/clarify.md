# Clarify: Scale media ingest (10k + video)

## Ambiguities

001–003 proved semantic search on a tiny corpus with synchronous Import on
Cloud Run + OpenCLIP + sqlite-vec. Scaling to ~10k mixed image/video with
**team UI Import** changes timeouts, concurrency, thumbnail durability, and
operator UX — without changing the product search contract (`q` + filters).

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | Corpus mix at target | A images-heavy, few videos / B images **and** videos both thousands–~10k | resolved → **B** |
| Q2 | Who imports | A solo occasional batch / B **team via UI on demand** | resolved → **B** |
| Q3 | Search latency bar | A **few seconds OK** (keep current OpenCLIP path) / B need much faster | resolved → **A** |
| Q4 | Video index grain | A **representative frames** (current) / B fine time-sliced / native video embed | resolved → **A** |
| Q5 | Heavy Import execution | A long Cloud Run request / B **Cloud Run Job** (UI enqueues) / C always-on worker | resolved → **B** |
| Q6 | Index under concurrent Import | A sqlite-vec + **single-writer lock** + GCS sync / B Cloud SQL + pgvector / C Vertex Vector Search | resolved → **A** |
| Q7 | Thumbnail / best-frame durability | A local ephemeral only / B **GCS-backed** (fix 002 residual) | resolved → **B** |
| Q8 | Embedder for 005 | A **keep OpenCLIP** / B switch Vertex default / C dual | resolved → **A** |
| Q9 | Assurance profile | A lean / B **full** | resolved → **B** |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D1 | Target corpus: **images and videos** both at thousands–~10k scale | Human | 2026-09-05 |
| D2 | Import path: **team uses UI** (on-demand), not solo-only batch | Human | 2026-09-05 |
| D3 | Search latency: **few seconds acceptable**; do not redesign for sub-second | Human | 2026-09-05 |
| D4 | Video semantics: **representative frame sampling** (001 grain); no native video-embed cutover | Human | 2026-09-05 |
| D5 | Heavy Import = UI triggers **Cloud Run Job**; HTTP only enqueues / reports status | Human (rec) | 2026-09-05 |
| D6 | Index = **sqlite-vec** + **single-writer** (+ GCS DB sync); no pgvector/VS in 005 | Human (rec) | 2026-09-05 |
| D7 | Frame thumbnails / best-frame JPEGs persisted to **GCS** | Human (rec) | 2026-09-05 |
| D8 | Embedder default remains **OpenCLIP** (004 no-go for Vertex cutover) | Human (rec) | 2026-09-05 |
| D9 | Feature profile = **full** | Human (rec) | 2026-09-05 |
| D10 | Shared understanding locked for 005 Round 1+2 | Human | 2026-09-05 |

## Unresolved items

- None
