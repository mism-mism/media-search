---
id: "019"
status: active
profile: full
profile_reason: "Reference category domain, persisted judgments, Gemini multimodal contract and management API"
---
# Spec: Reference-image category tagging

## Problem / Goal
Operators want to supply category examples and find images containing a similar
visible subject. Human authorized implementation in an isolated worktree and a
PR on 2026-09-07. This is category presence, not exact-image or SKU identification.

## Requirements
- Register a category name, visual criteria and 1–3 uploaded example images from
  a visible UI. List examples and delete categories. Initial maximum 5 categories.
- On import, compare an image with registered examples through Google Cloud
  Gemini. Record match / no_match / uncertain and a short reason per category.
  Only match category names enter keyword search and tag filters.
- Keep category results/provenance separate from manual tags and generic AI tags.
  Preserve product identity, media vectors and video behavior.
- Reuse successful judgments for unchanged assets/catalogs. Catalog mutation
  invalidates previous judgments immediately; reimport computes current results.
- Bound additional classification calls to 50 per import by default, independently
  configurable. Failure/deferred are visible and retryable. No search-time calls.
- Keep SQLite/GCS, IAP and single-writer import locking. No new cloud service or
  credentials. Classification follows existing Gemini enablement. No deployment
  or unbounded corpus processing in this PR.

## Acceptance Criteria
- AC1. UI/API create/list/preview/delete validated categories; reject invalid,
  oversized/non-image inputs, duplicates, >3 references and >5 categories.
- AC2. Import→persistent reload→keyword and exact tag filter retrieve matches;
  negative/uncertain outcomes do not add tags. Manual/generic tags stay intact.
- AC3. Unchanged success reuses results without model calls/re-embedding;
  changed media/catalog invalidates results; errors/caps preserve indexed media.
- AC4. Catalog mutation holds existing distributed lock, reloads before write,
  commits catalog+invalidation together, persists before release; busy returns409.
- AC5. Fixed authenticated Gemini endpoint, bounded multi-image request, strict
  complete category ID/enum/reason validation, safe errors and escaped UI output.
- AC6. Shared service/worker wiring, old schema and DB replacement remain valid;
  deterministic concurrency, migration, API and rendered UI tests pass.
- AC7. Record a bounded real-image sample if existing provider access permits,
  distinguish observed quality from fake wiring, and document limits/retry/cost.
- AC8. Independent full Inner/Outer reviews and feature-scoped gates pass; PR
  contains reviewable code, verification evidence and outstanding limitations.

## Open Questions / Constraints
None unresolved for this increment. Operational caps and create/delete-only
management are implementation choices within the authorized feature. Automatic
SKU identity, bounding boxes, videos, model training and editing are out of scope.
