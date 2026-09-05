# Run on GCP (Feature 002)

Local-first 001 stays the default for development. This path deploys the **same**
stack to **Cloud Run + GCS** with Terraform + GitHub Actions.

## Architecture (002)

| Piece | Choice |
|-------|--------|
| Runtime | Cloud Run |
| Media | GCS (`MEDIA_BACKEND=gcs`) |
| Index | sqlite + sqlite-vec (synced to `gs://…/state/*.db` after import) |
| Embed | OpenCLIP in the container (`EMBEDDER=local`) |
| Auth | none (v0; `--allow-unauthenticated`) |
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

The workflow builds with `INSTALL_SEMANTIC=1` and `INSTALL_GCP=1`, pushes to
`media-search-repo`, and deploys Cloud Run env for GCS.

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

## Production vs experiment

| Mode | `allow_unauthenticated` | Use |
|------|-------------------------|-----|
| Experiment (002 v0) | `true` | Temporary public URL — **not production** |
| Production | `false` + IAP emails | See [`run-gcp-iap.md`](run-gcp-iap.md) |

**Do not cut over to production until Feature 003 (IAP) has converged** and you
have verified browser login with your allowlisted Gmail.

