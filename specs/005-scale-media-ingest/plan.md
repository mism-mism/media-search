# Plan: Scale media ingest (10k + video)

Clarify D1–D10 locked. Profile **full**.

## Architecture

```text
UI / POST /api/import
        │  enqueue only (fast)
        ▼
  ImportJobPort ──Local──► in-process thread/subprocess (dev)
               ──GCP────► Cloud Run Job (same image, IMPORT_MODE=worker)
        │
        ▼
  single-writer lock (GCS object lease or DB flag in state/)
        │
        ▼
  ImportDirectory (existing) + OpenCLIP
        │
        ├─ sqlite-vec mutate → upload gs://…/state/*.db
        └─ frame JPEGs → gs://…/frames/…  (new; fix 002 residual)
```

Search path unchanged: OpenCLIP query embed + sqlite-vec KNN + asset collapse.

## Domain / ports

| Port | Change |
|------|--------|
| `ImportJobPort` (new) | `enqueue() → job_id`, `get(job_id) → status/progress/error` |
| `ImportLockPort` (new) | acquire/release single-writer |
| `FrameStorePort` (new or extend MediaStorage) | put/get frame JPEG by `frame_key` |
| `ImportDirectory` | write frames via FrameStore; emit progress callbacks |
| Domain | unchanged search contract / frame grain |

Local adapters: filesystem lock file + background thread + local frame dir  
GCP adapters: Cloud Run Jobs API + GCS lock object + GCS frame prefix

## Dependency direction

```text
Domain ← Application ← API
                ↓ ports
         adapters (local | gcs | run_jobs)
```

No `google.cloud` in Domain/Application.

## Terraform / ops

- Cloud Run **Job** resource (same image as service; command/env `IMPORT_MODE=worker`)
- SA permissions: run.jobs.run, GCS read/write on media + state + frames
- Env: `IMPORT_JOB_NAME`, `FRAME_GCS_PREFIX` / reuse bucket prefixes
- Docs: `docs/run-gcp.md` (+ optional `run-gcp-scale.md`) — 10k ingest procedure

## UI / API

| Endpoint | Behavior |
|----------|----------|
| `POST /api/import` | Enqueue job; **409** if lock held (or return existing running job id) |
| `GET /api/import/status` or `/api/import/jobs/{id}` | status, counts, error |
| `GET /api/stats` | keep totals (AC5) |
| UI Import button | poll status until terminal |

Local/dev: enqueue may run worker in-process so `docker compose` / pytest stay simple.

## Tests

| Layer | Coverage |
|-------|----------|
| Unit | lock acquire/conflict; job status state machine; frame store round-trip |
| Integration | import → frames on store → search bestFrame URL resolves after “cold” frame_root wipe |
| API | enqueue 202/200; second enqueue 409/queued; status fields |
| GCP smoke (manual/doc) | Job run + scale-to-zero + thumb still 200 |

Deterministic tests use FakeEmbedder. No Vertex.

## Risks

| Risk | Mitigation |
|------|------------|
| Job image/env drift from service | Same Artifact Registry image; shared env via TF |
| Long Job + OpenCLIP CPU | Document expected wall time; Job timeout high enough |
| Lock stuck after crash | TTL / heartbeat on GCS lease |
| sqlite writer from web during Job | Web import path only enqueues when `MEDIA_BACKEND=gcs` |
| 10k wall clock | Differential + progress; smoke on subset + documented full run |

## Task decomposition

See `tasks.md` (T010–T080).
