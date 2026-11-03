---
id: "020"
status: active
profile: lean
profile_reason: "Adds an alternate Gemini transport and a thin CLI over existing use cases; no domain, storage or API contract change. GCP paths stay as they are."
---

# Spec: Run on EC2 with local adapters

## Problem

The search service runs on Cloud Run with GCS, IAP and Vertex. The user decided
(2026-11-01, mk2-harness ADR 0007 §3) to move it to the shared EC2 box behind the
Slack front desk: local disk instead of GCS, systemd instead of Cloud Run,
Cloudflare Access instead of IAP, and Gemini through an AI Studio API key instead
of Vertex + ADC. Local adapters already exist; two pieces are missing.

## Goal

1. Gemini annotation and category classification work with an API key only.
2. The harness dispatcher can search and import from the command line.

## User

The operator (non-engineer) searching from Slack; the harness dispatcher that
runs the CLI as the `media` user.

## Requirements

- Keep tags continuous: same model, prompt and response schema; only the
  transport and credentials change.
- The dispatcher never parses HTML or reads the media folder itself: the CLI
  returns everything it needs (metadata, thumbnails, one self-contained HTML page).

## Acceptance Criteria

- AC1. When `GEMINI_API_KEY` is set, `IMAGE_ANNOTATION_BACKEND=gemini` builds the
  annotator and the category classifier against
  `https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent`
  with the key in the `x-goog-api-key` header, without `GOOGLE_CLOUD_PROJECT` or
  google-auth. The key never appears in the URL, job errors or exceptions. Without
  the key, the Vertex + ADC path is unchanged (existing tests keep passing).
- AC2. `python -m media_search.cli search <query> [--top-k N] [--json]` runs the
  existing text search through the resident API (`MEDIA_SEARCH_API`; the CLI loads no model). `--json` prints `{query, hits: [{asset_id, display_name,
  media_type, score, tags, thumbnail}], html}`: `thumbnail` is a base64 JPEG at
  most 512 px on the long side (the representative frame for videos), `html` is
  one self-contained page (thumbnails as data URIs, every text field escaped, no
  scripts). A hit whose thumbnail cannot be read keeps `thumbnail: ""` and is left out of
  the page; the search still exits 0. Without `--json` it prints one line per hit.
- AC3. `python -m media_search.cli import [--json]` imports the configured media
  root through the resident API (`POST /api/import`, waits for the job) and prints `{imported, updated, skipped}` (the same lists as `POST /api/import`). A busy
  lock exits with code 75 and `{error: "import_busy"}`; other failures exit 1 with
  `{error}` and no traceback or provider body on stdout.
- AC4. `docs/run-ec2.md` lists the local env (`MEDIA_BACKEND=local`,
  `FRAME_BACKEND=local`, `IMPORT_LOCK_BACKEND=fs`, no `MEDIA_SEARCH_DB_GCS`,
  `GEMINI_API_KEY` in `media.env`) and how the CLI is called. Unit tests cover
  AC1–AC3; the existing suite and lifecycle gates pass.

## Out of Scope

- Removing GCS, Cloud Run, IAP or Terraform code (kept for rollback for two weeks).
- systemd units, users, proxy allowlists and data copy (they live in mk2-harness).
- Video import on EC2 (needs ffmpeg there; images only in the current data).

## Constraints

- No new runtime dependency beyond `requests` for the API-key transport.
- One OpenCLIP model per box: the CLI calls the resident API; no second wiring of adapters.

## Open Questions

None. Gemini via API key and keeping tags were decided by the user on 2026-11-01 (clarify.md D2).
