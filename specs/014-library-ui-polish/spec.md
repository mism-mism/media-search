---
id: "014"
status: completed
profile: lean
profile_reason: "Presentation-only UI; same APIs"
---

# Spec: Library UI polish

## Problem

`/` looks like a verification console, not a product.

## Goal

Redesign Library UI per `docs/design/014-library-ui.md` v2 (DAM IA + スタジオライト).

## User

Operators using IAP Library daily.

## Requirements

- R1. Follow design brief IA and visual tokens.
- R2. Preserve upload→Import poll, search, folders, products CRUD behaviors.
- R3. Single `_ui_html` implementation; JA chrome; debug in footer.

## Acceptance Criteria

- AC1. Design brief committed and implemented.
- AC2. Existing API flows still work (smoke via UI / hermetic if feasible).
- AC3. Lean reviews PASS.

## Out of Scope

New search semantics, dual vectors, SPA rewrite.

## Open Questions

None.
