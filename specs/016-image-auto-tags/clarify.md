# Clarify: Japanese image enrichment

## Decisions and provenance

- Human, 2026-09-06: accepted the recommendation to generate Japanese tags and
  short descriptions from images, store them and use them in keyword search.
- Existing project constraints: Google Cloud deployment, IAP, exact product_id
  identity, OpenCLIP and single-writer SQLite/GCS persistence remain applicable.
- Agent implementation choices within that scope: separate generated/manual
  metadata, image-only initial slice, reuse completed output, keep indexed assets
  usable on enrichment failure, bounded per-import calls, and an initial small
  real sample. These are not represented as separately elicited human decisions.
- Existing images are supported via reimport/scoped import. No unattended full
  corpus backfill is performed. Provider calls occur only on import, not search.

## Unresolved items

None affecting this bounded feature. Actual corpus quality and provider access
are verification work, not assumed facts. New storage/model migration is deferred.
