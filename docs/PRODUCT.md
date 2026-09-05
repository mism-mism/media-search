# Product

## What this is

**media-search** is a Media Asset Search server: import local image/video
assets, extract technical metadata, embed them into a local vector index, and
search by **semantic meaning** with simple metadata filters.

Users find mixed image and video assets through one search experience, open
asset detail, and preview the source media.

## Why it exists

Creative and production teams need to locate the right visual asset by meaning
(“person holding a product outdoors”), not only by filename or hand-written
tags. The first deliverable proves that value **locally**, without cloud
credentials, then later deploys the same application core to GCP via adapters.

## Users

- Local single operator / developer evaluating the vertical slice (v0 / 001)
- Later: teams deploying the same product capability on GCP (002+)

## Deployment posture

| Stage | Target |
|-------|--------|
| Development / Feature 001 | Local-first (no GCP required) |
| Reproducible runtime (part of 001) | Thin container for the local slice |
| Production | **GCP** — Cloud Run + GCS (+ OpenCLIP / sqlite-vec in 002; Vertex later) |

Development order:

```text
Local → Container / reproducible runtime → GCP deployment
```

Do **not** develop by deploying to GCP from day one.

## Feature roadmap (product boundary)

| Feature | Intent | Status |
|---------|--------|--------|
| **001** Local-first Media Asset Search Vertical Slice | Prove semantic search + filters + preview locally | completed |
| **002** `gcp-deployment` | Cloud Run + GCS; OpenCLIP + sqlite-vec; Terraform + CD | completed |
| **003** `iap-access` | IAP (External + Gmail allowlist) before production | completed |
| **004+** | Vertex eval (optional) — [PR #7](https://github.com/mism-mism/media-search/pull/7) | draft |

Rules:

- Concrete GCP service selection for compute/storage is Feature **002**.
- **Production** requires Feature **003 (IAP)** (no anonymous invoker).
- Feature **002** plumbing alone must not be treated as production if public.
- Feature specs: `specs/002-gcp-deployment/`, `specs/003-iap-access/`.
- Bootstrap prompt summary (non-SoR):
  [`docs/prompts/media-search-server-bootstrap.md`](prompts/media-search-server-bootstrap.md)

## Product search contract (001)

```text
semantic search  (required query)
  +
metadata filters
  - mediaType: image | video
  - tags: AND inclusion
```

No keyword/path/description substring search in 001. No filter-only browse
(empty semantic query is invalid).

Vector search is a **formal product requirement** for 001, constrained to a
**local / single-runtime** existing engine via adapters. Managed or distributed
large-scale vector infrastructure is out of scope for 001.

## Non-goals (near-term)

- Microservices, Kubernetes, complex IaC, Pub/Sub, distributed job platforms
  introduced “because GCP later”
- Building a custom ANN / vector-DB engine (build the **product capability** and
  ports; reuse an existing local engine as an adapter)
- AI caption / tag generation in 001 (embedding quality must not be conflated
  with caption quality)
- Auth / multi-user in 001
- Fully offline reproducibility (model download may require network once)

## Success (001)

With no GCP credentials:

1. Import JPEG/PNG/MP4(H.264) from a designated directory
2. Index with real local embeddings
3. Semantic query + mediaType/tags filters returns mixed MediaAsset results
4. Detail + HTTP preview of source media
5. Deterministic verify + **required** semantic-real gate + full-profile reviews
   converge

## Notes

- Docs (`PRODUCT` / `ARCHITECTURE` / feature specs) are Source of Truth.
- Agent bootstrap prompts are summaries only.
- Runtime language/framework is decided in Architecture (not in this file).
- Vector engine product name is chosen in 001 `plan.md` after Domain/Ports.
