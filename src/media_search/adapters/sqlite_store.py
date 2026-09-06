from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import sqlite_vec

from media_search.domain.media_asset import MediaAsset, MediaType


class SqliteMetadataRepository:
    def __init__(self, conn: sqlite3.Connection, *, lock: threading.Lock | None = None) -> None:
        self._conn = conn
        self._lock = lock or threading.Lock()
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS assets (
                  asset_id TEXT PRIMARY KEY,
                  media_type TEXT NOT NULL,
                  mime_type TEXT NOT NULL,
                  size_bytes INTEGER NOT NULL,
                  width INTEGER,
                  height INTEGER,
                  duration_seconds REAL,
                  tags_json TEXT NOT NULL,
                  description TEXT NOT NULL,
                  display_name TEXT NOT NULL DEFAULT '',
                  folder_id TEXT,
                  product_id TEXT
                )
                """
            )
            cols = {
                r[1]
                for r in self._conn.execute("PRAGMA table_info(assets)").fetchall()
            }
            if "display_name" not in cols:
                self._conn.execute(
                    "ALTER TABLE assets ADD COLUMN display_name TEXT NOT NULL DEFAULT ''"
                )
            if "folder_id" not in cols:
                self._conn.execute("ALTER TABLE assets ADD COLUMN folder_id TEXT")
            if "product_id" not in cols:
                self._conn.execute("ALTER TABLE assets ADD COLUMN product_id TEXT")
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS folders (
                  folder_id TEXT PRIMARY KEY,
                  name TEXT NOT NULL,
                  parent_id TEXT
                )
                """
            )
            self._conn.commit()

    def upsert(self, asset: MediaAsset) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO assets(
                  asset_id, media_type, mime_type, size_bytes, width, height,
                  duration_seconds, tags_json, description, display_name, folder_id,
                  product_id
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(asset_id) DO UPDATE SET
                  media_type=excluded.media_type,
                  mime_type=excluded.mime_type,
                  size_bytes=excluded.size_bytes,
                  width=excluded.width,
                  height=excluded.height,
                  duration_seconds=excluded.duration_seconds,
                  tags_json=excluded.tags_json,
                  description=excluded.description,
                  display_name=excluded.display_name,
                  folder_id=excluded.folder_id,
                  product_id=excluded.product_id
                """,
                (
                    asset.asset_id,
                    asset.media_type.value,
                    asset.mime_type,
                    asset.size_bytes,
                    asset.width,
                    asset.height,
                    asset.duration_seconds,
                    json.dumps(asset.tags),
                    asset.description,
                    asset.display_name or asset.asset_id,
                    asset.folder_id,
                    asset.product_id,
                ),
            )
            self._conn.commit()

    def get(self, asset_id: str) -> Optional[MediaAsset]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM assets WHERE asset_id = ?", (asset_id,)
            ).fetchone()
        if row is None:
            return None
        return _row_to_asset(row)

    def list_all(self) -> list[MediaAsset]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM assets ORDER BY asset_id"
            ).fetchall()
        return [_row_to_asset(r) for r in rows]

    def list_by_folder(self, folder_id: Optional[str]) -> list[MediaAsset]:
        with self._lock:
            if folder_id is None:
                rows = self._conn.execute(
                    "SELECT * FROM assets WHERE folder_id IS NULL ORDER BY display_name, asset_id"
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM assets WHERE folder_id = ? ORDER BY display_name, asset_id",
                    (folder_id,),
                ).fetchall()
        return [_row_to_asset(r) for r in rows]

    def search_text(self, needle: str) -> list[MediaAsset]:
        n = needle.strip().lower()
        if not n:
            return []
        # Escape LIKE metacharacters; match display_name or tags_json substring.
        like = "%" + n.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM assets
                WHERE lower(display_name) LIKE ? ESCAPE '\\'
                   OR lower(tags_json) LIKE ? ESCAPE '\\'
                ORDER BY asset_id
                """,
                (like, like),
            ).fetchall()
        return [_row_to_asset(r) for r in rows]

    def count_by_product_id(self, product_id: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS c FROM assets WHERE product_id = ?",
                (product_id,),
            ).fetchone()
        return int(row["c"] if row is not None else 0)

    def delete(self, asset_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM assets WHERE asset_id = ?", (asset_id,))
            self._conn.commit()


class SqliteFolderRepository:
    def __init__(self, conn: sqlite3.Connection, *, lock: threading.Lock | None = None) -> None:
        self._conn = conn
        self._lock = lock or threading.Lock()
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS folders (
                  folder_id TEXT PRIMARY KEY,
                  name TEXT NOT NULL,
                  parent_id TEXT
                )
                """
            )
            self._conn.commit()

    def upsert(self, folder) -> None:
        from media_search.ports.folder import Folder

        assert isinstance(folder, Folder)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO folders(folder_id, name, parent_id) VALUES (?,?,?)
                ON CONFLICT(folder_id) DO UPDATE SET
                  name=excluded.name,
                  parent_id=excluded.parent_id
                """,
                (folder.folder_id, folder.name, folder.parent_id),
            )
            self._conn.commit()

    def get(self, folder_id: str):
        from media_search.ports.folder import Folder

        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM folders WHERE folder_id = ?", (folder_id,)
            ).fetchone()
        if row is None:
            return None
        return Folder(
            folder_id=row["folder_id"], name=row["name"], parent_id=row["parent_id"]
        )

    def list_children(self, parent_id: Optional[str] = None):
        from media_search.ports.folder import Folder

        with self._lock:
            if parent_id is None:
                rows = self._conn.execute(
                    "SELECT * FROM folders WHERE parent_id IS NULL ORDER BY name"
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM folders WHERE parent_id = ? ORDER BY name",
                    (parent_id,),
                ).fetchall()
        return [
            Folder(folder_id=r["folder_id"], name=r["name"], parent_id=r["parent_id"])
            for r in rows
        ]

    def list_all(self):
        from media_search.ports.folder import Folder

        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM folders ORDER BY name"
            ).fetchall()
        return [
            Folder(folder_id=r["folder_id"], name=r["name"], parent_id=r["parent_id"])
            for r in rows
        ]

    def delete(self, folder_id: str) -> None:
        with self._lock:
            child = self._conn.execute(
                "SELECT 1 FROM folders WHERE parent_id = ? LIMIT 1", (folder_id,)
            ).fetchone()
            if child:
                raise ValueError("folder not empty (has child folders)")
            asset = self._conn.execute(
                "SELECT 1 FROM assets WHERE folder_id = ? LIMIT 1", (folder_id,)
            ).fetchone()
            if asset:
                raise ValueError("folder not empty (has assets)")
            self._conn.execute("DELETE FROM folders WHERE folder_id = ?", (folder_id,))
            self._conn.commit()


