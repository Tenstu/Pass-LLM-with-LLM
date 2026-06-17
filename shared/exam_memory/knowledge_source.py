"""knowledge_source.py — KnowledgeSource Protocol + DirConnector 实现。

定义标准化外部知识源接口，DirConnector 作为首个连接器覆盖本地文档挂载场景。

用法:
    from exam_memory.knowledge_source import DirConnector

    ds = DirConnector(name="pdd-notes", path="targets/pdd-algo/cheatsheets/")
    ds.connect()
    chunks = ds.fetch("哈希表", limit=5)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Protocol, TypedDict, runtime_checkable

from exam_memory.chunking import chunk_text

logger = logging.getLogger(__name__)


# ── 类型定义 ─────────────────────────────────────────────────


class SourceChunk(TypedDict):
    """知识源返回的标准化 chunk。"""

    text: str
    source: str
    section: str
    metadata: dict[str, Any]


@runtime_checkable
class KnowledgeSource(Protocol):
    """知识源标准化接口。"""

    @property
    def name(self) -> str: ...

    @property
    def source_type(self) -> str: ...

    @property
    def connected(self) -> bool: ...

    def connect(self) -> bool: ...

    def fetch(self, topic: str, limit: int = 10) -> list[SourceChunk]: ...

    def list_topics(self) -> list[str]: ...

    def refresh(self) -> int: ...


# ── DirConnector 实现 ────────────────────────────────────────


class DirConnector:
    """本地目录连接器：扫描本地文档目录，按关键词检索并分块返回。"""

    def __init__(
        self,
        name: str,
        path: str | Path,
        glob_pattern: str = "*.md",
        chunk_size: int = 1600,
    ) -> None:
        self._name = name
        self._path = Path(path)
        self._glob_pattern = glob_pattern
        self._chunk_size = chunk_size
        self._connected = False
        self._files: list[Path] = []

    # ── Protocol properties ──────────────────────────────────

    @property
    def name(self) -> str:
        return self._name

    @property
    def source_type(self) -> str:
        return "local_dir"

    @property
    def connected(self) -> bool:
        return self._connected

    # ── Protocol methods ─────────────────────────────────────

    def connect(self) -> bool:
        """扫描目录，缓存文件列表。成功返回 True。"""
        if not self._path.is_dir():
            logger.warning("DirConnector: 路径不存在或不是目录: %s", self._path)
            return False
        self._files = sorted(self._path.glob(self._glob_pattern))
        self._connected = True
        logger.info("DirConnector '%s': 扫描到 %d 个文件", self._name, len(self._files))
        return True

    def fetch(self, topic: str, limit: int = 10) -> list[SourceChunk]:
        """在文件名和文件内容中做关键词匹配，命中文件读取后分块返回。

        Args:
            topic: 搜索关键词。
            limit: 最大返回 chunk 数。

        Returns:
            匹配到的 SourceChunk 列表，最多 limit 个。
        """
        if not self._connected:
            return []

        topic_lower = topic.lower()
        results: list[SourceChunk] = []

        for fpath in self._files:
            stem = fpath.stem.lower()
            # 优先匹配文件名
            filename_match = topic_lower in stem

            # 读取内容检查内容匹配
            try:
                text = fpath.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning("DirConnector: 读取失败 %s: %s", fpath, e)
                continue

            content_match = topic_lower in text.lower()

            if not filename_match and not content_match:
                continue

            # 分块
            chunks = chunk_text(text, max_chars=self._chunk_size)
            for chunk_text_str in chunks:
                section = chunk_text_str.split("\n")[0].strip()
                results.append(
                    SourceChunk(
                        text=chunk_text_str,
                        source=fpath.name,
                        section=section,
                        metadata={
                            "filename_match": filename_match,
                            "content_match": content_match,
                            "path": str(fpath),
                        },
                    )
                )

            if len(results) >= limit:
                break

        return results[:limit]

    def list_topics(self) -> list[str]:
        """返回已缓存文件名列表（去扩展名）。"""
        return [f.stem for f in self._files]

    def refresh(self) -> int:
        """重新扫描目录，返回新增文件数。"""
        old_count = len(self._files)
        old_set = set(self._files)
        self._files = sorted(self._path.glob(self._glob_pattern))
        new_set = set(self._files)
        added = len(new_set - old_set)
        logger.info("DirConnector '%s': refresh 完成，新增 %d 个文件", self._name, added)
        return added
