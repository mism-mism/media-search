# Clarify

## Decisions and provenance
- Human requested category presence tagging from reference images, then explicitly
  authorized separate-worktree implementation through PR (2026-09-07).
- Existing Google Cloud Gemini, IAP and SQLite/GCS constraints continue.
- Implementation choices: name + visible criteria + 1–3 examples, at most five
  categories, conservative three-way outcomes; only positive outcomes are tags.
  These are not separately elicited human decisions. References are independent
  snapshots, so deleting a library asset cannot break category definitions.
- Create/delete first increment; changing a definition uses delete then register.
  All category results are invalidated on a catalog change, with explicit UI copy.
- PR only for category feature; do not deploy or process the production corpus.

## Unresolved items
None affecting Domain, Constraints or Acceptance Criteria for this increment.
