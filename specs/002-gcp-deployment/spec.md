---
id: "002"
status: completed
profile: full
profile_reason: "Production cloud adapter swap — Domain/ports stability, GCP services, secrets, Terraform + CD."
---

# Spec: GCP Deployment (adapter swap)

## Problem

Feature 001 proved Media Asset Search **locally**. Production needs the same
product capability on **GCP** without rewriting Domain / Application cores.

## Goal

Deploy the **same** product stack on GCP by swapping Local adapters for GCP
adapters, with first-class **Terraform** and **GitHub Actions CD**.

```text
Same Domain / Application
        │
   Port / Interface
        │
   ┌────┴─────┐
   ▼          ▼
Local (001)  GCP (002)
             Cloud Run + GCS
             OpenCLIP in runtime
             sqlite + sqlite-vec
```

## User

Single operator deploying to one GCP project (no end-user auth in 002).

## Requirements

### Locked from 001 / PRODUCT

- R1. Domain / Application must not import GCP SDKs.
- R2. Search contract unchanged: semantic `q` required; `mediaType` + tags AND.
- R3. Video → MediaAsset; max frame score + bestFrame evidence.
- R4. Fake embedder never counts as semantic PASS.
- R5. Vendor = GCP only.

### Selected service map (clarify)

- R6. Runtime: **Cloud Run** (container; include semantic deps for Real Local).
- R7. Media bytes: **GCS** via media-storage / media-source adapters.
- R8. Metadata + vectors: **sqlite + sqlite-vec** (persist strategy in plan —
  e.g. GCS-backed DB object and/or volume; must survive redeploy for demo AC).
- R9. Embedding: **OpenCLIP in Cloud Run** (001 default multilingual model).
- R10. Preview: app **streams** objects from GCS on `/media` (and thumbnails
  as in 001).
- R11. Auth: **none** for v0 (document IAM / who can invoke). Harden later.
- R12. **Terraform** provisions Artifact Registry, GCS bucket, service
  accounts/IAM, Cloud Run service (minimal modules, one env).
- R13. **GitHub Actions** CD via **`workflow_dispatch`**: build image → push
  AR → deploy Cloud Run (Workload Identity Federation preferred; document
  secrets if WIF not ready).
- R14. Docs: deploy, import path to GCS, smoke checklist.
- R15. Gates: default local verify + `semantic-real` remain Required; plus
  **deployed URL smoke** (health + one search) for 002 convergence.

## Acceptance Criteria

- AC1. Documented Terraform apply + workflow_dispatch deploy yields a public
  (or noted) Cloud Run URL serving API + minimal UI.
- AC2. Operator can place/import assets into the GCS-backed path and search
  with Real Local embedder; empty `q` → 400; filters work as 001.
- AC3. `/media` and video bestFrame thumbnails work against GCS-backed storage.
- AC4. Domain/Application have zero GCP SDK imports (architecture review).
- AC5. Local `./scripts/verify` + `./scripts/semantic-real` PASS; deployed
  smoke (health + search) PASS when credentials/project available — if project
  unavailable in CI, smoke is a **Required manual/local-with-creds** gate
  documented honestly (no silent SKIP pretending PASS).
- AC6. Terraform + CD workflow are in-repo and reviewed; no “docs only” path.
- AC7. Full-profile reviews PASS; human judges GCP deploy “usable” (AC9-style).

## Out of Scope

- Vertex AI Vector Search / Vertex multimodal embeddings (later feature)
- GKE, multi-env staging/prod split, IAP/Identity Platform
- Auto-deploy on every `main` push
- Custom ANN; Domain rewrite for cloud APIs
- Multi-cloud

## Constraints

- Prefer adapter swap; keep 001 Local path working.
- Smallest GCP surface that meets AC.
- Secrets never committed; prefer WIF over long-lived JSON keys.
- Align with [`docs/PRODUCT.md`](../../docs/PRODUCT.md) /
  [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).

## Open Questions

None — see [`clarify.md`](clarify.md).
