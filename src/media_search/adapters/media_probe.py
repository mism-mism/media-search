from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image

from media_search.domain.formats import classify_path
from media_search.domain.frames import representative_frame_positions
from media_search.domain.media_asset import MediaAsset, MediaType


@dataclass
class SidecarMeta:
    tags: list[str]
    description: str
    product_id: Optional[str] = None


def load_sidecar(path: Path) -> SidecarMeta:
    """Optional `{filename}.meta.json` next to the media file."""
    candidate = path.parent / f"{path.name}.meta.json"
    if not candidate.is_file():
        return SidecarMeta(tags=[], description="")
    data = json.loads(candidate.read_text(encoding="utf-8"))
    tags = data.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    desc = data.get("description") or ""
    raw_pid = data.get("product_id")
    product_id = str(raw_pid).strip() if raw_pid else None
    if product_id == "":
        product_id = None
    return SidecarMeta(
        tags=[str(t) for t in tags],
        description=str(desc),
        product_id=product_id,
    )


def probe_image(path: Path) -> tuple[str, int, Optional[int], Optional[int]]:
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    with Image.open(path) as img:
        width, height = img.size
    size = path.stat().st_size
    return mime, size, width, height


def probe_video(path: Path) -> tuple[str, int, Optional[int], Optional[int], float]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,duration:format=duration",
        "-of",
        "json",
        str(path),
    ]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    payload = json.loads(proc.stdout)
    streams = payload.get("streams") or [{}]
    stream = streams[0]
    fmt = payload.get("format") or {}
    width = stream.get("width")
    height = stream.get("height")
    duration_raw = stream.get("duration") or fmt.get("duration") or 0
    duration = float(duration_raw)
    size = path.stat().st_size
    return "video/mp4", size, width, height, duration


def build_asset(path: Path, *, import_root: Path) -> MediaAsset:
    kind = classify_path(path)
    if kind is None:
        raise ValueError(f"unsupported format: {path}")
    asset_id = path.resolve().relative_to(import_root.resolve()).as_posix()
    sidecar = load_sidecar(path)
    if kind == "image":
        mime, size, width, height = probe_image(path)
        return MediaAsset(
            asset_id=asset_id,
            media_type=MediaType.IMAGE,
            mime_type=mime,
            size_bytes=size,
            width=width,
            height=height,
            tags=list(sidecar.tags),
            description=sidecar.description,
            product_id=sidecar.product_id,
        )
    mime, size, width, height, duration = probe_video(path)
    return MediaAsset(
        asset_id=asset_id,
        media_type=MediaType.VIDEO,
        mime_type=mime,
        size_bytes=size,
        width=width,
        height=height,
        duration_seconds=duration,
        tags=list(sidecar.tags),
        description=sidecar.description,
        product_id=sidecar.product_id,
    )


def extract_frame_jpeg(path: Path, *, position: float, duration_seconds: float, dest: Path) -> None:
    """Extract one JPEG frame at fractional position using ffmpeg."""
    if duration_seconds <= 0:
        ts = 0.0
    else:
        # Stay off the exact EOF; some H.264 files fail seeking to the last packet.
        safe_end = max(duration_seconds - 0.05, 0.0)
        ts = min(max(position, 0.0), 1.0) * duration_seconds
        ts = min(ts, safe_end)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{ts:.3f}",
        "-i",
        str(path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(dest),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def plan_video_frames(duration_seconds: float) -> list[float]:
    return [p.position for p in representative_frame_positions(duration_seconds)]


class LocalMediaProbe:
    """Local ffmpeg/Pillow implementation of MediaProbePort."""

    def build_asset(self, path: Path, *, import_root: Path) -> MediaAsset:
        return build_asset(path, import_root=import_root)

    def extract_frame_jpeg(
        self,
        path: Path,
        *,
        position: float,
        duration_seconds: float,
        dest: Path,
    ) -> None:
        extract_frame_jpeg(
            path,
            position=position,
            duration_seconds=duration_seconds,
            dest=dest,
        )
