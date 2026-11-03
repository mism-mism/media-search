"""Spec 020 AC2/AC3: the dispatcher's CLI (search / import, --json) over the resident API."""
import base64
import importlib
import json
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from media_search import cli


@pytest.fixture
def fetch(monkeypatch, tmp_path):
    """The real app (fake embedder, local adapters) behind the CLI's fetch hook."""
    for key in ("MEDIA_SEARCH_DB_GCS", "CLOUD_RUN_IMPORT_JOB", "IMPORT_JOB_BACKEND", "GEMINI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MEDIA_SEARCH_DATA", str(tmp_path))
    monkeypatch.setenv("EMBEDDER", "fake")
    monkeypatch.setenv("MEDIA_BACKEND", "local")
    monkeypatch.setenv("FRAME_BACKEND", "local")
    monkeypatch.setenv("IMPORT_LOCK_BACKEND", "fs")
    monkeypatch.setenv("IMAGE_ANNOTATION_BACKEND", "off")
    monkeypatch.setenv("IMPORT_SYNC", "1")
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    Image.new("RGB", (1600, 900), "white").save(incoming / "white <bottle>.png")
    Image.new("RGB", (40, 40), "black").save(incoming / "black.jpg")
    client = TestClient(importlib.import_module("media_search.main").build_app())

    def call(method, path):
        response = client.request(method, path)
        if response.status_code >= 400:
            raise cli.ApiError(response.status_code)
        return response.content

    return call


def run(capsys, argv, fetch):
    code = cli.main(argv, fetch=fetch)
    return code, capsys.readouterr().out


def test_import_then_search_returns_thumbnails_and_one_escaped_html_page(capsys, fetch):
    code, out = run(capsys, ["import", "--json"], fetch)
    assert code == 0
    summary = json.loads(out)
    assert sorted(summary["imported"]) == ["black.jpg", "white <bottle>.png"] and summary["updated"] == [] and summary["skipped"] == [], "same lists as POST /api/import"

    code, out = run(capsys, ["search", "white <bottle>", "--top-k", "5", "--json"], fetch)
    assert code == 0
    result = json.loads(out)
    assert result["query"] == "white <bottle>"
    assert {h["asset_id"] for h in result["hits"]} == {"white <bottle>.png", "black.jpg"}
    hit = next(h for h in result["hits"] if h["asset_id"] == "white <bottle>.png")
    assert set(hit) == {"asset_id", "display_name", "media_type", "score", "tags", "thumbnail"}
    thumb = Image.open(BytesIO(base64.b64decode(hit["thumbnail"])))
    assert thumb.format == "JPEG" and max(thumb.size) <= cli.THUMBNAIL_PX
    page = result["html"]
    assert page.startswith("<!doctype html>") and "<script" not in page.lower()
    assert "white &lt;bottle&gt;" in page and "white <bottle>" not in page, "every text field is escaped"
    assert page.count("data:image/jpeg;base64,") == 2

    code, out = run(capsys, ["search", "white"], fetch)
    assert code == 0 and len(out.strip().splitlines()) == 2, "without --json, one line per hit"


def test_an_unreadable_thumbnail_leaves_that_hit_without_an_image(capsys):
    def fetch(method, path):
        if path.startswith("/api/search"):
            return json.dumps({"results": [{"asset_id": "v.mp4", "media_type": "video", "score": 0.5, "tags": [], "thumbnail_url": "/thumbnails/missing"}]}).encode()
        raise cli.ApiError(404)

    code, out = run(capsys, ["search", "x", "--json"], fetch)
    result = json.loads(out)
    assert code == 0 and result["hits"][0]["thumbnail"] == "" and "data:image" not in result["html"]


def test_generated_tags_are_escaped_in_the_page(capsys):
    def fetch(method, path):
        if path.startswith("/api/search"):
            return json.dumps({"results": [{"asset_id": "a.png", "media_type": "image", "score": 0.9, "tags": [], "thumbnail_url": "/media/a.png",
                                            "annotation": {"tags": ["<img src=x onerror=alert(1)>"]}}]}).encode()
        out = BytesIO()
        Image.new("RGB", (8, 8), "white").save(out, "PNG")
        return out.getvalue()

    code, out = run(capsys, ["search", "x", "--json"], fetch)
    page = json.loads(out)["html"]
    assert code == 0 and "&lt;img src=x onerror=alert(1)&gt;" in page and "<img src=x" not in page


def test_http_fetch_uses_media_search_api_and_maps_http_errors(monkeypatch):
    import urllib.error

    seen = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b"ok"

    def urlopen(request, timeout):
        seen.append((request.get_method(), request.full_url, timeout))
        if request.full_url.endswith("/missing"):
            raise urllib.error.HTTPError(request.full_url, 404, "nf", {}, None)
        return Response()

    monkeypatch.setenv("MEDIA_SEARCH_API", "http://127.0.0.1:9999/")
    monkeypatch.setattr(cli.urllib.request, "urlopen", urlopen)
    assert cli.http_fetch("POST", "/api/import") == b"ok"
    assert seen[0][:2] == ("POST", "http://127.0.0.1:9999/api/import")
    with pytest.raises(cli.ApiError) as caught:
        cli.http_fetch("GET", "/missing")
    assert caught.value.status == 404


def test_tags_merge_annotation_and_categories():
    hit = {"tags": ["a"], "annotation": {"tags": ["b", "a"]}, "category_report": {"tags": ["c"]}}
    assert cli._tags(hit) == ["a", "b", "c"]


def test_busy_lock_exits_75_and_failures_print_no_traceback(capsys, fetch):
    def busy(method, path):
        raise cli.ApiError(409)

    code, out = run(capsys, ["import", "--json"], busy)
    assert code == 75 and json.loads(out) == {"error": "import_busy"}, "EX_TEMPFAIL: the dispatcher retries later"

    def failed_job(method, path):
        return json.dumps({"job_id": "j1", "status": "failed", "error": "provider body"}).encode()

    code, out = run(capsys, ["import", "--json"], failed_job)
    assert code == 1 and json.loads(out) == {"error": "import_failed"}, "a failed job is not reported as an empty success"

    def broken(method, path):
        raise RuntimeError("provider said: secret body")

    code, out = run(capsys, ["search", "x", "--json"], broken)
    assert code == 1 and json.loads(out) == {"error": "RuntimeError"}, "no provider body or traceback on stdout"

    def down(method, path):
        raise cli.ApiError(503)

    code, out = run(capsys, ["search", "x", "--json"], down)
    assert code == 1 and json.loads(out) == {"error": "http_503"}

    code, out = run(capsys, ["search", "   ", "--json"], fetch)
    assert code == 2 and json.loads(out) == {"error": "empty_query"}


def test_import_waits_for_the_async_job(monkeypatch):
    replies = iter([{"job_id": "j/1", "status": "queued"}, {"job_id": "j/1", "status": "running"}, {"job_id": "j/1", "status": "succeeded", "imported": ["x.png"]}])
    seen = []

    def fake(method, path):
        seen.append((method, path))
        return json.dumps(next(replies)).encode()

    assert cli.import_media(fake, poll_s=0) == {"imported": ["x.png"], "updated": [], "skipped": []}
    assert seen == [("POST", "/api/import"), ("GET", "/api/import/jobs/j%2F1"), ("GET", "/api/import/jobs/j%2F1")]
