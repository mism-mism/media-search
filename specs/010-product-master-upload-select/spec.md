---
id: "010"
status: active
profile: lean
profile_reason: "Product CRUD + upload select; no new auth/embedder"
---

# Spec: Product master + upload-time select

## Problem

SKU (`product_id`) is only set via PATCH or sidecar. Operators want a
**product master** and to **choose the product when uploading**.

## Goal

1. Maintain Products (`product_id` + `name`)
2. Optional product select on library upload
3. Selected id stored on the asset for 007 search filters

## User

IAP operators managing a shared media library.

## Requirements

- R1. Create / list / rename Products; `product_id` immutable after create.
- R2. Delete Product only when no asset references it.
- R3. Upload API/UI accepts optional `product_id` (must exist in master if set).
- R4. No auto SKU-from-pixels; no required reference images.
- R5. Existing `product_id` search filter unchanged.

## Acceptance Criteria

- AC1. Clarify Round 1 locked (D1–D6).
- AC2. Create + list products via API (and UI).
- AC3. Upload with selected product stores `product_id` on asset.
- AC4. Delete in-use product → error; rename name works; id not changed.
- AC5. Out of Scope upheld.

## Out of Scope

- Automatic product recognition
- External PIM sync
- API-key auth / 008 cutover

## Constraints

- sqlite same DB as assets (D5); lean profile (D6).