class SqliteProductRepository:
    def __init__(self, conn: sqlite3.Connection, *, lock: threading.Lock | None = None) -> None:
        self._conn = conn
        self._lock = lock or threading.Lock()
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                  product_id TEXT PRIMARY KEY,
                  name TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def upsert(self, product) -> None:
        from media_search.domain.product import Product

        assert isinstance(product, Product)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO products(product_id, name) VALUES (?,?)
                ON CONFLICT(product_id) DO UPDATE SET name=excluded.name
                """,
                (product.product_id, product.name),
            )
            self._conn.commit()

    def get(self, product_id: str):
        from media_search.domain.product import Product

        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM products WHERE product_id = ?", (product_id,)
            ).fetchone()
        if row is None:
            return None
        return Product(product_id=row["product_id"], name=row["name"])

    def list_all(self):
        from media_search.domain.product import Product

        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM products ORDER BY name, product_id"
            ).fetchall()
        return [Product(product_id=r["product_id"], name=r["name"]) for r in rows]

    def delete(self, product_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
            self._conn.commit()


def _row_to_asset(row: sqlite3.Row) -> MediaAsset:
    keys = row.keys()
    display = row["display_name"] if "display_name" in keys else ""
    folder_id = row["folder_id"] if "folder_id" in keys else None
    product_id = row["product_id"] if "product_id" in keys else None
    return MediaAsset(
        asset_id=row["asset_id"],
        media_type=MediaType(row["media_type"]),
        mime_type=row["mime_type"],
        size_bytes=int(row["size_bytes"]),
        width=row["width"],
        height=row["height"],
        duration_seconds=row["duration_seconds"],
        tags=list(json.loads(row["tags_json"] or "[]")),
        description=row["description"] or "",
        display_name=display or row["asset_id"],
        folder_id=folder_id,
        product_id=product_id,
    )


class SqliteVecSearch:
    def __init__(
        self,
        conn: sqlite3.Connection,
        *,
        dimension: int,
        lock: threading.Lock | None = None,
    ) -> None:
        self._conn = conn
        self._dimension = dimension
        self._lock = lock or threading.Lock()
        with self._lock:
            self._conn.enable_load_extension(True)
            sqlite_vec.load(self._conn)
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS frames (
                  frame_key TEXT PRIMARY KEY,
                  asset_id TEXT NOT NULL,
                  position REAL NOT NULL
                )
                """
            )
            exists = self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='frame_vec'"
            ).fetchone()
            if exists is None:
                self._conn.execute(
                    f"""
                    CREATE VIRTUAL TABLE frame_vec USING vec0(
                      frame_key TEXT PRIMARY KEY,
                      embedding float[{dimension}] distance_metric=cosine
                    )
                    """
                )
            self._conn.commit()

    def upsert_frame(
        self,
        *,
        asset_id: str,
        frame_key: str,
        position: float,
        vector: Sequence[float],
    ) -> None:
        if len(vector) != self._dimension:
            raise ValueError(
                f"vector dim {len(vector)} != expected {self._dimension}"
            )
        vec = np.asarray(vector, dtype=np.float32)
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        embedding = "[" + ",".join(f"{float(x):.8f}" for x in vec.tolist()) + "]"
        with self._lock:
            self._conn.execute(
                "DELETE FROM frame_vec WHERE frame_key = ?", (frame_key,)
            )
            self._conn.execute(
                "INSERT INTO frame_vec(frame_key, embedding) VALUES (?, ?)",
                (frame_key, embedding),
            )
            self._conn.execute(
                """
                INSERT INTO frames(frame_key, asset_id, position) VALUES (?,?,?)
                ON CONFLICT(frame_key) DO UPDATE SET
                  asset_id=excluded.asset_id,
                  position=excluded.position
                """,
                (frame_key, asset_id, position),
            )
            self._conn.commit()

    def delete_asset_frames(self, asset_id: str) -> None:
        with self._lock:
            keys = [
                r[0]
                for r in self._conn.execute(
                    "SELECT frame_key FROM frames WHERE asset_id = ?", (asset_id,)
                ).fetchall()
            ]
            for key in keys:
                self._conn.execute(
                    "DELETE FROM frame_vec WHERE frame_key = ?", (key,)
                )
                self._conn.execute("DELETE FROM frames WHERE frame_key = ?", (key,))
            self._conn.commit()

    def search(
        self,
        *,
        query_vector: Sequence[float],
        top_k: int,
    ) -> list[tuple[str, str, float, float]]:
        vec = np.asarray(query_vector, dtype=np.float32)
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        embedding = "[" + ",".join(f"{float(x):.8f}" for x in vec.tolist()) + "]"
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT frame_vec.frame_key, frames.asset_id, frame_vec.distance, frames.position
                FROM frame_vec
                JOIN frames ON frames.frame_key = frame_vec.frame_key
                WHERE frame_vec.embedding MATCH ?
                  AND k = ?
                ORDER BY frame_vec.distance
                """,
                (embedding, int(top_k)),
            ).fetchall()
        out: list[tuple[str, str, float, float]] = []
        for frame_key, asset_id, distance, position in rows:
            # sqlite-vec cosine distance ≈ 1 - cosine_similarity
            score = max(0.0, 1.0 - float(distance))
            out.append((str(asset_id), str(frame_key), score, float(position)))
        return out


def open_db(path: str | Path) -> sqlite3.Connection:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # FastAPI runs sync routes in a worker thread; allow cross-thread use + lock.
    conn = sqlite3.connect(str(p), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
