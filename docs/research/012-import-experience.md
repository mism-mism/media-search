# 012 — Import experience

Date: 2026-09-06  
Clarify: D0–D6 locked (single-add priority; incremental + skip fix; ≥3× hermetic;
OpenCLIP unchanged; DB reload after Job; profile full).

## Changes

| Area | Change |
|------|--------|
| Skip logic | Unchanged only if **size match and `has_frames`** — Library upload no longer stuck without vectors |
| Cheap skip | `MediaStoragePort.size_bytes` avoids materialize/download when skipping |
| Scoped jobs | `ImportJobRecord.only_keys`; Library `upload` / `upload_many` enqueue new asset ids only |
| Search freshness | On Job SUCCEEDED poll, service `reload_db` (GCS download + sqlite conn swap) |

Model / Job size / GPU: unchanged (D4 / Q2=A).

## Hermetic evidence

`tests/test_import_experience_012.py`:

- metadata-without-vectors embeds
- unchanged+vectors skips
- `only_keys` scopes work
- scoped single embed ≥3× faster than re-embedding N=24 with slow FakeEmbedder

`tests/test_db_reload_012.py`: connection swap after “remote” DB replace.

## Residual (production)

Cloud Run **Job cold start** + OpenCLIP warm on each Job still dominate absolute
wall clock for tiny adds. 012 removes full-corpus materialize and the skip bug;
further wins need Job warm pool / smaller model (out of scope).
