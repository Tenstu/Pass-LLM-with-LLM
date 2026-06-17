"""Weighted RRF 混合检索（exam-memory V2）。

对齐 OneFind v1.7:
  - dense_score_weight: 42（42% 语义 + 58% 词法），算法场景微调为 40:60
  - k: 60（RRF 分母常数）
  - 直接融合返回，无需 reranker

用法:
    from exam_memory.hybrid_search import hybrid_search, FUSION_WEIGHTS
    results = hybrid_search("双指针", fts_store, vector_store, limit=5)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── 融合权重 ─────────────────────────────────────────────────

FUSION_WEIGHTS: dict[str, dict[str, float]] = {
    "单选题": {"dense": 0.40, "sparse": 0.60},
    "多选题": {"dense": 0.40, "sparse": 0.60},
    "算法": {"dense": 0.35, "sparse": 0.65},
}

_DEFAULT_DENSE = 0.40
RRF_K = 60


# ── 融合 ─────────────────────────────────────────────────────

def hybrid_search(
    query: str,
    fts_store: Any,
    vector_store: Any,
    *,
    limit: int = 5,
    exp_type: str | None = None,
    dense_weight: float | None = None,
    k: int = RRF_K,
) -> list[dict[str, Any]]:
    """混合检索：FTS BM25 + 向量 cosine，Weighted RRF 融合。

    Args:
        query: 查询文本。
        fts_store: FTSStore 实例（词法检索）。
        vector_store: NumpyVectorStore 实例（语义检索）。
        limit: 最终返回条数。
        exp_type: 题型过滤（单选题/多选题/算法）。
        dense_weight: 语义权重 (0~1)。None 时按 exp_type 自动选择。
        k: RRF 分母常数。

    Returns:
        按融合分数降序排列的 dict 列表。
    """
    preset = FUSION_WEIGHTS.get(exp_type or "单选题", {"dense": _DEFAULT_DENSE, "sparse": 1 - _DEFAULT_DENSE})
    w = dense_weight if dense_weight is not None else preset["dense"]
    sparse_w = 1.0 - w

    fts_hits = _safe(fts_store.search, query, type_filter=exp_type, limit=20)
    vec_hits = _safe(vector_store.search, query, type_filter=exp_type, top_k=20)

    scores: dict[str, float] = {}
    fts_meta: dict[str, dict] = {}
    vec_meta: dict[str, dict] = {}

    for rank, hit in enumerate(fts_hits):
        key = hit.get("canonical_key", "")
        scores[key] = scores.get(key, 0.0) + sparse_w / (k + rank + 1)
        fts_meta[key] = hit

    for rank, hit in enumerate(vec_hits):
        key = hit.get("canonical_key", hit.get("metadata", {}).get("file_name", ""))
        scores[key] = scores.get(key, 0.0) + w / (k + rank + 1)
        vec_meta[key] = hit

    ranked = sorted(scores.items(), key=lambda x: -x[1])[:limit]

    results: list[dict[str, Any]] = []
    for key, score in ranked:
        fts_data = fts_meta.get(key, {})
        vec_data = vec_meta.get(key, {})

        text = vec_data.get("text") or fts_data.get("content") or ""
        metadata = vec_data.get("metadata") or {
            "title": fts_data.get("title", ""),
            "knowledge": fts_data.get("knowledge", ""),
        }

        results.append({
            "score": round(score, 4),
            "fts_score": fts_data.get("score"),
            "vec_score": vec_data.get("score"),
            "text": text,
            "metadata": metadata,
        })

    return results


def get_weights(exp_type: str) -> tuple[float, float]:
    """获取指定题型的 (dense_weight, sparse_weight)。"""
    preset = FUSION_WEIGHTS.get(exp_type, {"dense": _DEFAULT_DENSE, "sparse": 1 - _DEFAULT_DENSE})
    return preset["dense"], preset["sparse"]


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logger.debug(f"[hybrid_search] {fn.__name__} 异常: {e}")
        return []
