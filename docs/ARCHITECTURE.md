# Architecture

## Dual concern

This repository still runs the **Project OS** (CONSTITUTION, `AGENTS.md`,
hooks, verify, loops, agent roles). That process architecture is unchanged in
intent; see preserved docs (`LOOPS.md`, `RUNTIME.md`, `CI.md`, `ADOPTION.md`).

This file describes the **media-search product** application architecture.

## Product shape (ports & adapters)

```text
Domain / Application
        │
        ▼
   Port / Interface
        │
   ┌────┴─────┐
   ▼          ▼
Local       GCP
Adapter     Adapter
```

- **GCP is the production placement detail**, not a domain premise.
- Do not leak GCP SDKs/APIs into Domain / Application.
- Feature **001** implements **Local** adapters only (+ thin reproducible
  container for that local slice).
- Feature **002** swaps Local adapters for GCP adapters without changing
  Domain / Application cores when possible.

## Design principles

1. SOLID / DIP — Domain depends on ports; adapters implement them
2. Domain ↛ Infrastructure
3. Vertical slices over premature platform sprawl
4. Rule → Enforcer (else SKIP, never fake PASS) for harness gates
5. Simplicity — no dual Local implementations “only to prove DIP”
6. True adapter swap proof is **002** (Local → GCP); 001 proves one Real Local
   path + dependency direction via architecture review and tests

## Capability boundaries (names finalize after Domain)

Propose Local vs GCP adapters for each capability after Product/Domain/Use Case
design—not before:

| Capability | 001 (Local) | 002 (GCP) |
|------------|-------------|-----------|
| Application runtime | Local process / thin container | **Cloud Run** |
| Media storage | Filesystem under import/data roots | **GCS** |
| Metadata persistence | SQLite via port | **sqlite** (durable strategy per 002 plan) |
| Search / vector index | sqlite-vec | **sqlite-vec** (same; Vertex deferred) |
| Embedding / AI | FakeEmbedder + Real Local OpenCLIP | **OpenCLIP in Cloud Run** (Vertex deferred) |
| Media source / preview | HTTP media endpoint (local files) | HTTP media endpoint **streaming from GCS** |
| Secrets / configuration | Local config / env | Terraform + Actions (WIF preferred) |
| Observability | Minimal local logging | Cloud Run logs (minimal) |
| IaC / CD | n/a | **Terraform** + Actions **`workflow_dispatch`** |

Illustrative ports (not mandatory names):

```text
MediaStorage / MetadataRepository / VectorSearch
EmbeddingPort / MediaSource
```

## Embedder switching

| Mode | Use |
|------|-----|
| `EMBEDDER=fake` | Unit / integration / wiring; deterministic |
| `EMBEDDER=local` | Semantic golden tests + product evaluation |

Default runtime posture for “real” app startup: **Real Local**.
Fake must not be the default for product-like launches.
**Fake must never count as semantic-search PASS.**

## Verify / gates (product)

```text
Default verify
├ deterministic tests (incl. Fake wiring)
└ harness / schema / API contracts as configured

Semantic-real gate (Required for 001 convergence; separate job/command)
├ fixed model/version
├ Real Local Embedder
└ golden Top-K tests
```

Model cache miss → setup/download → run. Setup failure → **FAIL** (no silent
SKIP). Full offline reproducibility is a **non-goal**.

001 converged when: Inner deterministic verify + semantic-real + required
reviews (profile **full**) pass.

## Runtime language / framework (locked for 001)

| Choice | Decision |
|--------|----------|
| Language | **Python 3.10+** (container target **3.12** when available) |
| HTTP API | **FastAPI** |
| Minimal UI | Static/templates served by the same app (no separate SPA framework required for 001) |
| Media tooling | **ffmpeg** (frames) + **Pillow** (images) |
| Embeddings | **OpenCLIP multilingual** default:
  `xlm-roberta-base-ViT-B-32` / `laion5b_s13b_b90k` (override via env);
  FakeEmbedder for deterministic tests |
| Local vector | **SQLite** persistence + **sqlite-vec** (exact/local KNN). Filters may be applied in Application if simpler |
| Container | `python` slim image + ffmpeg; model weights via cache volume (not baked in) |

### Embedding contract (mandatory)

- Multimodal: `embed_image` and `embed_text` share one space and dimension.
- Index grain: persist **one vector per frame** (an image is one frame); collapse to
  `MediaAsset` at query time via `asset_id` (`max` score + `best_frame`).
- Changing the embedding model/version requires re-index.

### Local vector engine rationale

Chosen for local-first, single-runtime, persistence, low setup cost, and container
friendliness. GCP migration impact is **not** a primary selector (002 rewrites
the adapter). See 001 `plan.md` comparison table.

## What 001 must not add “for GCP later”

Microservices, Kubernetes, complex IaC, Pub/Sub, distributed job platforms,
managed/distributed large-scale vector infrastructure, GCP-only abstractions
without a Local path.

## Project OS (unchanged summary)

Work SoT: `specs/<NNN-name>/`. Agent entry: `AGENTS.md`.  
Loops: [`LOOPS.md`](LOOPS.md) · Runtime: [`RUNTIME.md`](RUNTIME.md) ·
CI: [`CI.md`](CI.md).

| Profile | Inner | Outer |
|---------|-------|-------|
| lean | test, code-quality | product |
| full | test, code-quality | + architecture, security, final (+ analyze) |

Feature 001 uses **full** because it establishes cross-boundary contracts for
the product.
