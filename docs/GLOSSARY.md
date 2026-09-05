# Glossary

| Term | Definition | Notes |
|------|------------|-------|
| MediaAsset | One imported image or video unit returned by search and shown in detail | Results never promote frames/segments to this unit in 001 |
| Semantic search | Retrieve assets by meaning via embeddings + local vector index | Required non-empty query in 001 |
| Metadata filter | Restrict semantic hits by `mediaType` and/or tags | Tags use AND when multiple |
| Representative frame | Deterministically sampled still from a video, embedded in the same space as images | Max 3; short videos use 1 middle frame |
| bestFrame | Frame with max similarity score for a video hit | Evidence / thumbnail source; optional on detail API |
| EmbeddingPort | Port for producing vectors | Fake (wiring) vs Real Local (semantic AC) |
| Local-first | Run the vertical slice without GCP credentials | Product posture for 001 |
| Project OS | Repo harness: specs, hooks, verify, loops, agent roles | Inherited from template; not the media product |

Rules:

- Prefer terms the business/product already uses.
- Do not silently rename domain language for technical convenience.
- Ambiguous terms affecting acceptance criteria → Open Questions in the
  feature `clarify.md`.
