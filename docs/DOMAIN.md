# Domain

## Purpose

Represent **media assets** (images and videos) that operators import, enrich
with technical metadata and optional human tags/descriptions, embed for
semantic retrieval, and inspect via search and detail views.

Domain language follows the product: search results are always **MediaAsset**
units. Video representative frames and `bestFrame` evidence are indexing /
debug details, not separate searchable domain entities in Feature 001.

## People / Things / Events (TM sketch)

- **People:** Local operator (single user in 001; no auth)
- **Things:** MediaAsset (image or video), technical metadata, tags,
  description (optional human/fixture), embedding vectors (via ports),
  search query, filter criteria
- **Events:** Import (batch from directory), upsert by relative path identity,
  embed/index, semantic search, view detail / preview

## Boundaries

### In scope (product direction; 001 details in spec)

- Import from a designated directory
- Technical metadata extraction
- Semantic embedding and local vector search
- Metadata filters (`mediaType`, `tags` AND)
- Mixed image/video results collapsed to MediaAsset
- Asset detail and source preview

### Out of scope (domain)

- VideoSegment / scene / transcript as first-class search results (001)
- Multi-tenant tenancy and authentication (001)
- GCP-specific concepts inside the domain model

## Notes

- Agents must not invent domain facts to fill gaps — raise Open Questions.
- Port names and aggregate details are finalized in Architecture / 001 plan
  after this sketch.
- Identity for import upsert: **relative path from import root** (not content
  hash as domain identity).
