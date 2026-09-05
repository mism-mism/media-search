# Tasks: 002-gcp-deployment

## T001 — Ports for media bytes (GCS-ready)

- [ ] Introduce/confirm port for reading/writing media bytes + listing import
      root semantics so Application does not depend on local `Path` for GCS.
- [ ] Keep Local filesystem adapter for 001 path.
- AC: AC4 (direction), enables AC2–AC3

## T002 — GCS adapters + wiring

- [ ] GCS media storage/source adapter (google-cloud-storage).
- [ ] Composition: env switch Local vs GCS; stream `/media` + thumbnails.
- [ ] Import path works with GCS-backed layout (document operator upload).
- AC: AC2, AC3, AC4

## T003 — sqlite persistence strategy on Cloud Run

- [ ] Implement chosen plan option (prefer GCS DB sync).
- [ ] Document re-import / sync behavior.
- AC: AC2

## T004 — Container image for Cloud Run

- [ ] Ensure Dockerfile (semantic profile) suitable for Cloud Run (port, memory
      guidance, model cache dirs).
- [ ] Health endpoint remains cheap enough for probes where possible.
- AC: AC1

## T005 — Terraform (minimal)

- [ ] `infra/` (or `terraform/`): APIs enable, Artifact Registry, GCS bucket,
      SA + IAM, Cloud Run service skeleton, outputs (URL, bucket, repo).
- [ ] Example `tfvars` / README; no secrets in repo.
- AC: AC1, AC6

## T006 — GitHub Actions CD

- [ ] `workflow_dispatch` workflow: auth (WIF preferred), build/push, deploy
      Cloud Run with needed env/secrets.
- [ ] Document required GitHub/GCP setup.
- AC: AC1, AC6

## T007 — Deploy smoke script + docs

- [ ] Script: health + one semantic search against `BASE_URL`.
- [ ] `docs/run-gcp.md` (apply, dispatch, upload, import, smoke).
- [ ] Update ARCHITECTURE capability table for 002 choices.
- AC: AC1, AC5, AC7 prep

## T008 — Outer convergence

- [ ] pre-implement / implement / post-implement / reviews (full) / pre-merge.
- AC: AC5–AC7
