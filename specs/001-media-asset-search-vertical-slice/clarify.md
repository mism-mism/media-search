# Clarify: Media Asset Search Vertical Slice (Local-first)

## Ambiguities

Resolved in grilling (2026-09-05). Product/Architecture/Spec split agreed.

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | 2-day end point | A Phase4 local / B Phase5 / C Phase6 | resolved → A |
| Q2 | SoR for constraints | A prompt / B docs / C 001 only / D docs+001+prompt summary | resolved → D |
| Q3 | GCP fixation strength | A vendor only / B +capability map / C soft | resolved → A |
| Q5 | Container ownership | A in 001 thin / B separate feature / C with GCP / D optional | resolved → A |
| Q6 | DIP proof in 001 | A review+deps / B dual Local / C FakeGcp / D defer all | resolved → A |
| Q7 | Vector in v0 vs ban | A withdraw ban / B local-only allow / C defer vector / D throwaway | resolved → B |
| Q8 | “Build vector DB” meaning | A reuse engine / B custom engine / C A then B / D research B | resolved → A |
| Q9 | Embedding local strategy | A fake only / B real only / C fake then real / D cloud API | resolved → C |
| Q10 | Search UX shape | A fusion / B modes / C semantic+filters / D semantic only | resolved → C |
| Q11 | Video embedding | A rep frames (multi) / … | resolved → A multi-frame collapse to MediaAsset |
| Q12 | Metadata depth | A+B technical + human tags | resolved → A+B |
| Q13 | Semantic AC | C golden automated + Outer human | resolved → C |
| Q14 | Container done | C model not baked; network for first fetch OK | resolved → C |
| Q15 | Engine pick timing | B after Domain in plan | resolved → B |
| Q16 | Repo start order | A adopt→docs→001 | resolved → A |
| Q17 | Frame count rule | C N=3 constant | resolved → C |
| Q18 | Video collapse | B max + bestFrame | resolved → B |
| Q19 | Surface | A API+minimal UI | resolved → A |
| Q20 | Import entry | A directory batch | resolved → A |
| Q21 | Source reachability | B HTTP preview | resolved → B |
| Q22 | Profile | B full | resolved → B |
| Q23 | Formats | A JPEG/PNG/MP4 H.264 | resolved → A |
| Q24 | Short video | B T=5s → 1 middle else max 3 | resolved → B |
| Q25 | Filters | C mediaType + tags | resolved → C |
| Q26 | Re-import | A upsert by relative path | resolved → A |
| Q27 | Unsupported | A skip+warn+summary | resolved → A |
| Q28 | Embedder switch | C env/config + fake tests / real default | resolved → C |
| Q29 | Real in CI | B separate job but Required for 001; no silent SKIP | resolved → B+ |
| Q30 | bestFrame visibility | B optional on detail | resolved → B |
| Q31 | Auth | A none | resolved → A |
| Q32 | Keyword word | A remove keyword from 001 | resolved → A |
| Q33 | T seconds | B 5s | resolved → B |
| Q34 | Golden size | A K=5, 8–12 queries | resolved → A |
| Q35 | Thumbnail | A bestFrame-derived for video | resolved → A |
| Q36 | Stack timing | B in Architecture | resolved → B |
| Q37 | Prompt depth | A skeleton only | resolved → A |
| Q38 | 002 promise | B PRODUCT boundary; no specs/002 yet | resolved → B |
| Q39 | Multi tags | A AND | resolved → A |
| Q40 | Empty q | A 400 | resolved → A |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D1 | Local-first / GCP vendor-only / Domain knows neither | Human + grill | 2026-09-05 |
| D2 | 001 local slice + thin container; 002 GCP swap; no GCP service pick before 001 convergence | Human | 2026-09-05 |
| D3 | Local vector search required; single-runtime existing engine; no managed mega-vector in 001 | Human | 2026-09-05 |
| D4 | Semantic + mediaType/tags(AND); q required; no keyword; video multi-frame→MediaAsset max/bestFrame | Human | 2026-09-05 |
| D5 | Profile full; Fake≠semantic PASS; semantic-real Required separate gate | Human | 2026-09-05 |
| D6 | Shared understanding locked (4-layer decision log) | Human | 2026-09-05 |

## Unresolved items

- None

## Plan-time selections (resolved 2026-09-05)

- Runtime: Python 3.12+ / FastAPI → `docs/ARCHITECTURE.md`
- Local vector engine: SQLite + sqlite-vec → `plan.md`
- Semantic-real model: OpenCLIP `xlm-roberta-base-ViT-B-32` / `laion5b_s13b_b90k` → `plan.md` / Architecture
- 002 candidate (not selected): Vertex AI Vector Search / multimodal embeddings
