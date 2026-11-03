# Verification evidence

- CI-equivalent environment (`pip install -e ".[dev]"`, no semantic or gemini-key extras):
  `pytest -q` → 186 passed, 2 skipped (optional real OpenCLIP; `requests`-only header test),
  1 dependency deprecation warning.
- Targeted: `tests/test_cli_020.py`, `tests/test_gemini_annotator.py`,
  `tests/test_annotation_runtime.py` → 24 passed (local venv with requests).
- EC2 (mk2-harness, 2026-11-03, t3.large): CLI wheel installed from `de6f1f4` into
  `/opt/media-search/.venv`; `studio-dispatch media-search search 白いボトル` started the
  socket-activated service, ran `GET /api/search` through the CLI and returned
  `{hits: []}` (empty data by the user's decision) in 19 s cold. mk2-harness `check.sh`: all OK.
- Memory (ADR 0007 §3 criterion): one model in the resident service plus one in-process
  import of 38 photos, with Hermes, squid and the editor running: minimum MemAvailable
  3,922 MB, no OOM. Two processes each holding the model froze both t3.medium and
  t3.large, which is why the CLI calls the resident API (spec AC2/AC3, tasks decision).
- An earlier CI run timed out: a new test iterated over a list its monkeypatch appended
  to. Fixed in `77949b2`; no gate bypass.
