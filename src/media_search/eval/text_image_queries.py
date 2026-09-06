"""Fixed JA/EN queries for 004/011-style text→image eval."""

from __future__ import annotations

# (query_id, query_text, filename_hint_prefix)
QUERIES: list[tuple[str, str, str]] = [
    ("en01", "a cat", "01-cat"),
    ("en02", "a dog", "02-dog"),
    ("en03", "sandy beach ocean", "03-beach"),
    ("en04", "red sports car", "17-car"),
    ("en05", "plate of food", "16-food"),
    ("en06", "mountain landscape", "04-mountain"),
    ("en07", "kitchen interior", "18-kitchen"),
    ("en08", "desert sand dunes", "12-desert"),
    ("en09", "bridge over water", "10-bridge"),
    ("en10", "colorful flower", "07-flower"),
    ("ja01", "猫", "01-cat"),
    ("ja02", "犬", "02-dog"),
    ("ja03", "砂浜", "03-beach"),
    ("ja04", "赤い車", "17-car"),
    ("ja05", "料理", "16-food"),
    ("ja06", "山の景色", "04-mountain"),
    ("ja07", "キッチン", "18-kitchen"),
    ("ja08", "砂漠", "12-desert"),
    ("ja09", "橋", "10-bridge"),
    ("ja10", "花", "07-flower"),
]


def hit_at_1(top_asset_id: str | None, hint: str) -> bool:
    if not top_asset_id:
        return False
    name = top_asset_id.split("/")[-1]
    return name.startswith(hint) or hint in name
