from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


def write_synthetic_sku_corpus(root: Path, *, skus: int = 4, views: int = 3) -> list[dict]:
    """Create multi-view SKUs (color / crop / brightness) with sidecar product_id."""
    root.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    palette = [
        (220, 40, 40),
        (40, 120, 220),
        (40, 180, 90),
        (240, 180, 40),
        (140, 60, 200),
        (30, 30, 30),
    ]
    for s in range(skus):
        pid = f"SKU-{s + 1:03d}"
        base_color = palette[s % len(palette)]
        base = Image.new("RGB", (128, 128), base_color)
        # Distinct center mark so crops still share identity cues
        for x in range(48, 80):
            for y in range(48, 80):
                base.putpixel((x, y), (255, 255, 255))
        for v in range(views):
            img = base.copy()
            if v == 1:
                img = ImageOps.crop(img, border=12).resize((128, 128))
            elif v == 2:
                img = ImageEnhance.Brightness(img).enhance(0.75)
            elif v >= 3:
                img = ImageEnhance.Color(img).enhance(1.2)
            name = f"{pid.lower()}-v{v}.png"
            path = root / name
            img.save(path)
            meta = {
                "tags": [pid.lower(), "synthetic"],
                "description": f"synthetic view {v}",
                "product_id": pid,
            }
            (root / f"{name}.meta.json").write_text(
                json.dumps(meta, indent=2) + "\n", encoding="utf-8"
            )
            manifest.append(
                {"path": name, "product_id": pid, "bytes_path": str(path)}
            )
    # Hard negatives: unique one-offs
    for i in range(4):
        color = (10 * i, 20 * i, 30 * i)
        name = f"neg-{i}.png"
        path = root / name
        Image.new("RGB", (128, 128), color).save(path)
        pid = f"NEG-{i + 1:03d}"
        meta = {"tags": ["negative"], "description": "", "product_id": pid}
        (root / f"{name}.meta.json").write_text(
            json.dumps(meta, indent=2) + "\n", encoding="utf-8"
        )
        manifest.append({"path": name, "product_id": pid, "bytes_path": str(path)})
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def load_corpus_items(root: Path) -> list[tuple[str, str, bytes]]:
    """Return (asset_id, product_id, image_bytes) from corpus dir + sidecars."""
    items: list[tuple[str, str, bytes]] = []
    for path in sorted(root.iterdir()):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        if path.name.endswith(".meta.json"):
            continue
        meta_path = path.parent / f"{path.name}.meta.json"
        product_id = ""
        if meta_path.is_file():
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            product_id = str(data.get("product_id") or "").strip()
        items.append((path.name, product_id, path.read_bytes()))
    return items
