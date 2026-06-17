"""bge-m3 embedding 封装（exam-memory V2 核心层）。

设计对齐 OneFind v1.7：
  - pooling: CLS token（非 mean），确保向量空间兼容
  - normalize: L2，使 dot product = cosine similarity
  - 维度: 1024，与 OneFind zotero/obsidian/folder source 一致

无 LangChain 依赖，CPU-only，静默降级。

用法:
    from exam_memory.embedding import get_embedder, encode, is_available
    if is_available():
        vec = encode("双指针三数之和")          # (1024,) float32
        vecs = encode(["背包问题", "动态规划"])   # (2, 1024) float32
"""

from __future__ import annotations

import logging
import os
from typing import Union

import numpy as np

logger = logging.getLogger(__name__)

# ── 依赖检测 ────────────────────────────────────────────────

class EmbeddingError(Exception):
    pass


def _check_dependency() -> None:
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        raise EmbeddingError(
            "sentence-transformers 未安装。"
            "请运行: pip install '.[embed]'"
        )


# ── 模型单例 ────────────────────────────────────────────────

_MODEL = None


def get_embedder(model_name: str = "BAAI/bge-m3"):
    """延迟加载 bge-m3 模型（单例）。CPU-only。

    对齐 OneFind: CLS pooling + L2 normalize。
    验证 model[1].pooling_mode_cls_token == True。
    """
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    _check_dependency()
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

    from sentence_transformers import SentenceTransformer
    _MODEL = SentenceTransformer(model_name, device="cpu")

    _verify_pooling(_MODEL)
    return _MODEL


def _verify_pooling(model) -> None:
    """验证模型使用 CLS pooling（对齐 OneFind）。"""
    try:
        pooling = model[1]
        if hasattr(pooling, "pooling_mode_cls_token"):
            is_cls = pooling.pooling_mode_cls_token
        elif hasattr(pooling, "pooling_mode_mean_tokens"):
            is_cls = not pooling.pooling_mode_mean_tokens
        else:
            is_cls = True  # 无法检测时假设正确，OneFind 已知配置

        if not is_cls:
            logger.warning(
                "[embedding] 模型 pooling 非 CLS 模式，向量空间可能与 OneFind 不兼容。"
                "当前 pooling_mode_cls_token=False，建议检查模型配置。"
            )
        else:
            logger.info("[embedding] CLS pooling 已确认，向量空间与 OneFind 兼容。")
    except Exception as e:
        logger.debug(f"[embedding] pooling 验证跳过（结构不匹配）: {e}")


def is_available() -> bool:
    """embedding 层是否可用。"""
    try:
        _check_dependency()
        return True
    except EmbeddingError:
        return False


# ── 编码接口 ────────────────────────────────────────────────

def encode(
    text: Union[str, list[str]],
    *,
    normalize: bool = True,
) -> np.ndarray:
    """将文本编码为 embedding 向量。

    对齐 OneFind:
      - CLS token pooling（模型层已配置）
      - L2 归一化（使 dot product = cosine similarity）
      - 输出 float32，shape (dim,) 或 (n, dim)，dim=1024

    Args:
        text: 单条文本或文本列表。
        normalize: L2 归一化（使 dot product = cosine similarity）。

    Returns:
        float32 numpy 数组，shape (dim,) 或 (n, dim)。
    """
    model = get_embedder()
    emb = model.encode(
        text,
        normalize_embeddings=normalize,
        show_progress_bar=False,
    )
    return np.asarray(emb, dtype=np.float32)


def encode_safe(
    text: Union[str, list[str]],
    *,
    normalize: bool = True,
) -> np.ndarray | None:
    """编码的安静版本——依赖不可用时返回 None。"""
    try:
        return encode(text, normalize=normalize)
    except Exception:
        return None
