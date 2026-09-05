# Run on GCP (Feature 002)

Local-first 001 stays the default for development. This path deploys the **same**
stack to **Cloud Run + GCS** with Terraform + GitHub Actions.

## Architecture (002)

| Piece | Choice |
|-------|--------|
| Runtime | Cloud Run |
| Media | GCS (`MEDIA_BACKEND=gcs`) |
| Index | sqlite + sqlite-vec (synced to `gs://…/state/*.db` after import) |
| Embed | OpenCLIP in the container (`EMBEDDER=local`; CPU torch + prewarm) |
| Auth | Experiment: none. **Production: IAP** — [`run-gcp-iap.md`](run-gcp-iap.md) |
| IaC | `infra/terraform` |
| CD | `.github/workflows/deploy-gcp.yml` (`workflow_dispatch`) |

Vertex embeddings / Vector Search remain **out of scope**.

## Prerequisites

1. GCP project with billing
2. `gcloud` + Terraform ≥ 1.5 locally (for apply)
3. GitHub repo secrets for CD:
   - `GCP_WORKLOAD_IDENTITY_PROVIDER`
   - `GCP_SERVICE_ACCOUNT`  
   (Workload Identity Federation — prefer over JSON keys)

## 1. Terraform apply

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# edit project_id (leave image empty on first apply to create bucket/AR/SA only)
terraform init
terraform apply
```

Note outputs: `artifact_registry`, `media_bucket`, `service_account`.

Grant the GitHub deploy SA permission to push to Artifact Registry and deploy
Cloud Run (project IAM). Bind WIF per Google’s GitHub Actions docs.

## 2. Dispatch CD

Actions → **deploy-gcp** → Run workflow → enter `project_id` / `region` / tag.

The workflow builds with `INSTALL_SEMANTIC=1`, `INSTALL_GCP=1`, and
`PREWARM_OPENCLIP=1` (CPU torch wheels — CUDA wheels OOM on Cloud Run), pushes
to `media-search-repo`, and deploys Cloud Run env for GCS.

## 3. Upload media + import

```bash
BUCKET="$(terraform -chdir=infra/terraform output -raw media_bucket)"
gsutil cp path/to/photo.jpg "gs://${BUCKET}/incoming/"
# optional sidecar: photo.jpg.meta.json

BASE_URL="$(gcloud run services describe media-search --region=asia-northeast1 --format='value(status.url)')"
curl -X POST "${BASE_URL}/api/import"   # empty path → configured GCS storage
```

## 4. Smoke

```bash
BASE_URL=https://… ./scripts/gcp-smoke
```

Also keep Required local gates:

```bash
FEATURE=002-gcp-deployment ./scripts/verify
./scripts/semantic-real
```

## Index persistence (production)

- Media bytes live in GCS (`incoming/`).
- The search index is sqlite on the container disk, synced to
  `MEDIA_SEARCH_DB_GCS` after each Import.
- On cold start the service downloads that DB — **you do not re-Import just to
  search**.
- Default Import is **differential** (new keys only). Use `?force=true` /
  「再インデックス」only when you intentionally want to re-embed everything.

## Production vs experiment

| Mode | `allow_unauthenticated` | Use |
|------|-------------------------|-----|
| Experiment (002 v0) | `true` | Temporary public URL — **not production** |
| Production | `false` + IAP emails | See [`run-gcp-iap.md`](run-gcp-iap.md) |

**Do not cut over to production without IAP** (Feature 003). Prefer
`allow_unauthenticated=false` + browser smoke with your allowlisted Gmail.
See [`run-gcp-iap.md`](run-gcp-iap.md).

