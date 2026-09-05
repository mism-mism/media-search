"""Domain rules for representative video frames."""

from __future__ import annotations

from dataclasses import dataclass

# Spec constants
MAX_REPRESENTATIVE_FRAMES = 3
SHORT_VIDEO_THRESHOLD_SECONDS = 5.0


@dataclass(frozen=True)
class FrameSample:
    """A sampling point expressed as a fraction of duration in [0, 1]."""

    position: float  # 0.0 .. 1.0 inclusive


def representative_frame_positions(duration_seconds: float) -> list[FrameSample]:
    """
    Deterministic frame positions for a video.

    - duration < 5s → one middle frame (0.5)
    - duration >= 5s → up to 3 uniformly spaced positions including ends
    """
    if duration_seconds < 0:
        raise ValueError("duration_seconds must be >= 0")
    if duration_seconds < SHORT_VIDEO_THRESHOLD_SECONDS:
        return [FrameSample(0.5)]
    if MAX_REPRESENTATIVE_FRAMES == 1:
        return [FrameSample(0.5)]
    n = MAX_REPRESENTATIVE_FRAMES
    # Uniform including endpoints: 0, 0.5, 1 for n=3
    return [FrameSample(i / (n - 1)) for i in range(n)]
