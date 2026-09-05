# Clarify: Media library (upload + folders + search)

## Ambiguities

005 makes async Import + durable thumbs viable at ~10k. Operators still use
`gsutil` and a separate mental model for “where files live.” 006 adds a
**library UI**: virtual folders, upload, manage (delete/move/rename), and
**colocated semantic search**.

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | Media types | A images only / B **images + videos** | resolved → **B** |
| Q2 | Directory model | A GCS prefix-as-folder / B **app virtual folder DB** | resolved → **B** |
| Q3 | Management ops | A list+upload / B +delete / C **+move/rename** | resolved → **C** |
| Q4 | Search placement | A separate search page only / B **library screen colocated** | resolved → **B** |
| Q5 | Import trigger | A **auto after upload** / B explicit “index update” | resolved → **A** |
| Q6 | Timing | A **after 005 deploy** / B parallel before 005 live | resolved → **A** |
| Q7 | Folder persistence | A **sqlite** folder tables / B separate DB / C only tags | resolved → **A** |
| Q8 | Move/rename vs GCS key | A **metadata-only** / B also rename GCS objects | resolved → **A** |
| Q9 | Delete semantics | A soft-delete / B **hard delete** | resolved → **B** |
| Q10 | Profile | A lean / B **full** | resolved → **B** |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D1 | Library handles **images and videos** | Human | 2026-09-05 |
| D2 | Directories are **app-owned virtual folders** | Human | 2026-09-05 |
| D3 | Ops: browse, upload, **delete, move, rename** | Human | 2026-09-05 |
| D4 | **Semantic search colocated** on the library UI | Human | 2026-09-05 |
| D5 | Upload **auto-enqueues Import** | Human | 2026-09-05 |
| D6 | Target after 005; implement on branch that already contains 005 code | Human | 2026-09-05 |
| D7 | Folders + membership columns in **sqlite** (GCS DB sync) | Human (rec) | 2026-09-05 |
| D8 | Move/rename = **metadata only**; GCS `asset_id` stable | Human (rec) | 2026-09-05 |
| D9 | Delete = **hard** (GCS + vectors + metadata + frames) | Human (rec) | 2026-09-05 |
| D10 | profile = **full** | Human (rec) | 2026-09-05 |
| D11 | Round 1+2 locked; proceed to implement | Human | 2026-09-05 |

## Unresolved items

- None
