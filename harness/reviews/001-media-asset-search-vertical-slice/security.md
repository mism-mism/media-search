---
reviewer_role: security-reviewer
reviewer_id: security-review-subagent
---

# Security review: 001-media-asset-search-vertical-slice

## Verdict

**PASS**

Threat model: local single-operator app, **no auth by design** (spec R25 /
clarify Q31). No blocking issues found under that model. Residual risks below
are acceptable for 001 when documented; they become blockers if the surface is
later treated as multi-user / network-exposed without auth (→ 002+).

## Scope checked

| Area | Result |
|------|--------|
| Path traversal `/media`, `/thumbnails` | Mitigated |
| Import path handling | Operator-trusted; residual if networked |
| Secrets in repo | None found |
| Command injection (ffmpeg / ffprobe) | Mitigated (argv, no shell) |
| SQL injection | Parameterized queries |
| Authn/authz | Intentionally absent (spec) |
| Agent safety / destructive scripts | No force-push / secret-print patterns in product path |

## Evidence

### Path traversal — `/media/{asset_id:path}`

`src/media_search/api/app.py` `media_file`:

1. Resolves only after `metadata.get(asset_id)` (unknown IDs → 404).
2. `(media_root / asset_id).resolve()` then `path.relative_to(root)` → 400 on escape.

Empirical:

| Request | Status | Notes |
|---------|--------|-------|
| `/media/ok.png` (in-root asset) | 200 | Baseline |
| `/media/%2e%2e/secret.txt` (tampered id in metadata) | **400** `invalid asset path` | Guard fires |
| `/media/../secret.txt` | 404 | Router normalizes; not served |

### Path traversal — `/thumbnails/{frame_key:path}`

`frame_cache_path` (`application/frame_paths.py`; moved from
`adapters/frame_cache.py`, same sanitization) strips non `[A-Za-z0-9._-]` to
`_`, so `../` cannot become a path separator. Endpoint also
`resolve()` + `relative_to(frame_root)` in `api/app.py`.

Empirical: `/thumbnails/../../../secret.txt` → 404 (no file under sanitized
name); sanitized map of `../../../etc/passwd` →
`frames/.._.._.._etc_passwd.jpg` **under** `frame_root`.

### Import path handling

- `POST /api/import?path=` takes an absolute/relative filesystem path and walks
  it (`ImportDirectory.execute` → `resolve()` + `is_dir()`).
- Asset IDs are `path.resolve().relative_to(import_root)` — outside-root
  symlink targets fail `relative_to` and land in skip summary.
- **Residual:** any caller who can reach the HTTP API can ask the process to
  read/import any directory the OS user can access. Intended for local
  operator; **not** safe if bound beyond loopback without a trust boundary.

Default process bind: `HOST` defaults to `127.0.0.1` (`main.py`). Docker
`CMD` / compose publish `0.0.0.0:8000` and `8000:8000` — LAN-reachable if the
host firewall allows. Documented residual for local compose use.

### ffmpeg / ffprobe injection

`media_probe.probe_video` / `extract_frame_jpeg`: `subprocess.run(cmd, ...)`
with **argument list** (no `shell=True`). Inputs are `Path` objects from the
import walk and a float timestamp (`f"{ts:.3f}"`). No shell metacharacter
injection sink observed. Repo-wide: no `shell=True` / `os.system` in product
code.

### Secrets

- No `.env`, credential, or key files in the tree.
- Config is env vars for paths / embedder mode only (`MEDIA_SEARCH_*`,
  `EMBEDDER`, `HOST`/`PORT`).
- `rules/security.md`: secret scanning / dependency vulns
  `NOT_CONFIGURED` → SKIP (harness), not a product secret leak.

### SQL / data stores

`SqliteMetadataRepository` / `SqliteVecSearch` use `?` placeholders for
user-influenced values (`asset_id`, `frame_key`, embeddings). No string-built
SQL for those fields.

### Authn / authz

Absent by Acceptance / Requirements. Not a FAIL for 001.

## Residual risk (accepted for local-only)

1. **Unauthenticated HTTP surface** — search, import, media, thumbnails open to
   anyone who can reach the port. OK for single operator; FAIL if multi-tenant.
2. **Compose publishes port 8000 on all host interfaces** — prefer localhost
   publish or firewall when on untrusted LAN.
3. **Import API = filesystem read as the service user** — operator trust; do not
   expose without auth / path allowlist in later features.
4. **Minimal UI `innerHTML` interpolation** of `asset_id` / tags / frame keys —
   self-XSS if a hostile filename is imported; low for operator-controlled
   corpora; harden before untrusted multi-user content.
5. **Secret / dependency scanners unconfigured** — process SKIP per
   `rules/security.md`; re-evaluate before cloud/shared deployment (002).

## Blocking issues

None within the 001 threat model.
