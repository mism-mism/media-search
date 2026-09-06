# Plan: Reliable keyword search

## Architecture and domain model

Keep SearchMediaAssets and MetadataRepositoryPort. Metadata text matching remains
adapter-owned; merged result ordering stays in the search use case. MediaAsset,
tags, frames, scores and exact product identity retain their current meanings.

## Interfaces and dependency direction

No signature, schema, dependency or layer changes. SQLite selects using decoded
JSON tag elements rather than serialized JSON. No full-corpus application scan.

## Contracts

GET/POST keep their request/response schema and combined candidate set. Text
matches precede semantic-only matches; score retains its existing meaning within
each group. Image search retains score ordering. Existing DB rows work directly.

## Test strategy

Observe failing repository parity and top-K ranking regressions first. Cover the
real SQLite metadata adapter through GET/POST, literal metacharacters, tag
boundaries, existing filters, deduplication and video best-frame behavior.

## Vertical slice and risks

Fix decoded tag selection, then keyword-first finalization, then API coverage.
JSON decoding adds query work; no index or performance improvement is claimed.
Model relevance and real-production corpus quality are not proven by fake vectors.

## Task decomposition

See tasks.md.
