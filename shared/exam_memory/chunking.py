"""文本分块模块（exam-memory V2）。

对齐 OneFind v1.7:
  - Chunk 大小: 1600 char（对齐 folder source）
  - 按段落切分，保持语义完整
  - 保留 chunk_order 顺序

用法:
    from exam_memory.chunking import chunk_text, EXPERIENCE_CHUNK_CHARS
    chunks = chunk_text(long_text, max_chars=1600)
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ── 常量 ─────────────────────────────────────────────────────

# 对齐 OneFind folder source chunk 大小
EXPERIENCE_CHUNK_CHARS = 1600


# ── 分块函数 ─────────────────────────────────────────────────

def chunk_text(text: str, max_chars: int = EXPERIENCE_CHUNK_CHARS) -> list[str]:
    """将文本按段落切分为不超过 max_chars 的块。

    策略:
      1. 文本长度 <= max_chars → 不切分，返回 [text]
      2. 按双换行符（段落边界）切分
      3. 逐段累积，超限时落盘为独立块
      4. 最后一段残余单独成块

    Args:
        text: 原始文本。
        max_chars: 单块最大字符数。

    Returns:
        chunk 列表（可能仅含 1 个元素）。
    """
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        # 单个段落超长时强制切分
        if len(para) > max_chars:
            if current.strip():
                chunks.append(current.strip())
                current = ""
            for i in range(0, len(para), max_chars):
                chunks.append(para[i:i + max_chars])
            continue

        if len(current) + len(para) + 2 > max_chars and current:
            chunks.append(current.strip())
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def chunk_text_with_order(
    text: str,
    source_id: str,
    max_chars: int = EXPERIENCE_CHUNK_CHARS,
) -> list[dict[str, str]]:
    """分块并附加 chunk_id 和 chunk_order。

    Args:
        text: 原始文本。
        source_id: 源标识符（如文件名）。
        max_chars: 单块最大字符数。

    Returns:
        list[{"chunk_id", "source_id", "chunk_order", "text"}]
    """
    chunks = chunk_text(text, max_chars=max_chars)
    return [
        {
            "chunk_id": f"{source_id}:{i}",
            "source_id": source_id,
            "chunk_order": i,
            "text": c,
        }
        for i, c in enumerate(chunks)
    ]
