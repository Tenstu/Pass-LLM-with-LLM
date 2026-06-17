"""tests/test_knowledge_source.py — KnowledgeSource Protocol + DirConnector + SourceRegistry 测试。"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pathlib import Path

from exam_memory.knowledge_source import KnowledgeSource, DirConnector, SourceChunk
from exam_memory.source_registry import SourceRegistry


# ── DirConnector ─────────────────────────────────────────────


class TestDirConnectorConnect:
    """DirConnector.connect() 测试。"""

    def test_connect_valid_dir(self, tmp_path: Path) -> None:
        """connect() 成功扫描已有文件。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "hash.md").write_text("# 哈希表\n内容", encoding="utf-8")
        (d / "sort.md").write_text("# 排序\n内容", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d))
        assert ds.connect() is True
        assert ds.connected is True

    def test_connect_nonexistent_dir(self) -> None:
        """connect() 对不存在目录返回 False。"""
        ds = DirConnector(name="test", path="/nonexistent/path/xyz")
        assert ds.connect() is False
        assert ds.connected is False

    def test_connect_empty_dir(self, tmp_path: Path) -> None:
        """connect() 对空目录返回 True（合法但无文件）。"""
        d = tmp_path / "empty"
        d.mkdir()

        ds = DirConnector(name="test", path=str(d))
        assert ds.connect() is True
        assert ds.connected is True

    def test_connected_property(self, tmp_path: Path) -> None:
        """connected 在 connect 前后正确反映状态。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "a.md").write_text("a", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d))
        assert ds.connected is False
        ds.connect()
        assert ds.connected is True


class TestDirConnectorFetch:
    """DirConnector.fetch() 测试。"""

    def test_fetch_returns_chunks(self, tmp_path: Path) -> None:
        """fetch() 按 topic 匹配文件名返回 chunks。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "哈希表.md").write_text("# 哈希表\nO(1) 查找", encoding="utf-8")
        (d / "排序.md").write_text("# 排序\n快速排序", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d))
        ds.connect()

        chunks = ds.fetch("哈希表")
        assert len(chunks) == 1
        assert all(isinstance(c, dict) for c in chunks)
        assert "text" in chunks[0]
        assert chunks[0]["source"] == "哈希表.md"

    def test_fetch_topic_match_in_content(self, tmp_path: Path) -> None:
        """fetch() 按 topic 匹配文件内容返回 chunks。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "algos.md").write_text(
            "# 算法合集\n\n## 哈希表\n哈希表是一种 O(1) 数据结构",
            encoding="utf-8",
        )

        ds = DirConnector(name="test", path=str(d))
        ds.connect()

        chunks = ds.fetch("哈希表")
        assert len(chunks) > 0
        assert any("哈希表" in c["text"] for c in chunks)

    def test_fetch_no_match_returns_empty(self, tmp_path: Path) -> None:
        """fetch() 无匹配时返回空列表。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "sort.md").write_text("# 排序", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d))
        ds.connect()

        chunks = ds.fetch("完全不匹配的关键词")
        assert chunks == []

    def test_fetch_limit_respected(self, tmp_path: Path) -> None:
        """fetch() 的 limit 参数限制返回数量。"""
        d = tmp_path / "notes"
        d.mkdir()
        # 写一个长文本，会被分成多个 chunks
        long_text = "\n\n".join(
            [f"## 段落 {i}\n哈希表相关内容 {i} " + "x" * 200 for i in range(20)]
        )
        (d / "hash.md").write_text(long_text, encoding="utf-8")

        ds = DirConnector(name="test", path=str(d), chunk_size=400)
        ds.connect()

        chunks = ds.fetch("哈希表", limit=2)
        assert len(chunks) <= 2


class TestDirConnectorListTopics:
    """DirConnector.list_topics() 测试。"""

    def test_list_topics_returns_filenames_without_extension(self, tmp_path: Path) -> None:
        """list_topics() 返回去扩展名的文件名列表。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "hash.md").write_text("hash content", encoding="utf-8")
        (d / "sort.md").write_text("sort content", encoding="utf-8")
        (d / "graph.md").write_text("graph content", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d))
        ds.connect()

        topics = ds.list_topics()
        assert "hash" in topics
        assert "sort" in topics
        assert "graph" in topics
        # 确认不含扩展名
        assert not any(t.endswith(".md") for t in topics)


class TestDirConnectorRefresh:
    """DirConnector.refresh() 测试。"""

    def test_refresh_detects_new_files(self, tmp_path: Path) -> None:
        """refresh() 检测新增文件并返回新增数量。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "a.md").write_text("a", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d))
        ds.connect()
        assert len(ds.list_topics()) == 1

        # 添加新文件后 refresh
        (d / "b.md").write_text("b", encoding="utf-8")
        added = ds.refresh()
        assert added >= 1
        assert len(ds.list_topics()) == 2


# ── SourceRegistry ────────────────────────────────────────────


class TestSourceRegistryMount:
    """SourceRegistry.mount() 测试。"""

    def test_mount_success(self, tmp_path: Path) -> None:
        """mount() 成功注册已连接的源。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "a.md").write_text("a", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d))
        reg = SourceRegistry()
        assert reg.mount(ds) is True

    def test_mount_connect_failure(self) -> None:
        """mount() 对连接失败的源返回 False。"""
        ds = DirConnector(name="bad", path="/nonexistent/xyz")
        reg = SourceRegistry()
        assert reg.mount(ds) is False

    def test_mount_duplicate_returns_false(self, tmp_path: Path) -> None:
        """mount() 重复挂载同名源返回 False。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "a.md").write_text("a", encoding="utf-8")

        ds1 = DirConnector(name="same", path=str(d))
        ds2 = DirConnector(name="same", path=str(d))
        reg = SourceRegistry()
        assert reg.mount(ds1) is True
        assert reg.mount(ds2) is False


