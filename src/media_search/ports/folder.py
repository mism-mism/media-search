from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class Folder:
    folder_id: str
    name: str
    parent_id: Optional[str] = None


class FolderRepositoryPort(Protocol):
    def upsert(self, folder: Folder) -> None: ...

    def get(self, folder_id: str) -> Optional[Folder]: ...

    def list_children(self, parent_id: Optional[str] = None) -> list[Folder]: ...

    def list_all(self) -> list[Folder]: ...

    def delete(self, folder_id: str) -> None: ...
