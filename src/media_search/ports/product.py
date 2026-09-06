from __future__ import annotations

from typing import Optional, Protocol

from media_search.domain.product import Product


class ProductRepositoryPort(Protocol):
    def upsert(self, product: Product) -> None: ...

    def get(self, product_id: str) -> Optional[Product]: ...

    def list_all(self) -> list[Product]: ...

    def delete(self, product_id: str) -> None: ...
