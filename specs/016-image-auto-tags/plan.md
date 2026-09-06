# Architecture: Japanese image enrichment

## Model received

See model.md. Preserve MediaAsset and product identity; introduce a generated
image-description value and an optional failure/deferred state on the asset.

## Use cases and boundaries

ImportDirectory consumes ImageAnnotationPort, receiving validated Japanese tags,
description and model/prompt provenance. It owns reuse, per-import request cap,
failure recording and single-writer persistence. For unchanged indexed images,
enrichment-only writes do not regenerate or delete frames.

Dependencies: domain value ← port ← import/search use cases; Gemini/SQLite/UI
adapters point inward. Composition root chooses the configured adapter. External
credentials, HTTP, image resizing and response parsing stay in Gemini adapter.

## Decisions and alternatives

- Gemini REST generateContent with existing google-auth/requests transport;
  declare these direct GCP dependencies. Thread-local authenticated sessions,
  fixed endpoint, timeout, one bounded request per attempt, strict JSON/schema
  validation. No API key. Upload resized JPEG bytes; no arbitrary URL fetching.
- Configurable model, initially gemini-3.1-flash-lite, global endpoint. Current
  official GA/model documentation is linked in the research note. Provider
  availability is verified with a small live sample before release claims.
- Retain SQLite/GCS. Add nullable generated annotation JSON and safe status
  fields with backwards-compatible defaults; ensure schema on DB replacement.
  A separate cloud metadata store would add migration cost without serving this
  incremental requirement. The new value is accessed through current metadata port.
- Expose separate generated fields in API and expandable card details. Manual
  fields retain their meaning. Keyword matching expands across descriptions and
  auto-tags; `tags` query filters use the combined set. No Gemini query calls.

## Contracts

Additive response fields only, existing request schemas unchanged. Persist
generated tags, description, model and prompt version. Failed/deferred state is
observable and contains no provider response or credential. Existing DB rows
load without enrichment. Image requests are only made for supported image assets.

## Validation and risks

TDD for persistence/search first, import lifecycle second, HTTP adapter third,
then composition/API/UI. Simulate timeout/refusal/bad JSON/cap concurrency and
database reload. Verify actual provider on <=3 existing local corpus photos;
record measured outputs and retrieval, no generalized quality claim. Prompt
injection in images is treated as untrusted content, output cannot invoke tools,
and rendered model strings use existing HTML escaping. Model correctness is not
guaranteed by JSON validation. Existing size-based freshness remains a limitation.

## Open issues

No unmade middleware choice blocks implementation. Real provider access remains
to be observed. No automatic broad backfill or embedding migration is authorized.
