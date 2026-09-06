from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


@dataclass(frozen=True)
class ImageAnnotation:
    tags: tuple[str, ...]
    description: str
    model_id: str
    prompt_version: str

    def __post_init__(self) -> None:
        if not 1 <= len(self.tags) <= 12 or any(
            not isinstance(t, str) or not t.strip() or len(t) > 40 for t in self.tags
        ):
            raise ValueError("annotation requires 1–12 tags of at most 40 characters")
        if not isinstance(self.description, str) or not self.description.strip() or len(self.description) > 300:
            raise ValueError("annotation description must be 1–300 characters")
        if not self.model_id or not self.prompt_version:
            raise ValueError("annotation provenance is required")


@dataclass
class MediaAsset:
    """Searchable media unit returned to users."""

    asset_id: str  # stable storage key (relative path)
    media_type: MediaType
    mime_type: str
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    tags: list[str] = field(default_factory=list)
    description: str = ""
    display_name: str = ""
    folder_id: Optional[str] = None
    product_id: Optional[str] = None
    annotation: Optional[ImageAnnotation] = None
    annotation_error: str = ""

    @property
    def search_tags(self) -> list[str]:
        generated = self.annotation.tags if self.annotation else ()
        return list(dict.fromkeys([*self.tags, *generated]))

    @property
    def annotation_status(self) -> str:
        if self.media_type != MediaType.IMAGE:
            return "not_applicable"
        if self.annotation:
            return "ready"
        if self.annotation_error == "limit_reached":
            return "deferred"
        return "failed" if self.annotation_error else "pending"


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
    match_kinds: tuple[str, ...] = ()
