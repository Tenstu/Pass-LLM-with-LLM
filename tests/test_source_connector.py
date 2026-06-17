"""tests/test_source_connector.py — SourceConnector 单元测试。"""
from __future__ import annotations

import pytest

from exam_memory.question_bank import QuestionBank
from exam_memory.source_connector import SourceConnector
from exam_memory.source_registry import SourceRegistry
from exam_memory.knowledge_source import DirConnector


# ── Fixtures ──────────────────────────────────────────────────

MOCK_RAW = """\
---
## 测试题

这是一道测试题。

### 选项

**A.** 选项A
**B.** 选项B
**C.** 选项C
**D.** 选项D

### 答案

C

### 解析

测试解析。
---
"""


@pytest.fixture
def connector(tmp_path, monkeypatch):
    bank = QuestionBank(bank_dir=tmp_path)
    monkeypatch.setattr(bank, "_call_llm", lambda s, u: MOCK_RAW)
    return SourceConnector(bank)


@pytest.fixture
def connector_no_llm(tmp_path, monkeypatch):
    bank = QuestionBank(bank_dir=tmp_path)
    monkeypatch.setattr(bank, "_call_llm", lambda s, u: None)
    return SourceConnector(bank)


# ── connect() 自动路由 ────────────────────────────────────────

class TestConnect:
    def test_connect_text(self, connector):
        result = connector.connect("哈希表是 O(1) 查找结构", topic="哈希表")
        assert result["error"] is None
        assert len(result["saved"]) == 1

    def test_connect_file(self, connector, tmp_path):
        fp = tmp_path / "notes.md"
        fp.write_text("快排平均 O(n log n) 时间复杂度。", encoding="utf-8")
        result = connector.connect(str(fp), topic="排序")
        assert result["error"] is None
        assert len(result["saved"]) == 1

    def test_connect_chunks(self, connector):
        chunks = [{"text": "BFS 从起点逐层遍历。"}, {"text": "DFS 深度优先。"}]
        result = connector.connect(chunks, topic="图遍历")
        assert result["error"] is None
        assert len(result["saved"]) == 1

    def test_connect_empty_text(self, connector):
        result = connector.connect("", topic="x")
        assert result["error"] is not None
        assert "为空" in result["error"]

    def test_connect_nonexistent_file(self, connector):
        result = connector.connect("/no/such/file.md", topic="x")
        assert result["error"] is not None
        assert "不存在" in result["error"]

    def test_connect_empty_chunks(self, connector):
        result = connector.connect([], topic="x")
        assert result["error"] is not None
        assert "为空" in result["error"]

    def test_connect_chunks_no_text(self, connector):
        result = connector.connect([{"text": ""}, {"other": "data"}], topic="x")
        assert result["error"] is not None

    def test_connect_unsupported_type(self, connector):
        result = connector.connect(12345, topic="x")  # type: ignore
        assert result["error"] is not None
        assert "不支持" in result["error"]


# ── 显式入口 ──────────────────────────────────────────────────

class TestExplicitMethods:
    def test_from_text(self, connector):
        result = connector.from_text("动态规划核心是状态转移。", topic="DP")
        assert result["error"] is None
        assert len(result["saved"]) == 1

    def test_from_file(self, connector, tmp_path):
        fp = tmp_path / "dp.md"
        fp.write_text("背包问题是经典 DP。", encoding="utf-8")
        result = connector.from_file(fp, topic="背包")
        assert result["error"] is None

    def test_from_chunks(self, connector):
        result = connector.from_chunks(
            [{"text": "二分查找 O(log n)"}], topic="二分",
        )
        assert result["error"] is None

    def test_from_file_empty(self, connector, tmp_path):
        fp = tmp_path / "empty.md"
        fp.write_text("", encoding="utf-8")
        result = connector.from_file(fp, topic="x")
        assert result["error"] is not None

    def test_from_file_nonexistent(self, connector):
        result = connector.from_file("/no/such/path.md", topic="x")
        assert result["error"] is not None


# ── LLM 不可用 ────────────────────────────────────────────────

