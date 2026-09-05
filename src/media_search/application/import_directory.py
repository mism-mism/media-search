from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path

from media_search.adapters.local_frame_store import LocalFrameStore
from media_search.domain.formats import classify_path
from media_search.domain.frames import (
    MAX_REPRESENTATIVE_FRAMES,
    representative_frame_positions,
)
from media_search.domain.media_asset import MediaType
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
    ) -> None:
        self._embedder = embedder
        self._vectors = vectors
        self._metadata = metadata
        self._media_probe = media_probe
        self._work_dir = work_dir
        if frame_store is not None:
            self._frame_store = frame_store
        elif work_dir is not None:
            self._frame_store = LocalFrameStore(work_dir / "frames")
        else:
            self._frame_store = None

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
        try:
            for idx, key in enumerate(keys, start=1):
                kind = classify_path(Path(key))
                if kind is None:
                    summary.skipped.append(
                        ImportWarning(path=key, reason="unsupported format")
                    )
                    if on_progress is not None:
                        on_progress(idx, total)
                    continue
                try:
                    existed = self._metadata.get(key)
                    with storage.materialize(key, stage) as local_path:
                        size_bytes = local_path.stat().st_size
                        if (
                            existed is not None
                            and existed.size_bytes == size_bytes
                            and classify_path(Path(key)) is not None
                        ):
                            # Differential: unchanged size → skip re-embed.
                            summary.skipped.append(
                                ImportWarning(path=key, reason="unchanged")
                            )
                            if on_progress is not None:
                                on_progress(idx, total)
                            continue
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
                            )
                        else:
                            asset = replace(asset, display_name=Path(key).name)
                        self._vectors.delete_asset_frames(asset.asset_id)
                        self._index_frames(local_path, asset)
                        self._metadata.upsert(asset)
                    if existed:
                        summary.updated.append(asset.asset_id)
                    else:
                        summary.imported.append(asset.asset_id)
                except Exception as exc:  # noqa: BLE001
                    try:
                        self._vectors.delete_asset_frames(key)
                    except Exception:  # noqa: BLE001
                        pass
                    summary.skipped.append(
                        ImportWarning(path=key, reason=f"import failed: {exc}")
                    )
                if on_progress is not None:
                    on_progress(idx, total)
        finally:
            if own_stage:
                shutil.rmtree(stage, ignore_errors=True)
        return summary

    def _index_frames(self, path: Path, asset) -> None:
        if asset.media_type == MediaType.IMAGE:
            image_bytes = path.read_bytes()
            vec = self._embedder.embed_image(image_bytes)
            self._vectors.upsert_frame(
                asset_id=asset.asset_id,
                frame_key=f"{asset.asset_id}::0",
                position=0.0,
                vector=vec.tolist(),
            )
            return

        duration = float(asset.duration_seconds or 0.0)
        positions = [s.position for s in representative_frame_positions(duration)]
        store = self._frame_store
        tmp_root: Path | None = None
        if store is None:
            tmp_root = Path(tempfile.mkdtemp())
            store = LocalFrameStore(tmp_root)
        try:
            store.delete_prefix(asset.asset_id, max_frames=MAX_REPRESENTATIVE_FRAMES)
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
                    store.put_jpeg(frame_key, jpeg)
                    vec = self._embedder.embed_image(jpeg)
                    self._vectors.upsert_frame(
                        asset_id=asset.asset_id,
                        frame_key=frame_key,
                        position=pos,
                        vector=vec.tolist(),
                    )
                finally:
                    dest.unlink(missing_ok=True)
        finally:
            if tmp_root is not None:
                shutil.rmtree(tmp_root, ignore_errors=True)
