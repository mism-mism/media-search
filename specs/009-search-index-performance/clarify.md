# Clarify: Search + index performance

## Ambiguities

Operators report **search too slow** and **indexing / Import too slow**.
Root causes overlap (in-process OpenCLIP on Cloud Run CPU) but fixes differ
(query path vs Job throughput vs always-on capacity).

### Diagnosis (current architecture)

| Path | Bottleneck |
|------|------------|
| Search (cold) | Cloud Run scale-to-zero + first OpenCLIP load (large `xlm-roberta` tower) |
| Search (warm) | Every query: CPU `embed_text` / `embed_image`; text path also `list_all` substring scan |
| Index (Import Job) | Sequential per-asset `embed_image`; videos = ffmpeg + up to 3 embeds; GCS IO; single-writer DB |
| Shared | One CPU OpenCLIP in service **and** Job; no query-embedding cache; Lazy load on first use |

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| P1 | Priority vs 008 | A **009 performance first** / B 008 first / C parallel tracks | resolved → **A** |
| Q1 | Warm search target | A **p95 &lt;1s** / B &lt;2s / C ~half of today | resolved → **A** |
| Q2 | Cold search | A **min-instances=1** (pay to stay warm) / B cold OK if warm meets Q1 / C both cold+warm aggressive | resolved → **A** |
| Q3 | Search fix depth (phase 1) | A **ops+cache+SQL text match** (no model change) / B A + evaluate smaller OpenCLIP / C redesign embedder service | resolved → **A** |
| Q4 | Index throughput target | A **≥3×** images/min vs baseline on same Job shape / B ≥2× / C “feels faster” only | resolved → **A** |
| Q5 | Index fix depth (phase 1) | A **pipeline + single-writer queue + Job size** / B A + fewer video frames option / C multi-Job sharded index (new design) | resolved → **A** |
| Q6 | Quality bar | A no intentional semantic regression on fixed smoke queries / B allow smaller model if latency wins | resolved → **A** |
| Q7 | Profile | A lean / B **full** | resolved → **B** |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | 009 covers **both** search latency and Import indexing speed | Human | 2026-09-06 |
| D1 | Do **009 before 008** | Human | 2026-09-06 |
| D2 | Warm search target: **p95 &lt;1s** | Human | 2026-09-06 |
| D3 | Cold mitigation: **min-instances=1** + eager OpenCLIP load at startup | Human | 2026-09-06 |
| D4 | Phase 1 search: ops + query embed cache + SQL text match; **keep current model** | Human | 2026-09-06 |
| D5 | Indexing target: **≥3×** images/min vs measured baseline | Human | 2026-09-06 |
| D6 | Phase 1 index: IO/embed pipeline + single-writer queue + Job CPU/mem tune | Human | 2026-09-06 |
| D7 | No deliberate semantic downgrade in phase 1 | Human | 2026-09-06 |
| D8 | profile = **full** | Human | 2026-09-06 |

## Unresolved items

None for Domain / Constraints / Acceptance Criteria (phase 1).
