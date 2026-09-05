from __future__ import annotations

from pathlib import Path

from PIL import Image

from media_search.adapters.local_media_storage import LocalMediaStorage


def test_local_media_storage_lists_and_reads(tmp_path: Path):
    root = tmp_path / "incoming"
    root.mkdir()
    Image.new("RGB", (8, 8), (1, 2, 3)).save(root / "a.png")
    (root / "notes.txt").write_text("skip")
    store = LocalMediaStorage(root)
    assert store.list_media_keys() == ["a.png", "notes.txt"]
    assert store.exists("a.png")
    assert store.read_bytes("a.png")[:8]
    with store.materialize("a.png", tmp_path / "stage") as path:
        assert path.is_file()
