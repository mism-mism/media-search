# 009 — Search + index performance

Date: 2026-09-06  
Clarify: D1–D8 locked (warm p95 &lt;1s; min-instances=1; ≥3× index throughput target).

## Changes shipped

| Area | Change |
|------|--------|
| Search ops | Cloud Run `min-instances=1`, `--no-cpu-throttling`; Terraform `min_instance_count=1`, `cpu_idle=false` |
| Search warm | Lifespan + worker call `SearchMediaAssets.warm()` (eager OpenCLIP after PORT bind) |
| Search cache | `CachingEmbedder` LRU for text/image query vectors |
| Search text | `MetadataRepositoryPort.search_text` (sqlite `LIKE`, in-memory mirror) — no full `list_all` |
| Index | Thread pool embed (`IMPORT_EMBED_WORKERS`, default 4) + serial sqlite/frame upserts |
| Job size | 4 CPU / 16Gi; env `IMPORT_EMBED_WORKERS=4` |

Model identity unchanged (OpenCLIP `xlm-roberta-base-ViT-B-32` / laion5b).

## Hermetic evidence

`make test` includes `tests/test_performance_009.py`:

- Text cache hit equivalence
- sqlite `search_text` substring
- Search use case calls `search_text` (not `list_all`)
- Parallel import (4 workers) faster than sequential under artificial embed sleep (≥3× class speedup locally)

## Production measurement (fill after deploy)

Method:

1. Warm: hit `/health` then time `GET /api/search?q=…` ×20 (p95).
2. Cold: after scale event (if any) — with min-instances=1 should be rare.
3. Index: upload N new images → Import Job; images/min = N / wall_seconds.

| Metric | Baseline (pre-009) | After |
|--------|--------------------|-------|
| Warm search p95 | _(operator: multi-second)_ | _TBD after `make deploy`_ |
| Import images/min | _TBD_ | _TBD_ |

Target: warm p95 &lt;1s; import ≥3× baseline images/min.