class TestNoLLM:
    def test_text_no_llm(self, connector_no_llm):
        result = connector_no_llm.from_text("some text", topic="x")
        assert result["error"] is not None

    def test_chunks_no_llm(self, connector_no_llm):
        result = connector_no_llm.from_chunks([{"text": "chunk"}], topic="x")
        assert result["error"] is not None


# ── 错误处理边界 ──────────────────────────────────────────────

class TestErrorBoundary:
    def test_from_text_converts_question_bank_value_error(self, connector, monkeypatch):
        """SourceConnector 是管道层，应把 QuestionBank 校验异常转换为 result dict。"""

        def fail_text_extract(*args, **kwargs):
            raise ValueError("不支持的题型：坏类型")

        monkeypatch.setattr(connector._bank, "text_extract", fail_text_extract)

        result = connector.from_text("有效文本", topic="T", q_type="坏类型")

        assert result["saved"] == []
        assert result["validated"] == []
        assert result["rejected"] == []
        assert result["raw_llm_output"] is None
        assert result["error"] == "不支持的题型：坏类型"

    def test_from_chunks_converts_question_bank_value_error(self, connector, monkeypatch):
        """chunks 入口同样遵守管道层 result-dict 契约。"""

        def fail_text_extract(*args, **kwargs):
            raise ValueError("题目重复：stem")

        monkeypatch.setattr(connector._bank, "text_extract", fail_text_extract)

        result = connector.from_chunks([{"text": "有效 chunk"}], topic="T")

        assert result["saved"] == []
        assert result["error"] == "题目重复：stem"


# ── 参数传递 ──────────────────────────────────────────────────

class TestParameterPassing:
    def test_count_and_type_forwarded(self, connector, monkeypatch):
        """验证 count, q_type, difficulty 正确传递到 text_extract。"""
        captured = {}
        original_text_extract = connector._bank.text_extract

        def spy(text, topic, count=3, q_type="算法", difficulty="中等"):
            captured["count"] = count
            captured["q_type"] = q_type
            captured["difficulty"] = difficulty
            return original_text_extract(text, topic, count, q_type, difficulty)

        monkeypatch.setattr(connector._bank, "text_extract", spy)
        connector.connect("text", topic="T", count=5, q_type="单选题", difficulty="困难")
        assert captured["count"] == 5
        assert captured["q_type"] == "单选题"
        assert captured["difficulty"] == "困难"


# ── from_source() ─────────────────────────────────────────────

class TestFromSource:
    def test_from_source_with_registry(self, tmp_path, monkeypatch):
        """from_source() 通过 registry 检索并出题。"""
        d = tmp_path / "notes"
        d.mkdir()
        (d / "哈希表.md").write_text("哈希表 O(1) 查找", encoding="utf-8")

        ds = DirConnector(name="test", path=str(d))
        reg = SourceRegistry()
        reg.mount(ds)

        bank = QuestionBank(bank_dir=tmp_path)
        monkeypatch.setattr(bank, "_call_llm", lambda s, u: MOCK_RAW)
        conn = SourceConnector(bank, registry=reg)

        result = conn.from_source("test", "哈希表")
        assert result["error"] is None
        assert len(result["saved"]) == 1

    def test_from_source_no_registry_returns_error(self, tmp_path, monkeypatch):
        """from_source() 无 registry 时返回错误。"""
        bank = QuestionBank(bank_dir=tmp_path)
        monkeypatch.setattr(bank, "_call_llm", lambda s, u: MOCK_RAW)
        conn = SourceConnector(bank)  # 无 registry

        result = conn.from_source("test", "topic")
        assert result["error"] is not None
        assert "registry" in result["error"].lower() or "未配置" in result["error"]

    def test_from_source_nonexistent_source_returns_error(self, tmp_path, monkeypatch):
        """from_source() 不存在的源返回错误。"""
        reg = SourceRegistry()
        bank = QuestionBank(bank_dir=tmp_path)
        monkeypatch.setattr(bank, "_call_llm", lambda s, u: MOCK_RAW)
        conn = SourceConnector(bank, registry=reg)

        result = conn.from_source("nope", "topic")
        assert result["error"] is not None
        assert "不存在" in result["error"] or "未找到" in result["error"]
