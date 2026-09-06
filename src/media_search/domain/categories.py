from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Sequence

MAX_CATEGORIES = 5
MAX_REFERENCES = 3
MAX_REFERENCE_BYTES = 256 * 1024


@dataclass(frozen=True)
class ReferenceCategory:
    category_id: str
    name: str
    criteria: str
    references: tuple[bytes, ...]

    def __post_init__(self):
        if not self.category_id or not self.name.strip() or len(self.name) > 40:
            raise ValueError('カテゴリ名は1〜40文字で入力してください')
        if not self.criteria.strip() or len(self.criteria) > 300:
            raise ValueError('判定基準は1〜300文字で入力してください')
        if not 1 <= len(self.references) <= MAX_REFERENCES:
            raise ValueError('見本画像は1〜3枚を選択してください')
        if any(not r or len(r) > MAX_REFERENCE_BYTES for r in self.references):
            raise ValueError('見本画像のサイズが上限を超えています')


@dataclass(frozen=True)
class CategoryDecision:
    category_id: str
    name: str
    outcome: str
    reason: str

    def __post_init__(self):
        if not self.category_id or not self.name or len(self.name) > 40:
            raise ValueError('invalid category identity')
        if self.outcome not in {'match', 'no_match', 'uncertain'}:
            raise ValueError('invalid category outcome')
        if not isinstance(self.reason, str) or not self.reason.strip() or len(self.reason) > 200:
            raise ValueError('invalid category reason')


@dataclass(frozen=True)
class CategoryReport:
    catalog_version: str
    decisions: tuple[CategoryDecision, ...]
    model_id: str
    prompt_version: str
    image_sha256: str = ""

    def __post_init__(self):
        if not self.catalog_version or not self.model_id or not self.prompt_version:
            raise ValueError('classification provenance required')
        if not 1 <= len(self.decisions) <= MAX_CATEGORIES:
            raise ValueError('invalid classification count')
        if len({d.category_id for d in self.decisions}) != len(self.decisions):
            raise ValueError('duplicate classification')

    @property
    def tags(self) -> tuple[str, ...]:
        return tuple(d.name for d in self.decisions if d.outcome == 'match')


def catalog_version(categories: Sequence[ReferenceCategory]) -> str:
    records = [(c.category_id, c.name, c.criteria,
                [hashlib.sha256(r).hexdigest() for r in c.references])
               for c in sorted(categories, key=lambda c: c.category_id)]
    return hashlib.sha256(json.dumps(records, ensure_ascii=False).encode()).hexdigest()
