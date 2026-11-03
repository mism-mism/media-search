"""Thin CLI for the harness dispatcher (spec 020): search and import, optionally as JSON.

It talks to the resident service (``MEDIA_SEARCH_API``, default http://127.0.0.1:3200)
instead of loading its own model: one OpenCLIP model per box (the load peak is >2.5 GB).
The dispatcher never reads the media folder, so ``search --json`` returns thumbnails and
one self-contained HTML page with the hits.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from io import BytesIO

from PIL import Image, ImageOps

THUMBNAIL_PX = 512
EXIT_BUSY = 75  # EX_TEMPFAIL: another import holds the lock
IMPORT_TIMEOUT_S = 3600


class ApiError(Exception):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"http_{status}")


class BusyError(Exception):
    pass


def http_fetch(method: str, path: str) -> bytes:
    base = os.environ.get("MEDIA_SEARCH_API", "http://127.0.0.1:3200").rstrip("/")
    request = urllib.request.Request(base + path, method=method)
    try:
        # The first request may start the service and warm the model.
        with urllib.request.urlopen(request, timeout=300) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise ApiError(exc.code) from None


def thumbnail(raw: bytes) -> str:
    """Base64 JPEG, at most THUMBNAIL_PX on the long side."""
    image = ImageOps.exif_transpose(Image.open(BytesIO(raw))).convert("RGB")
    image.thumbnail((THUMBNAIL_PX, THUMBNAIL_PX))
    out = BytesIO()
    image.save(out, "JPEG", quality=80)
    return base64.b64encode(out.getvalue()).decode("ascii")


def render_html(query: str, hits: list[dict]) -> str:
    """One page, no scripts, every text escaped, images as data URIs."""
    e = html.escape
    items = "".join(
        f'<figure><img src="data:image/jpeg;base64,{h["thumbnail"]}" alt="{e(h["display_name"])}">'
        f'<figcaption><strong>{i}. {e(h["display_name"])}</strong><br>{e(" / ".join(h["tags"][:6]))}'
        f'<br><small>{e(h["asset_id"])}・{h["score"]:.3f}</small></figcaption></figure>'
        for i, h in enumerate(hits, 1)
        if h["thumbnail"]
    )
    return (
        '<!doctype html><html lang="ja"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{e(query)} の検索結果</title><style>"
        "body{margin:0;padding:16px;font:15px/1.6 system-ui,sans-serif;color:#222;background:#f6f6f4}"
        "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}"
        "figure{margin:0;background:#fff;border:1px solid #ddd;border-radius:8px;overflow:hidden}"
        "img{display:block;width:100%;height:220px;object-fit:contain;background:#eee}"
        "figcaption{padding:8px;word-break:break-all}small{color:#666}"
        f"</style></head><body><h1>「{e(query)}」の検索結果（{len(hits)} 件）</h1><main>{items}</main></body></html>"
    )


def _tags(hit: dict) -> list[str]:
    generated = (hit.get("annotation") or {}).get("tags") or []
    categories = (hit.get("category_report") or {}).get("tags") or []
    return list(dict.fromkeys([*hit.get("tags", []), *generated, *categories]))


def _thumbnail_or_blank(fetch, url: str) -> str:
    """One unreadable thumbnail (a video without a frame, a broken file) must not fail the whole search."""
    try:
        return thumbnail(fetch("GET", url))
    except Exception:  # noqa: BLE001
        return ""


def search(fetch, query: str, top_k: int) -> dict:
    if not query.strip():
        raise ValueError("empty_query")
    params = urllib.parse.urlencode({"q": query, "top_k": top_k})
    results = json.loads(fetch("GET", f"/api/search?{params}"))["results"]
    rows = [
        {
            "asset_id": r["asset_id"],
            "display_name": r.get("display_name") or r["asset_id"],
            "media_type": r["media_type"],
            "score": round(float(r["score"]), 4),
            "tags": _tags(r),
            "thumbnail": _thumbnail_or_blank(fetch, r["thumbnail_url"]),
        }
        for r in results
    ]
    return {"query": query, "hits": rows, "html": render_html(query, rows)}


def import_media(fetch, *, poll_s: float = 2.0) -> dict:
    try:
        job = json.loads(fetch("POST", "/api/import"))
    except ApiError as exc:
        if exc.status == 409:
            raise BusyError() from None
        raise
    deadline = time.monotonic() + IMPORT_TIMEOUT_S
    while job.get("status") in ("queued", "running"):
        if time.monotonic() > deadline:
            raise TimeoutError("import_timeout")
        time.sleep(poll_s)
        job = json.loads(fetch("GET", f"/api/import/jobs/{urllib.parse.quote(job['job_id'], safe='')}"))
    if job.get("status") != "succeeded":
        raise RuntimeError("import_failed")
    return {"imported": job.get("imported", []), "updated": job.get("updated", []), "skipped": job.get("skipped", [])}


def main(argv: list[str] | None = None, fetch=http_fetch) -> int:
    parser = argparse.ArgumentParser(prog="media-search")
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("search", help="text search")
    s.add_argument("query")
    s.add_argument("--top-k", type=int, default=10, choices=range(1, 51), metavar="N")
    s.add_argument("--json", action="store_true")
    i = sub.add_parser("import", help="import the configured media root")
    i.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    def fail(code: int, error: str) -> int:
        print(json.dumps({"error": error}, ensure_ascii=False) if args.json else f"エラー: {error}", file=sys.stdout if args.json else sys.stderr)
        return code

    try:
        if args.command == "search":
            result = search(fetch, args.query, args.top_k)
            if args.json:
                print(json.dumps(result, ensure_ascii=False))
            else:
                for n, h in enumerate(result["hits"], 1):
                    print(f'{n}. {h["display_name"]}  {h["score"]:.3f}  {h["asset_id"]}  {" / ".join(h["tags"][:6])}')
        else:
            result = import_media(fetch)
            print(json.dumps(result, ensure_ascii=False) if args.json else f'取り込み {len(result["imported"])} 件、更新 {len(result["updated"])} 件、飛ばした {len(result["skipped"])} 件')
        return 0
    except BusyError:
        return fail(EXIT_BUSY, "import_busy")
    except (ApiError, TimeoutError, RuntimeError) as exc:
        # Only our own short codes (http_503, import_failed, ...); never a provider body
        known = str(exc) if str(exc).startswith(("http_", "import_")) else type(exc).__name__
        return fail(1, known)
    except ValueError as exc:
        return fail(2, "empty_query") if str(exc) == "empty_query" else fail(1, "ValueError")
    except Exception as exc:  # noqa: BLE001 — never print tracebacks or provider bodies
        return fail(1, type(exc).__name__)


if __name__ == "__main__":
    raise SystemExit(main())
