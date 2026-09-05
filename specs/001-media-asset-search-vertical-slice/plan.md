# Plan: Media Asset Search Vertical Slice (Local-first)

## Architecture

Ports & adapters per [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).

001 delivers **one** Real Local adapter path per port (plus Fake embedder for
deterministic tests). No second Local stack “to prove DIP”. GCP adapters are
002.

**Before coding:**

1. Fix runtime language/framework in `docs/ARCHITECTURE.md`
2. Compare local vector engines in this plan (axes below) and lock one brand
3. Pin embedding model/version for semantic-real

### Vector engine comparison (locked)

| Axis | sqlite-vec + SQLite | FAISS + separate meta | Qdrant embedded |
|------|---------------------|----------------------|-----------------|
| local-first | Excellent (one file DB) | Good | Good |
| image/video embeddings | Neutral (vectors only) | Neutral | Neutral |
| persistence | Excellent | Extra files | Good |
| filtering | SQL / app-level OK at 001 scale | App-level | Strong native |
| setup complexity | Low | Medium | Medium-high |
| container friendliness | High | High | Medium |
| GCP migration impact | Rewrite adapter anyway | Same | Same |

**Selected engine:** **SQLite + sqlite-vec** (Application may apply mediaType/tags
filters). Exact KNN is acceptable at 001 scale.

**Selected language/FW:** **Python 3.10+ / FastAPI** (container target 3.12; see `docs/ARCHITECTURE.md`)

**Semantic-real model/version:** **OpenCLIP
`xlm-roberta-base-ViT-B-32` / `laion5b_s13b_b90k`** (multilingual text; JA queries).
Override via `OPENCLIP_MODEL` / `OPENCLIP_PRETRAINED`. Re-index required if
changed. Do **not** evaluate semantic quality on `EMBEDDER=fake`.

**semantic-real gate:** `./scripts/semantic-real` (Required for 001 convergence;
separate from default `./scripts/verify`).

## Domain model

- **MediaAsset** (image | video): identity = import-root relative path
- Technical metadata; optional tags/description
- Video indexing uses representative frames internally; results collapse to
  MediaAsset with score = max(frame), bestFrame evidence
- No VideoSegment aggregate in 001

## Interfaces

- Import (directory path) → upsert pipeline
- EmbeddingPort: `fake` | `local`
- VectorSearch port: add/update/query (+ filter application)
- MediaSource / HTTP media endpoint for preview
- Search HTTP API: `q` (required), `mediaType?`, `tags?` (AND)
- Minimal UI consuming the API

## Dependency direction

```text
UI / HTTP → Application / Use cases → Domain
                ↓
              Ports
                ↓
        Local adapters (001)
```

Adapters must not be imported by Domain.

## Contracts

Required — public HTTP API and media endpoint shapes will be specified when
language/FW is chosen. Until then, behavioral contracts are the Acceptance
Criteria in `spec.md` (status codes for empty `q`, Top-K semantics, upsert
identity, import summary for skips).

Update this section with concrete request/response schemas before
pre-implement.

## Test strategy

| Layer | Embedder | Asserts |
|-------|----------|---------|
| Unit / wiring | Fake | import upsert, filters, validation 400, collapse max/bestFrame |
| Integration | Fake | API + filesystem fixtures without semantic quality |
| semantic-real (Required gate) | Real Local | golden 8–12, expected ∈ Top-5 |
| Outer product | Real Local | human usability (AC9) |

## Vertical slice

Walking skeleton → full slice:

1. Import + metadata + Fake embed + index + search API
2. Real Local embed + golden
3. UI + preview endpoint
4. Thin compose path + documented model prep
5. Full-profile reviews + convergence

## Risks

| Risk | Mitigation |
|------|------------|
| Model download / CI weight | Separate semantic-real gate; no silent SKIP |
| Ports wrong for GCP | full architecture review; swap proof deferred to 002 |
| Scope creep (ASR, captions, fusion) | Out of Scope enforced |
| 2-day timebox | Formats/filters/frames tightly capped in spec |

## Task decomposition

See `tasks.md` (high-level; refine after language + engine selection).
