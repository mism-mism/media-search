from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


@dataclass
class MediaAsset:
    """Searchable media unit returned to users."""

    asset_id: str  # relative path from import root
    media_type: MediaType
    mime_type: str
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    tags: list[str] = field(default_factory=list)
    description: str = ""


@dataclass(frozen=True)
class FrameHit:
    frame_key: str
    score: float
    position: float


@dataclass(frozen=True)
class AssetSearchHit:
    asset: MediaAsset
    score: float
    best_frame: Optional[FrameHit] = None
