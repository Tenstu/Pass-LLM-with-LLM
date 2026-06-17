"""source_registry.py — SourceRegistry 生命周期管理。

管理已挂载知识源的 mount/unmount/list/fetch 操作。

用法:
    from exam_memory.source_registry import SourceRegistry
    from exam_memory.knowledge_source import DirConnector

    reg = SourceRegistry()
    reg.mount(DirConnector(name="notes", path="./notes/"))
    chunks = reg.fetch_from("notes", "哈希表")
"""

from __future__ import annotations

import logging
from typing import Any

from exam_memory.knowledge_source import DirConnector, KnowledgeSource, SourceChunk

logger = logging.getLogger(__name__)


class SourceRegistry:
    """管理已挂载知识源的生命周期。"""

    def __init__(self) -> None:
        self._sources: dict[str, KnowledgeSource] = {}

    def mount(self, source: KnowledgeSource) -> bool:
        """挂载知识源。调用 connect()，成功注册，失败返回 False，已存在返回 False。"""
        if source.name in self._sources:
            logger.warning("SourceRegistry: 源 '%s' 已存在，跳过", source.name)
            return False
        if not source.connect():
            return False
        self._sources[source.name] = source
        logger.info("SourceRegistry: 挂载成功 '%s'", source.name)
        return True

    def unmount(self, name: str) -> bool:
        """移除已挂载源。存在返回 True，不存在返回 False。"""
        if name not in self._sources:
            return False
        del self._sources[name]
        logger.info("SourceRegistry: 卸载 '%s'", name)
        return True

    def get(self, name: str) -> KnowledgeSource | None:
        """获取已挂载源，不存在返回 None。"""
        return self._sources.get(name)

    def list_mounted(self) -> list[dict[str, Any]]:
        """返回已挂载源的状态列表。"""
        return [
            {
                "name": src.name,
                "source_type": src.source_type,
                "connected": src.connected,
                "topic_count": len(src.list_topics()),
            }
            for src in self._sources.values()
        ]

    def fetch_from(self, source_name: str, topic: str, limit: int = 10) -> list[SourceChunk]:
        """从指定源检索，源不存在时返回空列表。"""
        source = self._sources.get(source_name)
        if source is None:
            return []
        return source.fetch(topic, limit=limit)

    def fetch_all(self, topic: str, limit: int = 5) -> dict[str, list[SourceChunk]]:
        """遍历所有已挂载源，合并检索结果。"""
        result: dict[str, list[SourceChunk]] = {}
        for name, source in self._sources.items():
            chunks = source.fetch(topic, limit=limit)
            result[name] = chunks
        return result
