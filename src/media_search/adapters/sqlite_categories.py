from __future__ import annotations

import base64
import json
import sqlite3
import threading

from media_search.domain.categories import MAX_CATEGORIES, ReferenceCategory


class SqliteCategoryRepository:
    def __init__(self, conn: sqlite3.Connection, *, lock=None):
        self._lock = lock or threading.RLock()
        self.replace_connection(conn)

    def replace_connection(self, conn):
        with self._lock:
            conn.execute('''CREATE TABLE IF NOT EXISTS reference_categories (
                category_id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE,
                criteria TEXT NOT NULL, references_json TEXT NOT NULL)''')
            conn.commit()
            self._conn = conn

    def list_all(self):
        with self._lock:
            rows = self._conn.execute('SELECT * FROM reference_categories ORDER BY category_id').fetchall()
        return [ReferenceCategory(r['category_id'], r['name'], r['criteria'],
                tuple(base64.b64decode(v) for v in json.loads(r['references_json']))) for r in rows]

    def create(self, category: ReferenceCategory):
        with self._lock, self._conn:
            count = self._conn.execute('SELECT COUNT(*) FROM reference_categories').fetchone()[0]
            if count >= MAX_CATEGORIES:
                raise ValueError('カテゴリは最大5件です')
            try:
                self._conn.execute('INSERT INTO reference_categories VALUES (?,?,?,?)', (
                    category.category_id, category.name, category.criteria,
                    json.dumps([base64.b64encode(r).decode('ascii') for r in category.references]),
                ))
            except sqlite3.IntegrityError:
                raise ValueError('同じ名前のカテゴリが登録されています') from None
            self._invalidate()

    def delete(self, category_id):
        with self._lock, self._conn:
            cur = self._conn.execute('DELETE FROM reference_categories WHERE category_id=?', (category_id,))
            if not cur.rowcount:
                raise FileNotFoundError('カテゴリが見つかりません')
            self._invalidate()

    def _invalidate(self):
        self._conn.execute("UPDATE assets SET category_report_json=NULL, category_error=''")
