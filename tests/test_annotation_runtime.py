import importlib

import pytest
from PIL import Image

from media_search.domain.media_asset import ImageAnnotation


@pytest.fixture
def runtime_module(monkeypatch, tmp_path):
    for key in ("MEDIA_SEARCH_DB_GCS", "CLOUD_RUN_IMPORT_JOB", "IMPORT_JOB_BACKEND"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MEDIA_SEARCH_DATA", str(tmp_path))
    monkeypatch.setenv("EMBEDDER", "fake")
    monkeypatch.setenv("MEDIA_BACKEND", "local")
    monkeypatch.setenv("FRAME_BACKEND", "local")
    monkeypatch.setenv("IMPORT_LOCK_BACKEND", "fs")
    monkeypatch.setenv("IMAGE_ANNOTATION_BACKEND", "off")
    return importlib.import_module("media_search.main")


def test_annotations_disabled_by_default(runtime_module, monkeypatch):
    monkeypatch.delenv("IMAGE_ANNOTATION_BACKEND")
    assert runtime_module._build_annotator() is None


def test_gemini_configuration_requires_project(runtime_module, monkeypatch):
    monkeypatch.setenv("IMAGE_ANNOTATION_BACKEND", "gemini")
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    with pytest.raises(ValueError, match="GOOGLE_CLOUD_PROJECT"):
        runtime_module._build_annotator()


def test_runtime_import_uses_configured_annotation_adapter(runtime_module, monkeypatch, tmp_path):
    from media_search.adapters.gemini_annotator import GeminiImageAnnotator
    monkeypatch.setenv("IMAGE_ANNOTATION_BACKEND", "gemini")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setattr(GeminiImageAnnotator, "annotate", lambda self, raw: ImageAnnotation(tags=("白い背景",), description="白い画像。", model_id="test", prompt_version="v1"))
    incoming = tmp_path / "incoming"
    incoming.mkdir(exist_ok=True)
    Image.new("RGB", (8, 8), "white").save(incoming / "test.png")
    runtime = runtime_module.build_runtime()
    runtime.importer.execute_storage(runtime.media_storage)
    assert runtime.metadata.get("test.png").annotation.tags == ("白い背景",)


def test_gemini_api_key_needs_no_project_and_feeds_annotator_and_classifier(runtime_module, monkeypatch):
    from media_search.adapters.gemini_annotator import GeminiImageAnnotator
    monkeypatch.setenv("IMAGE_ANNOTATION_BACKEND", "gemini")
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    built = []
    original = GeminiImageAnnotator.__init__
    monkeypatch.setattr(GeminiImageAnnotator, "__init__", lambda self, **kw: built.append(kw) or original(self, **kw))
    runtime = runtime_module.build_runtime()
    assert runtime.categories is not None
    assert len(built) == 2, "annotator and category classifier share the transport"
    assert all(kw.get("api_key") == "test-key" and "project" not in kw for kw in built)
    assert all(GeminiImageAnnotator(**kw)._url.startswith("https://generativelanguage.googleapis.com/") for kw in built)
