from __future__ import annotations

import os
import hashlib
import shutil
import tempfile
import threading
import uuid
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
from pathlib import Path

from media_search.domain.categories import catalog_version
from media_search.ports.categories import CategoryClassificationError, CategoryClassifierPort, CategoryRepositoryPort
from media_search.domain.formats import classify_path
from media_search.domain.frames import (
    MAX_REPRESENTATIVE_FRAMES,
    representative_frame_positions,
)
from media_search.domain.media_asset import MediaAsset, MediaType
from media_search.ports.embedding import EmbeddingPort
from media_search.ports.annotation import ImageAnnotationError, ImageAnnotationPort
from media_search.ports.frame_store import FrameStorePort
from media_search.ports.media_probe import MediaProbePort
from media_search.ports.media_storage import MediaStoragePort
from media_search.ports.search import MetadataRepositoryPort, VectorSearchPort


@dataclass
class ImportWarning:
    path: str
    reason: str


@dataclass
class ImportSummary:
    imported: list[str] = field(default_factory=list)
    skipped: list[ImportWarning] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)


@dataclass
class _PreparedAsset:
    key: str
    asset: MediaAsset
    existed: bool
    frames: list[tuple[str, float, list[float], bytes | None]] | None
    # frame_key, position, vector, optional jpeg for frame store


