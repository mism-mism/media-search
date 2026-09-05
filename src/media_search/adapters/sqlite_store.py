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
                  description TEXT NOT NULL
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
                  duration_seconds, tags_json, description
                ) VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(asset_id) DO UPDATE SET
                  media_type=excluded.media_type,
                  mime_type=excluded.mime_type,
                  size_bytes=excluded.size_bytes,
                  width=excluded.width,
                  height=excluded.height,
                  duration_seconds=excluded.duration_seconds,
                  tags_json=excluded.tags_json,
                  description=excluded.description
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


def _row_to_asset(row: sqlite3.Row) -> MediaAsset:
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
