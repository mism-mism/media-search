# Clarify: BigQuery Vector Search evaluation

## Ambiguities

Human interest (2026-09-06): BigQuery vector search vs GCS-synced sqlite.
Round 1 locked same day.

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | 011 scope | A **eval + go/no-go only** / B spike / C cutover | resolved → **A** |
| Q2 | What moves to BQ | A BYO only / B BQ embed only / C **both compared** | resolved → **C** |
| Q3 | Interactive latency | A **warm p95 &lt;1s** or no-go for UI default / B &lt;3s / C UI stays sqlite | resolved → **A** |
| Q4 | vs 004 | A **keep: no Vertex interactive default; BQ batch OK to eval** / B reopen / C non-Vertex only | resolved → **A** |
| Q5 | Corpus | A 004-like / B product_id sample / C **both** | resolved → **C** |
| Q6 | Spend | A **≤ few tens USD** / B no cap / C dry-run | resolved → **A** |
| Q7 | Profile | A lean / B **full** | resolved → **B** |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | 011 = BigQuery Vector Search **evaluation** | Human | 2026-09-06 |
| D1 | Eval + go/no-go only — no production cutover | Human | 2026-09-06 |
| D2 | Compare **BYO OpenCLIP→BQ** and **BQ/Vertex embed** paths | Human | 2026-09-06 |
| D3 | Interactive default requires warm p95 &lt;1s; else no-go for UI cutover | Human | 2026-09-06 |
| D4 | Keep 004 spirit: no Vertex as Cloud Run interactive default | Human | 2026-09-06 |
| D5 | Corpus: 004-like set **and** product_id sample when available | Human | 2026-09-06 |
| D6 | Spend ceiling ≈ **few tens USD** | Human | 2026-09-06 |
| D7 | profile = **full** | Human | 2026-09-06 |

## Unresolved items

None for Domain / Constraints / Acceptance Criteria.
