# Plan: 002-gcp-deployment

## Approach

Keep Domain/Application intact. Add GCP adapters + composition wiring switched
by config (e.g. `MEDIA_BACKEND=gcs`, `DB` path). Provision with Terraform;
deploy with GitHub Actions `workflow_dispatch`.

## Service map

| Capability | 002 choice |
|------------|------------|
| Runtime | Cloud Run |
| Media | GCS |
| Metadata + vector | sqlite + sqlite-vec (persist via GCS object sync or mounted strategy — pick simplest durable demo in T00x) |
| Embedding | OpenCLIP in container (`EMBEDDER=local`) |
| Preview | Stream via app from GCS |
| Auth | None (v0) |
| IaC | Terraform (minimal) |
| CD | Actions `workflow_dispatch` → AR → Cloud Run |
| Env | Single GCP project |

## Persistence note (sqlite on Cloud Run)

Cloud Run local disk is ephemeral. Plan options (choose one in tasks, prefer
simplest that meets AC2/AC3 across redeploy):

1. **GCS sync**: download DB at start / upload after import (operator OK).
2. **Single-instance + GCS FUSE** (if acceptable complexity).
3. Document “re-import after deploy” as interim if (1) lands first — only if
   AC still satisfiable for demo.

Prefer (1) unless blocked.

## Contracts

- Ports: extend/add `MediaStoragePort` / media bytes access used by import +
  `/media` (Local FS vs GCS).
- Env: `GCS_BUCKET`, `GOOGLE_CLOUD_PROJECT`, DB path, `EMBEDDER=local`.
- Terraform outputs: service URL, bucket name, AR repo.
- Workflow inputs: project, region, image tag (defaults OK).

## Verify

| Gate | Role |
|------|------|
| `./scripts/verify` | Deterministic / Fake-capable |
| `./scripts/semantic-real` | Required semantic (local) |
| Deploy smoke | Required for 002: `GET /health` + `GET /api/search?q=…` against Cloud Run URL (manual or script with creds; CI may need secrets — document) |

## Risks

- Cold start + OpenCLIP model download on Cloud Run (memory/CPU/timeout).
- sqlite durability across revisions.
- WIF setup friction vs JSON key temptation (forbid keys in git).
