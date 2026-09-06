from __future__ import annotations

from media_search.adapters.sqlite_store import (
    SqliteFolderRepository,
    SqliteMetadataRepository,
    SqliteProductRepository,
    SqliteVecSearch,
    open_db,
)
from media_search.domain.media_asset import MediaAsset, MediaType


def test_replace_connection_preserves_reads(tmp_path):
    path_a = tmp_path / "a.db"
    path_b = tmp_path / "b.db"
    conn_a = open_db(path_a)
    meta = SqliteMetadataRepository(conn_a)
    folders = SqliteFolderRepository(conn_a)
    products = SqliteProductRepository(conn_a)
    vectors = SqliteVecSearch(conn_a, dimension=8)

    meta.upsert(
        MediaAsset(
            asset_id="x.png",
            media_type=MediaType.IMAGE,
            mime_type="image/png",
            size_bytes=1,
            display_name="x.png",
        )
    )
    vectors.upsert_frame(
        asset_id="x.png",
        frame_key="x.png::0",
        position=0.0,
        vector=[0.1] * 8,
    )
    conn_a.commit()

    # Simulate Job writing a newer DB elsewhere, then service reloads.
    conn_b = open_db(path_b)
    meta_b = SqliteMetadataRepository(conn_b)
    vec_b = SqliteVecSearch(conn_b, dimension=8)
    meta_b.upsert(
        MediaAsset(
            asset_id="y.png",
            media_type=MediaType.IMAGE,
            mime_type="image/png",
            size_bytes=2,
            display_name="y.png",
        )
    )
    vec_b.upsert_frame(
        asset_id="y.png",
        frame_key="y.png::0",
        position=0.0,
        vector=[0.2] * 8,
    )
    conn_b.commit()
    conn_b.close()

    # Copy b over a path and reopen
    path_a.write_bytes(path_b.read_bytes())
    new_conn = open_db(path_a)
    meta.replace_connection(new_conn)
    folders.replace_connection(new_conn)
    products.replace_connection(new_conn)
    vectors.replace_connection(new_conn)

    assert meta.get("y.png") is not None
    assert meta.get("x.png") is None
    assert vectors.has_frames("y.png")
    assert not vectors.has_frames("x.png")
