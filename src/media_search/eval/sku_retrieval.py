"""Same-SKU image retrieval metrics for Feature 008 eval (no I/O)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RetrievalScores:
    recall_at_1: float
    recall_at_5: float
    n_queries: int


def _normalize_rows(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    return mat / norms


def recall_at_k_same_product(
    *,
    vectors: np.ndarray,
    product_ids: list[str],
    k: int,
) -> float:
    """Leave-one-out: query each row; hit if any of top-k others share product_id."""
    if vectors.ndim != 2:
        raise ValueError("vectors must be 2D")
    n = vectors.shape[0]
    if n != len(product_ids):
        raise ValueError("vectors/product_ids length mismatch")
    if n < 2:
        return 0.0
    kk = max(1, min(k, n - 1))
    mat = _normalize_rows(np.asarray(vectors, dtype=float))
    sims = mat @ mat.T
    hits = 0
    queries = 0
    for i in range(n):
        pid = product_ids[i]
        if not pid:
            continue
        # Need at least one other gallery item with same product_id
        if sum(1 for j, p in enumerate(product_ids) if j != i and p == pid) == 0:
            continue
        queries += 1
        row = sims[i].copy()
        row[i] = -np.inf
        top = np.argpartition(-row, kk - 1)[:kk]
        top = top[np.argsort(-row[top])]
        if any(product_ids[int(j)] == pid for j in top):
            hits += 1
    if queries == 0:
        return 0.0
    return hits / queries


def score_same_product_retrieval(
    *,
    vectors: np.ndarray,
    product_ids: list[str],
) -> RetrievalScores:
    n = len(product_ids)
    return RetrievalScores(
        recall_at_1=recall_at_k_same_product(
            vectors=vectors, product_ids=product_ids, k=1
        ),
        recall_at_5=recall_at_k_same_product(
            vectors=vectors, product_ids=product_ids, k=5
        ),
        n_queries=sum(
            1
            for i, pid in enumerate(product_ids)
            if pid
            and any(j != i and product_ids[j] == pid for j in range(n))
        ),
    )
