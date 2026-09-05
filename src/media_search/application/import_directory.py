from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from media_search.application.frame_paths import frame_cache_path
from media_search.domain.formats import classify_path
from media_search.domain.frames import (
    MAX_REPRESENTATIVE_FRAMES,
    representative_frame_positions,
)
from media_search.domain.media_asset import MediaType
from media_search.ports.embedding import EmbeddingPort
from media_search.ports.media_probe import MediaProbePort
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
    ) -> None:
        self._embedder = embedder
        self._vectors = vectors
        self._metadata = metadata
        self._media_probe = media_probe
        self._work_dir = work_dir

    def execute(self, import_root: Path) -> ImportSummary:
        root = import_root.resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"import root not found: {root}")

        summary = ImportSummary()
        paths = sorted(p for p in root.rglob("*") if p.is_file())
        # ignore sidecar json
        paths = [p for p in paths if not p.name.endswith(".meta.json")]

        for path in paths:
            kind = classify_path(path)
            if kind is None:
                summary.skipped.append(
                    ImportWarning(path=str(path), reason="unsupported format")
                )
                continue
            try:
                existed = self._metadata.get(
                    path.resolve().relative_to(root).as_posix()
                )
                asset = self._media_probe.build_asset(path, import_root=root)
                self._vectors.delete_asset_frames(asset.asset_id)
                self._index_frames(path, asset)
                self._metadata.upsert(asset)
                if existed:
                    summary.updated.append(asset.asset_id)
                else:
                    summary.imported.append(asset.asset_id)
            except Exception as exc:  # noqa: BLE001 — collect per-file failures
                # Avoid orphan vectors from a half-finished index attempt.
                try:
                    asset_id = path.resolve().relative_to(root).as_posix()
                    self._vectors.delete_asset_frames(asset_id)
                except Exception:  # noqa: BLE001
                    pass
                summary.skipped.append(
                    ImportWarning(path=str(path), reason=f"import failed: {exc}")
                )
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
        if self._work_dir is not None:
            frame_root = Path(self._work_dir) / "frames"
            frame_root.mkdir(parents=True, exist_ok=True)
            own_tmp = False
        else:
            frame_root = Path(tempfile.mkdtemp())
            own_tmp = True
        try:
            self._clear_frame_jpegs(frame_root, asset.asset_id)
            for i, pos in enumerate(positions):
                frame_key = f"{asset.asset_id}::{i}"
                frame_path = frame_cache_path(frame_root, frame_key)
                self._media_probe.extract_frame_jpeg(
                    path,
                    position=pos,
                    duration_seconds=duration,
                    dest=frame_path,
                )
                vec = self._embedder.embed_image(frame_path.read_bytes())
                self._vectors.upsert_frame(
                    asset_id=asset.asset_id,
                    frame_key=frame_key,
                    position=pos,
                    vector=vec.tolist(),
                )
        finally:
            if own_tmp:
                shutil.rmtree(frame_root, ignore_errors=True)

    @staticmethod
    def _clear_frame_jpegs(frame_root: Path, asset_id: str) -> None:
        for i in range(MAX_REPRESENTATIVE_FRAMES):
            path = frame_cache_path(frame_root, f"{asset_id}::{i}")
            if path.is_file():
                path.unlink()
