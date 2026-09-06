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

## Scale ingest (005)

| Piece | Choice |
|-------|--------|
| Heavy Import | Cloud Run **Job** `media-search-import` (UI enqueues) |
| Single writer | GCS lock object `state/import.lock.json` |
| Frame thumbs | GCS prefix `frames/` (survive scale-to-zero) |
| Job status | GCS `state/import-jobs/*.json` |
| Embedder | OpenCLIP (unchanged) |

### Operator flow (~10k)

1. Upload media to `gs://$BUCKET/incoming/` (images + videos).
2. Open the IAP UI → **Import** (or `POST /api/import` with empty path).
3. Poll `/api/import/jobs/{id}` / UI status until `succeeded`.
4. Search as usual; video thumbs come from GCS frames.
5. Overlapping Import → **409** until the lock clears.

Local/dev without Job: omit `CLOUD_RUN_IMPORT_JOB` — Import runs on a
background thread (set `IMPORT_SYNC=1` for inline tests).

Worker entrypoint: `python -m media_search.worker_import` (Job command).

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

Everyday local rebuild (amd64 → Artifact Registry → Cloud Run + Import Job):

```bash
make deploy
# optional tag: make deploy IMAGE_TAG=005-006
```

Or GitHub Actions → **deploy-gcp** → Run workflow → enter `project_id` / `region` / tag.

The workflow / `make deploy` builds with `INSTALL_SEMANTIC=1`, `INSTALL_GCP=1`, and
`PREWARM_OPENCLIP=1` (CPU torch wheels — CUDA wheels OOM on Cloud Run), pushes
to `media-search-repo`, and deploys Cloud Run env for GCS.

Service (018): `--min=0 --min-instances=0 --cpu-throttling` allows scale-to-zero
and request-based billing. Both service and revision minimums are zero in local
and GitHub deploy commands and Terraform. CLI deployments set service and revision
maximums to one (`--max=1 --max-instances=1`), matching the subsequent user Console
setting. Terraform sets revision maximum one, but its Google 6.x provider cannot
declare the service-level maximum; a Terraform service update is not guaranteed
to preserve that separate setting. After such an update, reapply it explicitly:

```bash
gcloud run services update media-search --project=laperm-507708 \
  --region=asia-northeast1 --max=1
```

These are configured autoscaling limits, not a hard billing cap. This replaces
the always-warm 009 policy. The URL stays available: a request automatically starts an instance when
none is running. The first request after an idle period waits for container,
OpenCLIP and index startup; subsequent requests can reuse the warm instance.
Cloud Run controls idle shutdown timing, so zero minimum is not an immediate
stop command or a promise that no instance will ever remain temporarily idle.
GCS keeps media, index snapshots and job status across restarts.

Import Job remains 4 CPU / 16Gi with `IMPORT_EMBED_WORKERS=4`, running only when
invoked. The web service continues to enqueue this separate Job, so request-based
CPU allocation does not suspend the import after the HTTP response completes.

See [Cloud Run minimum instances](https://cloud.google.com/run/docs/configuring/min-instances)
and [billing settings](https://cloud.google.com/run/docs/configuring/billing-settings).

## Cost controls (013)

GCP **Billing budgets alert; they do not hard-stop charges.** 013 wires a
monthly project budget (Terraform + live `gcloud` create):

| Setting | Locked value |
|---------|----------------|
| Amount | **USD 50** / calendar month |
| Thresholds | 50% / 90% / 100% of current spend |
| Notify | `mishima0304@gmail.com` (Monitoring email channel) |

```bash
# terraform.tfvars (gitignored):
# billing_account    = "01XXXX-XXXXXX-XXXXXX"
# monthly_budget_usd = 50
# budget_alert_email = "mishima0304@gmail.com"

cd infra/terraform && terraform apply
# or one-shot:
# gcloud billing budgets create --billing-account=… --budget-amount=50USD …
```

Caller needs **Billing Account** permission to create budgets.

**Email channel:** confirm the Monitoring notification channel verification mail
if Google sends one (alerts will not deliver until verified).

Main cost drivers today: Cloud Run request processing/startup time, Import Job
execution, image annotation calls, GCS storage/egress, Artifact Registry storage,
and occasional BigQuery eval. Scale-to-zero removes the always-on compute floor;
it does not make total billing zero. The budget remains alert-only. Raise
`monthly_budget_usd` when the alert is too tight — do not disable billing from
automation in this repo.

Dockerfile is **multi-stage** (`deps` → `models` → `runtime`): torch/OpenCLIP
install and HF weight bake are cached unless `pyproject.toml` / embedder code
changes, so app-only edits rebuild much faster.

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

**Do not cut over to production without IAP** (Feature 003). Prefer
`allow_unauthenticated=false` + browser smoke with your allowlisted Gmail.
See [`run-gcp-iap.md`](run-gcp-iap.md).


## Japanese image tags

See [image auto-tags setup and testing](image-auto-tags.md) for Gemini IAM, import limits,
existing-image enrichment, and enable/disable settings. Vectors remain OpenCLIP.
