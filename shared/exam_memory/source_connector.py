"""source_connector.py — 统一输入适配层。

将不同来源的输入（raw text / file path / chunks）适配为三类提取管道的调用。

用法:
    from exam_memory.source_connector import SourceConnector
    from exam_memory.question_bank import QuestionBank

    bank = QuestionBank()
    connector = SourceConnector(bank)

    # 从文本
    result = connector.connect("哈希表是 O(1) 查找...", topic="哈希表")

    # 从文件
    result = connector.connect("/path/to/notes.md", topic="排序")

    # 从 chunks（RAG 检索结果）
    result = connector.connect([{"text": "chunk1"}, {"text": "chunk2"}], topic="BFS")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from exam_memory.question_bank import QuestionBank
from exam_memory.source_registry import SourceRegistry

logger = logging.getLogger(__name__)


class SourceConnector:
    """统一输入适配：自动识别输入类型，路由到对应的提取管道。"""

    def __init__(self, bank: QuestionBank, registry: SourceRegistry | None = None):
        self._bank = bank
        self._registry = registry

    def connect(
        self,
        source: str | list[dict],
        topic: str,
        count: int = 3,
        q_type: str = "算法",
        difficulty: str = "中等",
    ) -> dict[str, Any]:
        """统一入口：自动识别 source 类型并路由到对应提取管道。

        source 类型判断：
        - list[dict] → chunks → rag_extract
        - 存在的文件路径 → 读取内容 → text_extract
        - 其他 str → raw text → text_extract

        Returns: 与 rag_extract/text_extract 相同的 result dict。
        """
        if isinstance(source, list):
            return self._from_chunks(source, topic, count, q_type, difficulty)

        if isinstance(source, str):
            path = Path(source)
            # 启发式：含路径分隔符或文件扩展名 → 当作文件路径
            if self._looks_like_path(source):
                return self._from_file(path, topic, count, q_type, difficulty)
            return self._from_text(source, topic, count, q_type, difficulty)

        return self._make_error(f"不支持的 source 类型：{type(source).__name__}")

    def from_text(
        self,
        text: str,
        topic: str,
        count: int = 3,
        q_type: str = "算法",
        difficulty: str = "中等",
    ) -> dict[str, Any]:
        """显式文本模式入口。"""
        return self._from_text(text, topic, count, q_type, difficulty)

    def from_file(
        self,
        path: str | Path,
        topic: str,
        count: int = 3,
        q_type: str = "算法",
        difficulty: str = "中等",
    ) -> dict[str, Any]:
        """显式文件模式入口。"""
        return self._from_file(Path(path), topic, count, q_type, difficulty)

    def from_chunks(
        self,
        chunks: list[dict],
        topic: str,
        count: int = 3,
        q_type: str = "算法",
        difficulty: str = "中等",
    ) -> dict[str, Any]:
        """显式 chunks（RAG）模式入口。"""
        return self._from_chunks(chunks, topic, count, q_type, difficulty)

    def from_source(
        self,
        source_name: str,
        topic: str,
        count: int = 3,
        q_type: str = "算法",
        difficulty: str = "中等",
    ) -> dict[str, Any]:
        """从已挂载知识源检索并出题。"""
        if self._registry is None:
            return self._make_error("registry 未配置，无法使用 from_source")

        source = self._registry.get(source_name)
        if source is None:
            return self._make_error(f"知识源不存在：{source_name}")

        chunks = source.fetch(topic)
        if not chunks:
            return self._make_error(f"知识源 '{source_name}' 未找到与 '{topic}' 相关的内容")

        combined = "\n\n".join(c.get("text", "") for c in chunks if c.get("text"))
        if not combined.strip():
            return self._make_error(f"知识源 '{source_name}' 返回内容为空")
        return self._call_text_extract(combined, topic, count, q_type, difficulty)

    # ── 内部路由 ──────────────────────────────────────────────

    def _from_text(self, text: str, topic: str, count: int, q_type: str, difficulty: str) -> dict:
        if not text.strip():
            return self._make_error("source 文本为空")
        return self._call_text_extract(text, topic, count, q_type, difficulty)

    def _from_file(self, path: Path, topic: str, count: int, q_type: str, difficulty: str) -> dict:
        if not path.exists():
            return self._make_error(f"文件不存在：{path}")
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            return self._make_error(f"文件读取失败：{e}")
        if not text.strip():
            return self._make_error(f"文件内容为空：{path}")
        return self._call_text_extract(text, topic, count, q_type, difficulty)

    def _from_chunks(self, chunks: list[dict], topic: str, count: int, q_type: str, difficulty: str) -> dict:
        if not chunks:
            return self._make_error("chunks 列表为空")
        # 将 chunks 拼接为文本，走 text_extract
        combined = "\n\n".join(c.get("text", "") for c in chunks if c.get("text"))
        if not combined.strip():
            return self._make_error("chunks 中无有效文本")
        return self._call_text_extract(combined, topic, count, q_type, difficulty)

    def _call_text_extract(self, text: str, topic: str, count: int, q_type: str, difficulty: str) -> dict:
        """Call QuestionBank pipeline and convert expected validation errors."""
        try:
            return self._bank.text_extract(text, topic, count, q_type, difficulty)
        except ValueError as e:
            return self._make_error(str(e))

    @staticmethod
    def _looks_like_path(s: str) -> bool:
        """启发式判断字符串是否像文件路径。

        保守策略：仅当含路径分隔符且扩展名已知，
        或路径实际存在时才判定为路径，避免中文含 / 时误判。
        """
        if not s:
            return False
        p = Path(s)
        _KNOWN_EXTS = {".md", ".txt", ".py", ".json", ".yaml", ".yml", ".csv", ".html"}
        has_sep = "/" in s or "\\" in s
        if p.suffix.lower() in _KNOWN_EXTS and has_sep:
            return True
        if p.exists():
            return True
        return False

    @staticmethod
    def _make_error(msg: str) -> dict[str, Any]:
        return {
            "saved": [],
            "validated": [],
            "rejected": [],
            "raw_llm_output": None,
            "error": msg,
        }
