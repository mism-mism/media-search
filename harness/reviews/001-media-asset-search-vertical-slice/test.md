---
reviewer_role: test-reviewer
reviewer_id: test-review-subagent
---

# Test review: 001-media-asset-search-vertical-slice

## Verdict

**PASS**

Primary AC-locking coverage (import/upsert/skip, empty `q`, tags AND, video
frame collapse + bestFrame thumbnail, Fake wiring) plus the Required
**semantic-real** golden gate are present and green. Residual gaps below do
not overturn Inner test convergence for this slice, but should not be ignored.

## Evidence (claimed / inspected)

| Gate | Result | Notes |
|------|--------|-------|
| `python3 -m pytest -q` | **19 passed, 1 skipped** | Skip = OpenCLIP smoke (`RUN_OPENCLIP_SMOKE=1`); hermetic default OK per `rules/testing.md` |
| `./scripts/semantic-real` | **12/12 PASS** | Real Local embedder; expected ∈ Top-5 |
| Default `./scripts/verify` | unit-test wired; **does not** run semantic-real or Docker | Matches R27 / docs/run-docker.md |
| Golden fixtures | `fixtures/golden/golden.json` = **12** pairs (AC4 band 8–12); images + videos | Regenerated via `scripts/prepare-golden-fixtures` |

## AC mapping

| AC | Coverage | Assessment |
|----|----------|------------|
| AC1 local API+UI start | `test_health_ok`; FastAPI TestClient search/import/media | **Partial** — process start covered hermetically; **thin container path not automated** in default verify |
| AC2 import JPEG/PNG/MP4 + skip summary | PNG + MP4 import tests; unsupported SKIP+reason | **Partial** — **JPEG file import not asserted**; technical metadata fields (w/h/duration/EXIF) largely unasserted |
| AC3 re-import upsert | `test_reimport_is_upsert` | **Covered** |
| AC4 semantic golden Top-5 | `semantic-real` + golden.json (12 cases, both media types) | **Covered** (separate Required gate; Fake ≠ semantic PASS) |
| AC5 mediaType + tags AND; empty q→400 | empty q (API+use case); tags AND use case | **Partial** — **`media_type` filter has no automated test** (impl exists in search/API) |
| AC6 video→one MediaAsset, max score, bestFrame thumb/evidence | collapse test; API bestFrame thumbnail | **Mostly covered** — detail optional bestFrame evidence lightly exercised (list/search path stronger than detail) |
| AC7 HTTP preview image/video | `/media/` for PNG | **Partial** — **video `/media/` play path not tested** |
| AC8 deterministic verify + semantic-real | pytest via verify; semantic-real separate script | **Covered by design** (R27/R28); Docker compose E2E **not** in verify |
| AC9 human usable Outer | N/A for this role | Product reviewer / human |

## What is locked well

- Failure/edge: unsupported format skip; empty/whitespace `q`; negative duration;
  short vs ≥5s frame planning; short=1 / long=3 frame import.
- Risk-critical semantic path: pinned Real Local gate fails hard on model miss
  (no silent SKIP); golden prep script + fixture set exist.
- Fake hermetic path stays in default verify (R27/R29 alignment).

## Honest gaps / residual risk

1. **`mediaType` filter untested** (AC5) — highest residual AC gap for this review.
2. **JPEG import** and **rich technical metadata** assertions thin (AC2).
3. **Video HTTP preview** not covered (AC7).
4. **Docker / compose E2E** (Fake or Real Local) is documented manual path only —
   **not automated in default `./scripts/verify`** (intentional per R27; still a
   gap vs AC1 “via the thin container path” observability).
5. OpenCLIP unit smoke skipped by default — acceptable because semantic-real is
   the Required semantic gate; do not treat Fake pytest as semantic PASS (R29).

## Recommendation

PASS for Inner test-reviewer. Prefer a small follow-up (or Outer note) adding
at least: (a) `media_type=image|video` filter test, (b) optional video `/media/`
smoke — before treating the suite as fully AC-tight.
