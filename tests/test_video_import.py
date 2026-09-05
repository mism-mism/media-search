from __future__ import annotations

import subprocess
from pathlib import Path

from media_search.adapters.local_media_storage import LocalMediaStorage
from media_search.adapters.media_probe import LocalMediaProbe, probe_video
from media_search.adapters.memory_store import InMemoryMetadataRepository, InMemoryVectorSearch
from media_search.application.frame_paths import frame_cache_path
from media_search.application.import_directory import ImportDirectory
from media_search.domain.frames import (
    SHORT_VIDEO_THRESHOLD_SECONDS,
    representative_frame_positions,
)
from media_search.ports.embedding import FakeEmbedder


def _make_mp4(path: Path, duration: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # solid color video via lavfi
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=blue:s=64x64:d={duration}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-t",
        str(duration),
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def test_short_video_imports_one_frame(tmp_path: Path):
    incoming = tmp_path / "incoming"
    video = incoming / "short.mp4"
    _make_mp4(video, 2.0)
    dur = probe_video(video)[4]
    assert dur < SHORT_VIDEO_THRESHOLD_SECONDS
    assert [s.position for s in representative_frame_positions(dur)] == [0.5]

    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    work = tmp_path / "work"
    from media_search.adapters.local_frame_store import LocalFrameStore

    frames = LocalFrameStore(work / "frames")
    summary = ImportDirectory(
        embedder=embedder,
        vectors=vectors,
        metadata=meta,
        media_probe=LocalMediaProbe(),
        work_dir=work,
        frame_store=frames,
    ).execute_storage(LocalMediaStorage(incoming))
    assert summary.imported == ["short.mp4"]
    # one frame key present in vector store
    assert len(vectors._frames) == 1
    assert frame_cache_path(work / "frames", "short.mp4::0").is_file()


def test_long_video_imports_three_frames(tmp_path: Path):
    incoming = tmp_path / "incoming"
    _make_mp4(incoming / "long.mp4", 6.0)
    embedder = FakeEmbedder()
    meta = InMemoryMetadataRepository()
    vectors = InMemoryVectorSearch()
    from media_search.adapters.local_frame_store import LocalFrameStore

    work = tmp_path / "work"
    ImportDirectory(
        embedder=embedder,
        vectors=vectors,
        metadata=meta,
        media_probe=LocalMediaProbe(),
        work_dir=work,
        frame_store=LocalFrameStore(work / "frames"),
    ).execute_storage(LocalMediaStorage(incoming))
    assert len(vectors._frames) == 3
