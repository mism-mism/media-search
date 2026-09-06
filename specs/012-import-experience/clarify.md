# Clarify: Import experience

## Ambiguities

Operators say **Import after upload feels long**. 009 already added parallel
embed workers (default 4) + larger Job (4CPU/16Gi). Remaining pain is mostly:

| Factor | Today |
|--------|--------|
| Job cold start | Each Import = new Cloud Run Job execution (service `min-instances=1` does **not** warm Jobs) |
| Model warm on Job | Worker `warm()` OpenCLIP every execution |
| Full corpus touch | Every Import `list_media_keys()` + **materialize every object**; size-match only skips **embed** |
| Library upload skip bug | Upload writes metadata with `size_bytes` **before** Job; worker treats size-match as `unchanged` and may **never embed** new Library assets |
| Search freshness | Job uploads sqlite to GCS; service with `min-instances=1` may keep **stale local DB** until recycle |

009 phase 1 did **not** ship true only-new indexing or Job warm pool.

## Questions

| ID | Question | Options | Status |
|----|----------|---------|--------|
| Q1 | Primary outcome for 012 | A upload→searchable / B full reimport / C **A優先、Bは副次** | resolved → **C** |
| Q2 | Phase 1 depth | A **正しい差分 + skip 修正** / B A + Job 起動短縮 / C B + 小さめモデル or GPU | resolved → **A** |
| Q3 | Success bar (A向け) | A **単画像追加 Import wall ≥3×短縮** / B p95 &lt;30s / C 体感のみ | resolved → **A** |
| Q4 | Model / hardware in 012 | A **現状 OpenCLIP** / B 小さめ評価 / C GPU | resolved → **A** |
| Q5 | Job 後の検索鮮度 | A **サービスが Job 完了後に DB 再取得** / B recycle 可 / C 別ストア | resolved → **A** |
| Q6 | Profile | A lean / B **full** | resolved → **B** |

## Decisions

| ID | Decision | Decided by | Date |
|----|----------|------------|------|
| D0 | 012 = Import **体験**改善（検索 warm は 009 済み） | Human | 2026-09-06 |
| D1 | 単発 upload→searchable 優先；全量は副次 | Human | 2026-09-06 |
| D2 | Phase 1: 正しい差分（未ベクトル/変更のみ）+ Library skip 修正；Job warm / モデル変更は出さない | Human | 2026-09-06 |
| D3 | 成功基準: 単画像追加の Import wall を現状比 **≥3×**（同 Job 形） | Human | 2026-09-06 |
| D4 | 本番 embedder は現状 OpenCLIP のまま | Human | 2026-09-06 |
| D5 | Job 成功後、サービスが DB を再取得して検索に反映 | Human | 2026-09-06 |
| D6 | profile = **full** | Human | 2026-09-06 |

## Unresolved items

None for Domain / Constraints / Acceptance Criteria.
