from dataclasses import replace

from PIL import Image

from media_search.adapters.local_media_storage import LocalMediaStorage
from media_search.adapters.media_probe import LocalMediaProbe
from media_search.adapters.memory_store import InMemoryMetadataRepository, InMemoryVectorSearch
from media_search.application.import_directory import ImportDirectory
from media_search.domain.media_asset import ImageAnnotation
from media_search.ports.annotation import ImageAnnotationError
from media_search.ports.embedding import FakeEmbedder


class Annotator:
    def __init__(self, fail=False):
        self.calls = 0
        self.fail = fail

    def annotate(self, image_bytes):
        self.calls += 1
        if self.fail:
            raise ImageAnnotationError("generation_failed")
        return ImageAnnotation(tags=("白いボトル",), description="白い容器を持つ手。", model_id="fake", prompt_version="v1")


def setup_import(tmp_path, count=1):
    source = tmp_path / "source"
    source.mkdir()
    for i in range(count):
        Image.new("RGB", (12, 12), "white").save(source / f"{i}.png")
    meta, vectors, embedder = InMemoryMetadataRepository(), InMemoryVectorSearch(), FakeEmbedder()
    kwargs = dict(metadata=meta, vectors=vectors, embedder=embedder, media_probe=LocalMediaProbe(), embed_workers=4)
    return LocalMediaStorage(source), meta, vectors, kwargs


def test_import_generates_once_and_preserves_manual_metadata(tmp_path):
    storage, meta, vectors, kwargs = setup_import(tmp_path)
    ImportDirectory(**kwargs).execute_storage(storage)
    original = replace(meta.get("0.png"), tags=["広告"], description="手入力", product_id="sku", folder_id="folder", display_name="撮影")
    meta.upsert(original)
    before_frames = dict(vectors._frames)
    def no_reembed(_):
        raise AssertionError("annotation-only work must not re-embed")
    kwargs["embedder"].embed_image = no_reembed
    annotator = Annotator()
    importer = ImportDirectory(**kwargs, annotator=annotator)
    result = importer.execute_storage(storage)
    assert result.updated == ["0.png"]
    saved = meta.get("0.png")
    assert saved.annotation.tags == ("白いボトル",)
    assert replace(saved, annotation=None) == original
    assert all(vectors._frames[k] is v for k, v in before_frames.items())
    second = importer.execute_storage(storage)
    assert annotator.calls == 1
    assert second.skipped[0].reason == "unchanged"


def test_failure_keeps_new_vectors_and_retry_does_not_reembed(tmp_path):
    storage, meta, vectors, kwargs = setup_import(tmp_path)
    annotator = Annotator(fail=True)
    importer = ImportDirectory(**kwargs, annotator=annotator)
    result = importer.execute_storage(storage)
    assert result.imported == ["0.png"]
    assert vectors.has_frames("0.png")
    assert meta.get("0.png").annotation_status == "failed"
    annotator.fail = False
    before = vectors._frames["0.png::0"]
    importer.execute_storage(storage)
    assert meta.get("0.png").annotation_status == "ready"
    assert vectors._frames["0.png::0"] is before
    assert annotator.calls == 2


def test_concurrent_import_respects_per_run_request_cap(tmp_path):
    storage, meta, vectors, kwargs = setup_import(tmp_path, count=6)
    annotator = Annotator()
    importer = ImportDirectory(**kwargs, annotator=annotator, max_annotations=2)
    summary = importer.execute_storage(storage)
    assert len(summary.imported) == 6
    assert annotator.calls == 2
    assert sum(a.annotation_status == "deferred" for a in meta.list_all()) == 4
    assert all(vectors.has_frames(a.asset_id) for a in meta.list_all())
    importer.execute_storage(storage)
    assert annotator.calls == 4
    assert sum(a.annotation_status == "ready" for a in meta.list_all()) == 4


def test_changed_image_does_not_keep_stale_generated_words_on_failure(tmp_path):
    storage, meta, vectors, kwargs = setup_import(tmp_path)
    annotator = Annotator()
    importer = ImportDirectory(**kwargs, annotator=annotator)
    importer.execute_storage(storage)
    Image.new("RGB", (45, 35), "blue").save(tmp_path / "source" / "0.png")
    annotator.fail = True
    importer.execute_storage(storage)
    assert meta.get("0.png").annotation is None
    assert meta.get("0.png").annotation_status == "failed"
    assert vectors.has_frames("0.png")


def test_rebuilding_missing_vectors_reuses_successful_annotation(tmp_path):
    storage, meta, vectors, kwargs = setup_import(tmp_path)
    annotator = Annotator()
    importer = ImportDirectory(**kwargs, annotator=annotator)
    importer.execute_storage(storage)
    vectors.delete_asset_frames("0.png")
    importer.execute_storage(storage)
    assert vectors.has_frames("0.png")
    assert annotator.calls == 1
