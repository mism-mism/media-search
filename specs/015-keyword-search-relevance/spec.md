---
id: "015"
status: active
profile: lean
profile_reason: "Local keyword matching and ranking corrections within existing search interfaces"
---

# Spec: Reliable keyword search

## Problem

The operator reports poor search relevance and wants stronger keyword search.
Reproduction shows Japanese tags are missed by SQLite text search and a literal
name match can be excluded by the result limit in favor of semantic-only hits.

## Goal

Make existing display-name and tag keyword matches reliable and visible first.

## User

Operators searching the media library by known names and tags.

## Requirements

- R1. Search actual tag strings, including Japanese and escaped characters, in
  existing SQLite data without requiring reimport. Match each tag separately.
- R2. In text search, put literal display-name/tag matches before semantic-only
  matches, then use the existing score within each group. Break ties by asset ID.
- R3. Preserve semantic candidates, deduplication, filters, result limits, image
  search behavior, and the existing score and response fields.
- R4. Retain SQL candidate selection; do not load all metadata into Application.

## Acceptance Criteria

- AC1. SQLite and memory repositories agree on Japanese tags, quoted/backslash
  tags, literal `%`/`_`, case-insensitive ASCII matches, blank queries, and
  nonmatches across tag boundaries or against JSON serialization syntax.
- AC2. A literal name or tag hit survives `top_k=1` ahead of a stronger
  semantic-only hit; ties have deterministic ordering and duplicates stay merged.
- AC3. GET and POST search expose the corrected ranking and Japanese tag matches;
  type, tag and exact product filters, image search and best-frame selection
  retain regression coverage.
- AC4. Independent lean reviews and feature-scoped lifecycle gates pass.

## Out of Scope

New search modes, query syntax, product-master joins, synonyms, automatic image
tagging, embedding model changes, and UI redesign. Production deployment was
outside the initial implementation scope; the human follow-up authorizes
release through the existing deployment procedure (see clarify.md).

## Constraints

Build on 007 name/tag hybrid search and 009 SQL selection. No new dependencies,
database migration, external service or model execution is needed for this fix.

## Open Questions

None for this bounded correction of existing keyword search.
