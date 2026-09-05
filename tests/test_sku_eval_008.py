import numpy as np

from media_search.eval.sku_corpus import load_corpus_items, write_synthetic_sku_corpus
from media_search.eval.sku_retrieval import (
    recall_at_k_same_product,
    score_same_product_retrieval,
)


def test_recall_at_1_perfect_same_product():
    # Two SKUs, 2 views each; identical vectors within SKU
    vectors = np.array(
        [
            [1.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [0.0, 1.0],
        ]
    )
    pids = ["A", "A", "B", "B"]
    assert recall_at_k_same_product(vectors=vectors, product_ids=pids, k=1) == 1.0


def test_recall_at_1_zero_when_confused():
    vectors = np.array(
        [
            [1.0, 0.0],
            [0.0, 1.0],  # same product A but orthogonal → wrong neighbor is B
            [0.0, 1.0],
            [1.0, 0.0],
        ]
    )
    pids = ["A", "A", "B", "B"]
    # Query 0 → top1 is index 3 (B); miss. Query 1 → top1 is index 2 (B); miss.
    assert recall_at_k_same_product(vectors=vectors, product_ids=pids, k=1) == 0.0


def test_synthetic_corpus_has_multi_view_skus(tmp_path):
    write_synthetic_sku_corpus(tmp_path, skus=2, views=3)
    items = load_corpus_items(tmp_path)
    assert len(items) >= 2 * 3
    from collections import Counter

    counts = Counter(pid for _, pid, _ in items if pid.startswith("SKU-"))
    assert all(v >= 2 for v in counts.values())


def test_score_bundle():
    vectors = np.eye(4)
    pids = ["A", "A", "B", "B"]
    # Orthogonal within SKU → R@1 poor; still valid bundle
    s = score_same_product_retrieval(vectors=vectors, product_ids=pids)
    assert s.n_queries == 4
    assert 0.0 <= s.recall_at_1 <= 1.0
    assert 0.0 <= s.recall_at_5 <= 1.0
