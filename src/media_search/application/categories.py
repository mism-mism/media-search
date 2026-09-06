from __future__ import annotations

import uuid
from contextlib import contextmanager
from collections.abc import Callable

from media_search.domain.categories import ReferenceCategory
from media_search.ports.categories import CategoryRepositoryPort
from media_search.ports.import_lock import ImportLockBusy, ImportLockPort


class CategoryService:
    def __init__(self, *, repository: CategoryRepositoryPort, lock: ImportLockPort,
                 enabled: bool, max_per_import: int = 50,
                 reload_db: Callable[[], None] | None = None,
                 persist_db: Callable[[], None] | None = None):
        self._repository = repository
        self._lock = lock
        self._reload = reload_db
        self._persist = persist_db
        self.enabled = enabled
        self.max_per_import = max_per_import

    def list_all(self):
        return self._repository.list_all()

    def reference(self, category_id: str, index: int) -> bytes:
        for category in self.list_all():
            if category.category_id == category_id and 0 <= index < len(category.references):
                return category.references[index]
        raise FileNotFoundError('見本画像が見つかりません')

    @contextmanager
    def _mutation(self):
        holder = 'category-' + uuid.uuid4().hex
        if not self._lock.try_acquire(holder):
            raise ImportLockBusy('another mutation')
        try:
            if self._reload:
                self._reload()
            yield
            if self._persist:
                self._persist()
        finally:
            self._lock.release(holder)

    def create(self, *, name: str, criteria: str, references: tuple[bytes, ...]):
        category = ReferenceCategory(uuid.uuid4().hex, name.strip(), criteria.strip(), references)
        with self._mutation():
            self._repository.create(category)
        return category

    def delete(self, category_id: str):
        with self._mutation():
            self._repository.delete(category_id)
