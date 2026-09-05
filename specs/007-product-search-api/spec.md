---
id: "007"
status: active
profile: full
profile_reason: "Dual query modes + SKU-grade hybrid contract + API surface"
---

# Spec: Product name + similar-image search (API)

## Problem

Users need to find assets by **product name** and by **query image** (same /
similar product), with predictable warm latency, and a clear **HTTP API** for
later machine clients. Today only text→image semantic search exists; OpenCLIP
alone does not guarantee SKU identity.

## Goal

Expose API (+ library UI hooks where cheap) for:

1. Product-name search (semantic **and** display_name/tags text match)
2. Similar-image search (image query → same vector index)
3. SKU-grade identity when `product_id` is present (hybrid per D6)

Warm p95 may be a few seconds. Auth stays IAP for this Feature.

## User

Team operators (IAP) and, later, machine clients behind the same IAP edge
until a dedicated API-key Feature.

## Requirements

- R1. Text search combines semantic Top-K with display_name/tags substring
  match; merge by `asset_id` (keep best score; text-only hits included).
- R2. Image search: `POST /api/search/by-image` multipart → embed image →
  vector KNN over existing index (labeled **visual similar** unless filtered
  by `product_id`).
- R3. Optional `product_id` on assets; optional `product_id` query filter =
  exact match (SKU-grade path). Bare visual KNN must not claim SKU match.
- R4. Warm latency: few seconds acceptable; document cold-start separately.
- R5. IAP only (no new machine auth in 007).
- R6. Text search remains available as `GET /api/search` and also
  `POST /api/search` (JSON body) for clients.

## Acceptance Criteria

- AC1. `GET` and `POST` text search return semantic hits and include
  display_name/tags substring matches when present.
- AC2. `POST /api/search/by-image` returns ranked assets from the same corpus
  index; responses/docs mark bare image search as visual similar.
- AC3. When `product_id` filter is set, only assets with that exact
  `product_id` are returned; tests cover the hybrid rule.
- AC4. OpenAPI (`/docs`) and a short product/docs note describe both modes and
  the hybrid SKU contract.
- AC5. Out of Scope upheld (no API-key Feature; no mandatory Vertex).

## Out of Scope

- API keys / service-account machine auth productization
- Guaranteeing SKU match from pixels alone without metadata or a new embedder
- Sub-second p95 redesign
- Replacing OpenCLIP as default before a dedicated eval Feature

## Constraints

- Clarify Round 1–2 locked (D1–D8).
- 006 library UI finish acknowledged (deployed 2026-09-06).
