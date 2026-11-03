# Run on EC2 (spec 020)

The shared EC2 box (mk2-harness) runs the search service next to the article
studio. Users, systemd units, proxies and the dispatcher table live in
[mism-mism/mk2-harness](https://github.com/mism-mism/mk2-harness) (`ops/ec2/`);
this page lists only what the app needs.

## Layout

| What | Where | Owner |
|---|---|---|
| Code and venv | `/opt/media-search` (pinned commit, read-only) | root |
| Data (originals, DB, frames, jobs, lock) | `/srv/media/` | `media` 750 |
| Secrets | `/etc/media/media.env` | root:media 640 |

## Environment

```bash
MEDIA_SEARCH_DATA=/srv/media
MEDIA_SEARCH_MEDIA_ROOT=/srv/media/incoming
MEDIA_SEARCH_DB=/srv/media/media-local-cos.db
EMBEDDER=local
MEDIA_BACKEND=local
FRAME_BACKEND=local
IMPORT_LOCK_BACKEND=fs
IMAGE_ANNOTATION_BACKEND=gemini
IMAGE_ANNOTATION_MODEL=gemini-3.1-flash-lite
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
# media.env (the operator writes it): GEMINI_API_KEY=<AI Studio key>
```

Install with `pip install ".[semantic,gemini-key]"` (CPU torch first): without the
`gemini-key` extra (`requests`) the service starts but every annotation fails as
`generation_failed`.

Leave out `MEDIA_SEARCH_DB_GCS`, `GCS_BUCKET`, `CLOUD_RUN_IMPORT_JOB`,
`IMPORT_JOB_BACKEND` and `GOOGLE_CLOUD_PROJECT`. With `GEMINI_API_KEY` set,
annotation and category classification call
`generativelanguage.googleapis.com` with the key in a header (no ADC, no
project). The `media` user's proxy must allow that host.

## CLI

The dispatcher calls the CLI as the `media` user; it never reads `/srv/media`.
The CLI loads no model: it calls the resident service at `MEDIA_SEARCH_API`
(default `http://127.0.0.1:3200`, socket-activated on EC2).

```bash
python -m media_search.cli search "白いボトル" --top-k 10 --json
python -m media_search.cli import --json
```

- `search --json` → `{query, hits: [{asset_id, display_name, media_type, score, tags, thumbnail}], html}`.
  `thumbnail` is a base64 JPEG (≤ 512 px); `html` is one self-contained page.
- `import --json` → `{imported, updated, skipped}`. Exit 75 with `{error: "import_busy"}` when
  another import holds the lock; other failures exit 1 with `{error}` only.

Video import needs `ffmpeg`/`ffprobe` on PATH; the current data is images only.

## Rollback

The GCS data was not copied (clarify.md D4): EC2 starts empty and GCS keeps the
old library. Rolling back means redeploying Cloud Run (`make deploy`) against GCS;
images and tags imported on EC2 are not carried back. Keep the GCS bucket until
the operator decides the old library is no longer needed.
