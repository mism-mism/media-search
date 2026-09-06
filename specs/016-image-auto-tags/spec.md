---
id: "016"
status: active
profile: full
profile_reason: "Image enrichment provider, persisted provenance, import behavior and additive API fields"
---

# Spec: Japanese image tags and descriptions

## Problem / Goal / User

Operators want to find images using words describing their visible content even
when those words are absent from filenames. Generate Japanese tags and a short
description during image import, persist them, and include them in keyword search.
The human accepted this recommended increment on 2026-09-06.

## Requirements

- R1. Use Google Cloud Gemini for image enrichment on import when enabled.
  Describe visible objects, colors, actions and setting in Japanese. Do not
  infer a SKU or modify product identity from pixels.
- R2. Preserve manual tags, description, name, folder and product_id. Persist
  generated tags/description and model/prompt-version provenance separately.
- R3. Enrich new images and previously indexed images missing enrichment. Reuse
  successful enrichment for unchanged assets; enrichment-only work must preserve
  existing frame vectors/thumbnails. Videos retain existing behavior.
- R4. Generate at most 50 images per import by default (configurable positive
  limit). Timeout, invalid output, refusal and quota failures must not destroy
  successfully indexed media. Record a visible, safe enrichment failure state
  and permit retry on a later import. No unbounded automatic retry.
- R5. Keyword search includes manual/generated descriptions and generated tags;
  explicit tag filters include manual + generated tags. Keep 015 text priority,
  exact product filters, semantic candidates and image search.
- R6. Add generated metadata/status to library, search and detail responses;
  show expandable AI-generated tags/description on image cards, clearly labeled.
- R7. Keep current GCS-backed SQLite persistence and OpenCLIP vectors. External
  credentials and SDK types stay outside domain/application. Search does not
  call Gemini. Local default disables enrichment; production enables it explicitly.

## Acceptance Criteria

- AC1. Tests prove import → generated Japanese metadata → persistent reload →
  GET/POST keyword hit by words absent from the name/manual fields.
- AC2. Existing metadata survives; unchanged success makes no additional model
  call; missing/failed enrichment can be retried without re-embedding frames.
- AC3. Failure/refusal/invalid JSON and concurrent budget exhaustion preserve
  vectors and manual metadata, expose accurate status, and do not exceed the cap.
- AC4. Old SQLite rows migrate with no generated data; loaded and replaced
  connections work; SQL/memory search semantics and tag filters agree.
- AC5. Gemini adapter uses authenticated fixed Google endpoint, bounded image
  input/output, schema validation and safe errors; tests cover request/response
  boundaries without live credentials. Generated text renders escaped in the UI.
- AC6. Configuration is wired for service and Import Job; deployment guidance
  explains enable/disable, prerequisites, limits, retries and bounded backfill.
- AC7. Run a small real-image sample (initially <= 3 images), record generated
  metadata and keyword-retrieval results, or explicitly report a provider blocker.
  Fake results alone are not evidence of actual Japanese tag quality.
- AC8. Full Inner/Outer reviews, feature verification and merge gates converge.

## Out of Scope

Embedding-model/store migration, Firestore/BigQuery cutover, video auto-tags,
automatic SKU identification, OCR guarantees, unrestricted corpus backfill,
new tag-editing workflows, and broad UI redesign.

## Constraints / Open Questions

Use the existing single-writer import and IAP boundary. Initial implementation
uses the existing size-based unchanged detection; same-size external object
replacement detection is not strengthened here. None unresolved for this slice.
