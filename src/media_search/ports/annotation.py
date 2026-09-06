from typing import Protocol

from media_search.domain.media_asset import ImageAnnotation


class ImageAnnotationError(Exception):
    """Image description failed; provider details must not escape this boundary."""


class ImageAnnotationPort(Protocol):
    def annotate(self, image_bytes: bytes) -> ImageAnnotation:
        """Describe an image, or raise ImageAnnotationError with no private payload."""
        ...
