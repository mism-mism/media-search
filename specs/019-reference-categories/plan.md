# Architecture and plan

Model: model.md. Domain owns reference categories, decisions and classification
report. Ports own catalog persistence and classification; application manages
catalog mutations and import reuse/caps. Adapters implement SQLite and Gemini.
API normalizes bounded JPEG reference inputs and serves previews under existing
IAP. UI extends current neutral library styling and accessible tab navigation.

Retain SQLite/GCS rather than add another database. Store compressed immutable
reference bytes in category rows (bounded 5×3×256KiB). Category changes and report
invalidation share one transaction. Use existing import lock, reload remote DB
before mutation and persist after mutation. Reload also replaces catalog adapter
connection. Category writes unavailable while import owns the lock.

Import snapshots catalog once, sends target + all references in one bounded
classification call per image, independent of generic annotation. Default 50
additional calls per import, enabled by existing Gemini setting. Failed/deferred
classification is retried; metadata-only work preserves frame objects. Catalog
fingerprint covers category IDs/content so reports cannot be reused by accident.
Only matched names join search_tags and SQL text matches. Return full report and
status separately in existing asset responses. No vendor data types in domain.

Verification: Red/Green tests at domain/import/provider/persistence/API boundaries,
actual rendered UI interaction, optional bounded real provider sample; independent
full reviews and lifecycle gates. No production deployment for this feature.

## Deferred decisions
Editing, per-category selective reclassification, calibrated confidence scores,
object localization and training require demonstrated need and separate scope.

## Review correction: source identity
Classification reuse includes a SHA-256 fingerprint of source bytes. When enabled
categories exist, reimport reads image bytes to validate this fingerprint even
if legacy size detection says unchanged. This costs storage reads but no extra
model calls on unchanged success. A detected changed source rebuilds its image
vector and clears stale AI observations; same-size replacement cannot retain a
positive category through provider failure or cap deferral.
