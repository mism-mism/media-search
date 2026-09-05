---
reviewer_role: product-reviewer
reviewer_id: product-review-subagent
---

# Product review: 002-gcp-deployment

## Verdict

**PASS**

Adapter-swap + Terraform/CD/docs/smoke deliver the same search product on GCP
paths; AC5 treats deployed smoke as Required manual/local-with-creds (no CI
SKIP-as-PASS). Human “usable” (AC7) still pending operator judgment.

## Scope checked

- `specs/002-gcp-deployment/spec.md` (+ `clarify.md`)
- Ports/adapters: `MediaStoragePort`, `LocalMediaStorage`, `GcsMediaStorage`,
  `gcs_db_sync`; composition in `main.py` / `api/app.py`
- IaC/CD: `infra/terraform/`, `.github/workflows/deploy-gcp.yml`
- Ops: `docs/run-gcp.md`, `scripts/gcp-smoke`
- Sibling Inner: `harness/reviews/002-gcp-deployment/test.md` (pytest 20/1 skip)

## AC-by-AC

| AC | Verdict | Evidence |
|----|---------|----------|
| **AC1** TF apply + `workflow_dispatch` → Cloud Run URL (API + UI) | **PASS** | `docs/run-gcp.md` §1–2; `infra/terraform/main.tf` (AR, GCS, SA, optional Cloud Run + public invoker); `deploy-gcp.yml` builds `INSTALL_SEMANTIC=1`/`INSTALL_GCP=1`, pushes AR, `gcloud run deploy` with env; app still serves `/` UI + `/health` + `/api/*`. Live URL not exercised in this review (creds-gated). |
| **AC2** GCS import + Real Local search; empty `q`→400; filters as 001 | **PASS** | Empty-path `POST /api/import` → `execute_storage(storage)`; GCS via `MEDIA_BACKEND=gcs` + `GcsMediaStorage`; `EMBEDDER=local` in TF/CD; upload/import documented in `run-gcp.md` §3. Empty `q` / tags AND / `media_type` unchanged from 001 (hermetic suite per sibling `test.md`). No live GCS pytest — acceptable; cloud proof owned by smoke (AC5). |
| **AC3** `/media` + video bestFrame thumbs vs GCS-backed storage | **PASS** (with residual) | `/media` uses `storage.open_stream` → GCS bytes via `StreamingResponse`. Thumbs still `/thumbnails/{frame_key}` from local `frame_root` written at import (`materialize` + ffmpeg) — works on the importing instance after import. **Residual:** frame JPEGs are not GCS-synced; Cloud Run ephemeral disk + scale-to-zero can 404 thumbs until re-import (DB sync covers index, not frame files). |
| **AC4** Domain/Application zero GCP SDK imports | **PASS** | `google.cloud` only in `adapters/gcs_media_storage.py` and `adapters/gcs_db_sync.py` (+ composition root lazy import). Domain / Application / ports clean. (Sibling architecture notes Application→`LocalMediaStorage` DIP leak — out of AC4’s GCP-SDK wording; not a product-contract break for search behavior.) |
| **AC5** Local verify + semantic-real; deployed smoke honest when no project | **PASS** | Local gates remain `FEATURE=002-gcp-deployment ./scripts/verify` + `./scripts/semantic-real` (`run-gcp.md` §4). `scripts/gcp-smoke` = health + one search against `BASE_URL`. Not wired into `.github/workflows/verify.yml` — no silent SKIP pretending cloud PASS. Live smoke not run here (manual/creds-gated as AC allows). |
| **AC6** Terraform + CD in-repo (not docs-only) | **PASS** | Real `infra/terraform/main.tf` + `terraform.tfvars.example`; real `deploy-gcp.yml` with WIF secrets (no keys in repo). |
| **AC7** Full-profile reviews + human “usable” | **PARTIAL** | This artifact + concurrent Outer only; **human GCP-deploy usable judgment not recorded** in this review. Do not treat product PASS as AC7 human sign-off. |

## Out of scope check

| Out of scope | Respected? |
|--------------|------------|
| Vertex AI Vector Search / multimodal embeddings | **Yes** — OpenCLIP in Run; docs say Vertex deferred |
| GKE, multi-env, IAP/Identity Platform | **Yes** — single env, `--allow-unauthenticated` |
| Auto-deploy on every `main` push | **Yes** — `workflow_dispatch` only |
| Custom ANN; Domain rewrite for cloud APIs | **Yes** — sqlite-vec + port/adapters |
| Multi-cloud | **Yes** — GCP only |

## Product intent / silent invention

No keyword search, auth product, or Vertex path invented. Same semantic `q` +
filters + `/media` preview; Local path default preserved (`MEDIA_BACKEND=local`).

## Residual risks (non-blocking for this PASS)

1. Human AC7 “usable” after real deploy still required for Outer convergence.
2. Video thumbnail durability across Cloud Run instance recycle without re-import.
3. No hermetic mocked GCS adapter tests (sibling test residual).
4. Application `LocalMediaStorage` coupling (architecture FAIL) — fix before
   treating DIP as closed; does not block observed GCS import/`/media` path.

## Recommendation

Product behavior for 002 adapter-swap/deploy path is **acceptable to ship**
subject to operator-run `gcp-smoke` + human usable judgment and remaining
full-profile Outer / architecture DIP follow-up.