class ImportDirectory:
    def __init__(
        self,
        *,
        embedder: EmbeddingPort,
        vectors: VectorSearchPort,
        metadata: MetadataRepositoryPort,
        media_probe: MediaProbePort,
        work_dir: Path | None = None,
        frame_store: FrameStorePort | None = None,
        embed_workers: int | None = None,
        annotator: ImageAnnotationPort | None = None,
        max_annotations: int = 50,
        categories: CategoryRepositoryPort | None = None,
        classifier: CategoryClassifierPort | None = None,
        max_classifications: int = 50,
    ) -> None:
        self._embedder = embedder
        self._vectors = vectors
        self._metadata = metadata
        self._media_probe = media_probe
        self._work_dir = work_dir
        self._frame_store = frame_store
        self._annotator = annotator
        self._categories = categories
        self._classifier = classifier
        if max_classifications < 1:
            raise ValueError("max_classifications must be positive")
        self._max_classifications = max_classifications
        if max_annotations < 1:
            raise ValueError("max_annotations must be positive")
        self._max_annotations = max_annotations
        if embed_workers is None:
            embed_workers = int(os.environ.get("IMPORT_EMBED_WORKERS", "4"))
        self._embed_workers = max(1, embed_workers)

    def execute_storage(
        self,
        storage: MediaStoragePort,
        *,
        only_keys: Sequence[str] | None = None,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> ImportSummary:
        summary = ImportSummary()
        stage = Path(self._work_dir) / "import-stage" if self._work_dir else Path(
            tempfile.mkdtemp()
        )
        own_stage = self._work_dir is None
        stage.mkdir(parents=True, exist_ok=True)
        if only_keys is not None:
            keys = [k for k in only_keys if storage.exists(k)]
        else:
            keys = storage.list_media_keys()
        total = len(keys)
        processed = 0
        annotation_count = 0
        classification_count = 0
        categories = tuple(self._categories.list_all()) if self._categories and self._classifier else ()
        annotation_lock = threading.Lock()

        def claim_annotation() -> bool:
            nonlocal annotation_count
            with annotation_lock:
                if annotation_count >= self._max_annotations:
                    return False
                annotation_count += 1
                return True

        def claim_classification() -> bool:
            nonlocal classification_count
            with annotation_lock:
                if classification_count >= self._max_classifications:
                    return False
                classification_count += 1
                return True

        def _bump() -> None:
            nonlocal processed
            processed += 1
            if on_progress is not None:
                on_progress(processed, total)

        try:
            with ThreadPoolExecutor(max_workers=self._embed_workers) as pool:
                futures = {
                    pool.submit(self._prepare_one, storage, stage, key, claim_annotation, categories, claim_classification): key
                    for key in keys
                }
                for fut in as_completed(futures):
                    key = futures[fut]
                    try:
                        result = fut.result()
                    except Exception as exc:  # noqa: BLE001
                        # Preparation has not written frames. Keep any previous
                        # searchable version when materialization/enrichment fails.
                        summary.skipped.append(
                            ImportWarning(path=key, reason=f"import failed: {exc}")
                        )
                        _bump()
                        continue

                    if isinstance(result, ImportWarning):
                        summary.skipped.append(result)
                        _bump()
                        continue

                    assert isinstance(result, _PreparedAsset)
                    # Single-writer path: upsert frames + metadata serially.
                    try:
                        if result.frames is not None:
                            self._vectors.delete_asset_frames(result.asset.asset_id)
                            if self._frame_store is not None:
                                self._frame_store.delete_prefix(
                                    result.asset.asset_id,
                                    max_frames=MAX_REPRESENTATIVE_FRAMES,
                                )
                            for frame_key, position, vector, jpeg in result.frames:
                                if jpeg is not None and self._frame_store is not None:
                                    self._frame_store.put_jpeg(frame_key, jpeg)
                                self._vectors.upsert_frame(
                                    asset_id=result.asset.asset_id,
                                    frame_key=frame_key,
                                    position=position,
                                    vector=vector,
                                )
                        self._metadata.upsert(result.asset)
                        if result.existed:
                            summary.updated.append(result.asset.asset_id)
                        else:
                            summary.imported.append(result.asset.asset_id)
                    except Exception as exc:  # noqa: BLE001
                        if result.frames is not None:
                            try:
                                self._vectors.delete_asset_frames(key)
                            except Exception:  # noqa: BLE001
                                pass
                        summary.skipped.append(
                            ImportWarning(path=key, reason=f"import failed: {exc}")
                        )
                    _bump()
        finally:
            if own_stage:
                shutil.rmtree(stage, ignore_errors=True)
        return summary

    def _needs_embed(
        self, storage: MediaStoragePort, key: str
    ) -> tuple[bool, MediaAsset | None, str | None]:
        """Return (needs_work, existed_meta, skip_reason_if_any)."""
        kind = classify_path(Path(key))
        if kind is None:
            return False, None, "unsupported format"
        existed = self._metadata.get(key)
        has_vec = self._vectors.has_frames(key)
        if existed is not None and has_vec:
            try:
                size_bytes = storage.size_bytes(key)
            except FileNotFoundError:
                return False, existed, "missing object"
            if existed.size_bytes == size_bytes:
                return False, existed, "unchanged"
        return True, existed, None

    def _prepare_one(
        self,
        storage: MediaStoragePort,
        stage: Path,
        key: str,
        claim_annotation: Callable[[], bool],
        categories,
        claim_classification: Callable[[], bool],
    ) -> _PreparedAsset | ImportWarning:
        needs, existed, skip_reason = self._needs_embed(storage, key)
        annotation_only = (
            not needs and skip_reason == "unchanged" and self._annotator is not None
            and existed is not None and existed.media_type == MediaType.IMAGE
            and existed.annotation is None
        )
        # Catalog-enabled images must be read to validate the source fingerprint,
        # even when legacy embedding detection considers their byte length unchanged.
        classification_only = (not needs and skip_reason == "unchanged" and existed is not None
                               and existed.media_type == MediaType.IMAGE and bool(categories))
        metadata_only = annotation_only or classification_only
        if not needs and not metadata_only:
            return ImportWarning(path=key, reason=skip_reason or "unchanged")

        worker_stage = stage / f"w-{uuid.uuid4().hex}"
        worker_stage.mkdir(parents=True, exist_ok=True)
        try:
            with storage.materialize(key, worker_stage) as local_path:
                image_bytes = local_path.read_bytes() if categories and classify_path(Path(key)) == "image" else None
                image_sha256 = hashlib.sha256(image_bytes).hexdigest() if image_bytes is not None else ""
                source_changed = bool(existed and existed.category_report and existed.category_report.image_sha256
                                      and image_sha256 and existed.category_report.image_sha256 != image_sha256)
                if source_changed:
                    metadata_only = False
                asset = self._media_probe.build_asset(
                    local_path, import_root=local_path.parent
                )
                asset = replace(asset, asset_id=key)
                if existed is not None:
                    asset = replace(
                        asset,
                        folder_id=existed.folder_id,
                        display_name=existed.display_name or Path(key).name,
                        tags=existed.tags or asset.tags,
                        description=existed.description or asset.description,
                        product_id=existed.product_id or asset.product_id,
                    )
                else:
                    asset = replace(asset, display_name=Path(key).name)

                if metadata_only:
                    asset = existed
                elif existed is not None and existed.size_bytes == asset.size_bytes and not source_changed:
                    asset = replace(asset, annotation=existed.annotation, annotation_error=existed.annotation_error,
                                    category_report=existed.category_report, category_error=existed.category_error)

                classification_needed = bool(categories) and asset.media_type == MediaType.IMAGE and (
                    asset.category_report is None or asset.category_report.catalog_version != catalog_version(categories)
                    or asset.category_report.image_sha256 != image_sha256
                )
                if metadata_only and not classification_needed and (self._annotator is None or asset.annotation is not None):
                    return ImportWarning(path=key, reason="unchanged")
                frames = None if metadata_only else self._embed_frames(local_path, asset)
                if self._annotator is not None and asset.media_type == MediaType.IMAGE and asset.annotation is None:
                    if claim_annotation():
                        try:
                            generated = self._annotator.annotate(local_path.read_bytes())
                            asset = replace(asset, annotation=generated, annotation_error="")
                        except ImageAnnotationError:
                            asset = replace(asset, annotation=None, annotation_error="generation_failed")
                    else:
                        asset = replace(asset, annotation=None, annotation_error="limit_reached")
                if classification_needed:
                    asset = replace(asset, category_report=None, category_error="")
                    if claim_classification():
                        try:
                            report = self._classifier.classify(image_bytes, categories)
                            asset = replace(asset, category_report=replace(report, image_sha256=image_sha256))
                        except CategoryClassificationError:
                            asset = replace(asset, category_error="classification_failed")
                    else:
                        asset = replace(asset, category_error="limit_reached")
                return _PreparedAsset(
                    key=key,
                    asset=asset,
                    existed=existed is not None,
                    frames=frames,
                )
        finally:
            shutil.rmtree(worker_stage, ignore_errors=True)

    def _embed_frames(
        self, path: Path, asset: MediaAsset
    ) -> list[tuple[str, float, list[float], bytes | None]]:
        if asset.media_type == MediaType.IMAGE:
            image_bytes = path.read_bytes()
            vec = self._embedder.embed_image(image_bytes)
            return [
                (f"{asset.asset_id}::0", 0.0, vec.tolist(), None),
            ]

        duration = float(asset.duration_seconds or 0.0)
        positions = [s.position for s in representative_frame_positions(duration)]
        out: list[tuple[str, float, list[float], bytes | None]] = []
        for i, pos in enumerate(positions):
            frame_key = f"{asset.asset_id}::{i}"
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                dest = Path(tmp.name)
            try:
                self._media_probe.extract_frame_jpeg(
                    path,
                    position=pos,
                    duration_seconds=duration,
                    dest=dest,
                )
                jpeg = dest.read_bytes()
                vec = self._embedder.embed_image(jpeg)
                store_bytes = jpeg if self._frame_store is not None else None
                out.append((frame_key, pos, vec.tolist(), store_bytes))
            finally:
                dest.unlink(missing_ok=True)
        return out
