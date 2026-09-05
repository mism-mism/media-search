from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
from pathlib import Path

from media_search.domain.formats import classify_path
from media_search.domain.frames import (
    MAX_REPRESENTATIVE_FRAMES,
    representative_frame_positions,
)
from media_search.domain.media_asset import MediaAsset, MediaType
from media_search.ports.embedding import EmbeddingPort
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
    frames: list[tuple[str, float, list[float], bytes | None]]
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
    ) -> None:
        self._embedder = embedder
        self._vectors = vectors
        self._metadata = metadata
        self._media_probe = media_probe
        self._work_dir = work_dir
        self._frame_store = frame_store
        if embed_workers is None:
            embed_workers = int(os.environ.get("IMPORT_EMBED_WORKERS", "4"))
        self._embed_workers = max(1, embed_workers)

    def execute_storage(
        self,
        storage: MediaStoragePort,
        *,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> ImportSummary:
        summary = ImportSummary()
        stage = Path(self._work_dir) / "import-stage" if self._work_dir else Path(
            tempfile.mkdtemp()
        )
        own_stage = self._work_dir is None
        stage.mkdir(parents=True, exist_ok=True)
        keys = storage.list_media_keys()
        total = len(keys)
        processed = 0

        def _bump() -> None:
            nonlocal processed
            processed += 1
            if on_progress is not None:
                on_progress(processed, total)

        try:
            with ThreadPoolExecutor(max_workers=self._embed_workers) as pool:
                futures = {
                    pool.submit(self._prepare_one, storage, stage, key): key
                    for key in keys
                }
                for fut in as_completed(futures):
                    key = futures[fut]
                    try:
                        result = fut.result()
                    except Exception as exc:  # noqa: BLE001
                        try:
                            self._vectors.delete_asset_frames(key)
                        except Exception:  # noqa: BLE001
                            pass
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

    def _prepare_one(
        self,
        storage: MediaStoragePort,
        stage: Path,
        key: str,
    ) -> _PreparedAsset | ImportWarning:
        kind = classify_path(Path(key))
        if kind is None:
            return ImportWarning(path=key, reason="unsupported format")

        existed = self._metadata.get(key)
        worker_stage = stage / f"w-{uuid.uuid4().hex}"
        worker_stage.mkdir(parents=True, exist_ok=True)
        try:
            with storage.materialize(key, worker_stage) as local_path:
                size_bytes = local_path.stat().st_size
                if (
                    existed is not None
                    and existed.size_bytes == size_bytes
                    and classify_path(Path(key)) is not None
                ):
                    return ImportWarning(path=key, reason="unchanged")

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

                frames = self._embed_frames(local_path, asset)
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