class TestSourceRegistryUnmount:
    """SourceRegistry.unmount() 测试。"""

    def test_unmount_existing(self, tmp_path: Path) -> None:
        """unmount() 移除已挂载源并返回 True。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "a.md").write_text("a", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d))
        reg = SourceRegistry()
        reg.mount(ds)
        assert reg.unmount("test") is True
        assert reg.get("test") is None

    def test_unmount_nonexistent(self) -> None:
        """unmount() 不存在的源返回 False。"""
        reg = SourceRegistry()
        assert reg.unmount("nope") is False


class TestSourceRegistryGet:
    """SourceRegistry.get() 测试。"""

    def test_get_existing(self, tmp_path: Path) -> None:
        """get() 返回已挂载的源实例。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "a.md").write_text("a", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d))
        reg = SourceRegistry()
        reg.mount(ds)
        assert reg.get("test") is ds

    def test_get_nonexistent(self) -> None:
        """get() 不存在的源返回 None。"""
        reg = SourceRegistry()
        assert reg.get("nope") is None


class TestSourceRegistryListMounted:
    """SourceRegistry.list_mounted() 测试。"""

    def test_list_mounted_returns_info(self, tmp_path: Path) -> None:
        """list_mounted() 返回已挂载源的信息列表。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "a.md").write_text("a", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d))
        reg = SourceRegistry()
        reg.mount(ds)

        result = reg.list_mounted()
        assert len(result) == 1
        assert result[0]["name"] == "test"
        assert result[0]["source_type"] == "local_dir"
        assert result[0]["connected"] is True
        assert result[0]["topic_count"] == 1


class TestSourceRegistryFetch:
    """SourceRegistry.fetch_from / fetch_all 测试。"""

    def test_fetch_from(self, tmp_path: Path) -> None:
        """fetch_from() 从指定源检索。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "哈希表.md").write_text("# 哈希表\nO(1) 查找", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d))
        reg = SourceRegistry()
        reg.mount(ds)

        chunks = reg.fetch_from("test", "哈希表")
        assert len(chunks) > 0

    def test_fetch_from_nonexistent(self) -> None:
        """fetch_from() 不存在的源返回空列表。"""
        reg = SourceRegistry()
        chunks = reg.fetch_from("nope", "topic")
        assert chunks == []

    def test_fetch_all_multiple_sources(self, tmp_path: Path) -> None:
        """fetch_all() 遍历所有已挂载源合并结果。"""
        d1 = tmp_path / "s1"
        d1.mkdir()
        (d1 / "哈希表.md").write_text("源1 哈希表内容", encoding="utf-8")

        d2 = tmp_path / "s2"
        d2.mkdir()
        (d2 / "哈希表.md").write_text("源2 哈希表内容", encoding="utf-8")

        ds1 = DirConnector(name="s1", path=str(d1))
        ds2 = DirConnector(name="s2", path=str(d2))
        reg = SourceRegistry()
        reg.mount(ds1)
        reg.mount(ds2)

        result = reg.fetch_all("哈希表")
        assert "s1" in result
        assert "s2" in result
        assert len(result["s1"]) > 0
        assert len(result["s2"]) > 0


# ── 边界测试 ─────────────────────────────────────────────────


class TestDirConnectorEdgeCases:
    """DirConnector 边界 case。"""

    def test_connect_path_is_file_not_dir(self, tmp_path: Path) -> None:
        """connect() 对文件路径（非目录）返回 False。"""
        f = tmp_path / "file.md"
        f.write_text("content", encoding="utf-8")

        ds = DirConnector(name="test", path=str(f))
        assert ds.connect() is False

    def test_fetch_glob_no_match(self, tmp_path: Path) -> None:
        """glob_pattern 不匹配任何文件时 fetch 返回空。"""
        d = tmp_path / "notes"
        d.mkdir()
        # 文件是 .txt，但 glob 只匹配 *.md
        (d / "data.txt").write_text("哈希表内容", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d), glob_pattern="*.md")
        ds.connect()
        assert ds.list_topics() == []
        assert ds.fetch("哈希表") == []

    def test_fetch_large_file_chunking(self, tmp_path: Path) -> None:
        """大文件正确分块，每个 chunk 不超过 chunk_size。"""
        d = tmp_path / "notes"
        d.mkdir()
        chunk_size = 500
        # 生成超长文本
        large_text = "\n\n".join([f"## Section {i}\n哈希表 section {i} " + "x" * 100 for i in range(30)])
        (d / "big.md").write_text(large_text, encoding="utf-8")

        ds = DirConnector(name="test", path=str(d), chunk_size=chunk_size)
        ds.connect()

        chunks = ds.fetch("哈希表", limit=100)
        assert len(chunks) > 1
        for c in chunks:
            # chunk_text 不会切开一个段落；单个段落最长约 100 个填充字符加标题/空白。
            assert len(c["text"]) <= chunk_size + 100


class TestSourceRegistryEdgeCases:
    """SourceRegistry 边界 case。"""

    def test_unmount_then_fetch_returns_empty(self, tmp_path: Path) -> None:
        """unmount 后 fetch 返回空。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "哈希表.md").write_text("哈希表内容", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d))
        reg = SourceRegistry()
        reg.mount(ds)

        # 确认 fetch 有结果
        assert len(reg.fetch_from("test", "哈希表")) > 0

        # unmount 后 fetch 为空
        reg.unmount("test")
        assert reg.fetch_from("test", "哈希表") == []

    def test_fetch_all_empty_registry(self) -> None:
        """空 registry 的 fetch_all 返回空 dict。"""
        reg = SourceRegistry()
        result = reg.fetch_all("any topic")
        assert result == {}
