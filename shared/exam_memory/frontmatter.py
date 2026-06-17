"""frontmatter.py — 共享 YAML frontmatter 解析工具。

从 question_bank.py / server.py / vector_store.py 提取的重复逻辑。
"""

from __future__ import annotations

from typing import Any

import yaml


def parse_frontmatter(text: str) -> dict[str, Any]:
    """解析 Markdown YAML frontmatter（--- 之间的 YAML）。

    自动将 date 对象转为 str 以保证 JSON 序列化兼容。
    """
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        meta = yaml.safe_load(parts[1]) or {}
        for k, v in meta.items():
            if hasattr(v, "isoformat"):
                meta[k] = v.isoformat()
        return meta
    except yaml.YAMLError:
        return {}


def body_text(text: str) -> str:
    """提取 frontmatter 之后的正文。"""
    if text.startswith("---"):
        parts = text.split("---", 2)
        return parts[2].strip() if len(parts) >= 3 else text
    return text.strip()
