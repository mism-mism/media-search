from typing import Protocol, Sequence

from media_search.domain.categories import ReferenceCategory, CategoryReport


class CategoryClassificationError(Exception):
    """Provider failure; application exposes only a fixed safe code."""


class CategoryClassifierPort(Protocol):
    def classify(self, image_bytes: bytes, categories: Sequence[ReferenceCategory]) -> CategoryReport: ...


class CategoryRepositoryPort(Protocol):
    def list_all(self) -> list[ReferenceCategory]: ...
    def create(self, category: ReferenceCategory) -> None:
        """Atomically register and invalidate all previous asset reports."""
        ...
    def delete(self, category_id: str) -> None:
        """Atomically remove and invalidate previous asset reports."""
        ...
