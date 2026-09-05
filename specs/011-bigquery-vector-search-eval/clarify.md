# Clarify: BigQuery Vector Search evaluation

## Ambiguities

Human interest (2026-09-06): [BigQuery vector search intro](https://docs.cloud.google.com/bigquery/docs/vector-search-intro)
looks promising for durable scale vs GCS-synced sqlite. Need Round 1 lock on
**what to evaluate** (search vs embed-only) and relationship to **004 Vertex
no-go** before any spike.

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | 011 scope | A **eval + go/no-go only** / B eval + non-default adapter spike / C implement cutover | unresolved → rec **A** |
| Q2 | What moves to BQ first? | A search + index only (BYO vectors) / B embed+index via `AI.GENERATE_EMBEDDING` / C **both passes compared** | unresolved → rec **C** |
| Q3 | Interactive search latency bar | A warm p95 &lt;1s must hold on BQ / B &lt;3s OK / C batch/analytics OK, UI stays sqlite | unresolved → rec **A** (fail BQ for UI if missed) |
| Q4 | vs 004 Vertex no-go | A keep: no Vertex as Cloud Run default; BQ batch embed OK to eval / B reopen Vertex for interactive / C BQ only with non-Vertex vectors | unresolved → rec **A** |
| Q5 | Corpus | A current ~18 + fixed queries (004-like) / B library sample with product_id / C both | unresolved → rec **C** |
| Q6 | Spend ceiling | A **≤ few tens USD** / B no cap / C dry-run docs only | unresolved → rec **A** |
| Q7 | Profile | A lean / B **full** | unresolved → rec **B** |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | Ticket 011 as **evaluation** of BigQuery Vector Search vs current path | Human | 2026-09-06 |

## Unresolved items

Lock Round 1 (Q1–Q7) before implementation.

Recommended package: **A C A A C A B**

- **D1** Eval + go/no-go only
- **D2** Compare (i) BYO OpenCLIP vectors in BQ and (ii) BQ/Vertex embed path
- **D3** UI path must still meet warm p95 &lt;1s or BQ is no-go for interactive default
- **D4** Keep 004 spirit: no Vertex as Cloud Run interactive default; batch-via-BQ may be evaluated
- **D5** Corpus = 004-like set **and** a product_id library sample if available
- **D6** Spend ≤ few tens USD
- **D7** profile = full
