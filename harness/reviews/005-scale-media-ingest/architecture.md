---
reviewer_role: architecture
feature: 005-scale-media-ingest
verdict: PASS
---

# Architecture: 005

## Verdict: PASS

```text
UI → ImportJobPort → (Local thread | Cloud Run Job)
                 → ImportLockPort (single writer)
                 → ImportDirectory + FrameStorePort
                 → sqlite-vec + GCS DB sync
```

DIP upheld: `google.cloud` only in adapters (`gcs_*`, `import_jobs.CloudRun*`).
Search contract unchanged. ARCHITECTURE.md updated for Job + GCS frames.

## Residual

- GCS lock is best-effort (TTL), not Chubby; adequate for single-team v0.
