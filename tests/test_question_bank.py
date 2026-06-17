"""tests/test_question_bank.py — 题库模块单元测试。

覆盖: CRUD / QuestionParser / QualityValidator / PromptBuilder / generate 管道 / import_from_dir
运行: pytest tests/test_question_bank.py -v
"""
from __future__ import annotations

import pytest

from exam_memory.question_bank import (
    QuestionBank,
    QuestionParser,
    QualityValidator,
    PromptBuilder,
    ReviewGate,
    MODE_RAG,
    MODE_TEXT,
    MODE_DIRECT,
    _body,
    _extract_title,
    _parse_frontmatter,
)


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def sample_question(tmp_path):
    """手动创建一条题目，返回 (bank, filename)。"""
    bank = QuestionBank(bank_dir=tmp_path)
    fn = bank.add_manual(
        title="两数之和",
        content="给定一个整数数组 nums 和一个目标值 target，找出和为目标值的两个数。",
        q_type="算法",
        knowledge="双指针",
        answer="C",
        options={
            "A": "O(n^2) 暴力枚举",
            "B": "O(n log n) 排序后二分",
            "C": "O(n) 哈希表",
            "D": "O(n) 双指针（需先排序）",
        },
        explanation="用哈希表记录已遍历的值，查找 complement 在 O(1) 内完成。",
        difficulty="中等",
    )
    return bank, fn


# ── _parse_frontmatter ────────────────────────────────────────

class TestParseFrontmatter:
    def test_valid(self):
        text = "---\ntype: 算法\nknowledge: 双指针\n---\n\nbody"
        result = _parse_frontmatter(text)
        assert result["type"] == "算法"
        assert result["knowledge"] == "双指针"

    def test_no_frontmatter(self):
        assert _parse_frontmatter("plain body") == {}

    def test_incomplete(self):
        assert _parse_frontmatter("---\ntype: 算法") == {}

    def test_empty_yaml(self):
        assert _parse_frontmatter("---\n---\n\nbody") == {}


# ── _body / _extract_title ────────────────────────────────────

class TestBodyHelpers:
    def test_body_with_frontmatter(self):
        text = "---\nkey: val\n---\n\n## Hello\n\ncontent"
        assert _body(text) == "## Hello\n\ncontent"

    def test_body_without_frontmatter(self):
        assert _body("plain text") == "plain text"

    def test_extract_title(self):
        text = "# H1\n## My Title\n\nbody"
        assert _extract_title(text) == "My Title"

    def test_extract_title_none(self):
        assert _extract_title("no heading") is None


# ── Filename sequencing ───────────────────────────────────────

class TestFilenameSequencing:
    def test_uuid_filenames_keep_incrementing_sequence(self, tmp_path):
        bank = QuestionBank(bank_dir=tmp_path)
        common = {
            "content": "题干内容",
            "q_type": "算法",
            "knowledge": "哈希表",
            "answer": "A",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
        }

        first = bank.add_manual(title="T1", **common)
        second = bank.add_manual(title="T2", **common)

        assert first.startswith("算法_哈希表_001_")
        assert second.startswith("算法_哈希表_002_")


# ── QualityValidator ──────────────────────────────────────────

class TestQualityValidator:
    @pytest.fixture
    def v(self):
        return QualityValidator()

    def test_valid_question(self, v):
        q = {"stem": "题目", "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
             "answer": "C", "explanation": "解析"}
        valid, invalid = v.validate([q])
        assert len(valid) == 1
        assert len(invalid) == 0

    def test_empty_stem(self, v):
        q = {"stem": "", "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
             "answer": "C", "explanation": "解析"}
        valid, invalid = v.validate([q])
        assert len(valid) == 0
        assert len(invalid) == 1
        assert "题干为空" in invalid[0]["_reject_reason"]

    def test_too_few_options(self, v):
        q = {"stem": "题目", "options": {"A": "1", "B": "2"},
             "answer": "A", "explanation": "解析"}
        valid, invalid = v.validate([q])
        assert len(invalid) == 1

    def test_multi_char_answer(self, v):
        q = {"stem": "题目", "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
             "answer": "AC", "explanation": "解析"}
        valid, invalid = v.validate([q])
        assert len(invalid) == 1

    def test_out_of_range_answer(self, v):
        q = {"stem": "题目", "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
             "answer": "E", "explanation": "解析"}
        valid, invalid = v.validate([q])
        assert len(invalid) == 1

    def test_empty_explanation(self, v):
        v2 = QualityValidator(require_explanation=True)
        q = {"stem": "题目", "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
             "answer": "A", "explanation": ""}
        valid, invalid = v2.validate([q])
        assert len(invalid) == 1

    def test_no_explanation_required(self):
        v = QualityValidator(require_explanation=False)
        q = {"stem": "题目", "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
             "answer": "A", "explanation": ""}
        valid, invalid = v.validate([q])
        assert len(valid) == 1


# ── QuestionParser ────────────────────────────────────────────

class TestQuestionParser:
    @pytest.fixture
    def parser(self):
        return QuestionParser()

    def test_parse_single(self, parser):
        raw = """\
---
## 两数之和

给定整数数组，求和为 target 的两数。

### 选项

**A.** O(n^2) 暴力
**B.** O(n log n) 排序二分
**C.** O(n) 哈希表
**D.** O(n) 双指针

### 答案

C

### 解析

用哈希表记录遍历过的值。
---"""
        results = parser.parse(raw)
        assert len(results) == 1
        assert results[0]["answer"] == "C"
        assert "给定整数数组" in results[0]["stem"]
        assert len(results[0]["options"]) == 4
        assert "哈希表" in results[0]["explanation"]

    def test_parse_multiple(self, parser):
        raw = """\
---
## Q1
题干1
### 选项
**A.** a1
**B.** a2
**C.** a3
**D.** a4
### 答案
B
### 解析
解析1
---
## Q2
题干2
### 选项
**A.** b1
**B.** b2
**C.** b3
### 答案
C
### 解析
解析2
---"""
        results = parser.parse(raw)
        assert len(results) == 2
        assert results[0]["answer"] == "B"
        assert results[1]["answer"] == "C"

    def test_parse_empty(self, parser):
        assert parser.parse("") == []
        assert parser.parse("no markers here") == []

    def test_parse_missing_answer(self, parser):
        raw = "## 题\n题干\n### 选项\n**A.** x"
        results = parser.parse(raw)
        assert len(results) == 0  # no answer -> skipped

    def test_parse_case_insensitive_answer(self, parser):
        raw = "## 题\n题干\n### 选项\n**A.** x\n**B.** y\n**C.** z\n**D.** w\n### 答案\nc\n### 解析\n解析\n"
        results = parser.parse(raw)
        assert results[0]["answer"] == "C"


# ── PromptBuilder ─────────────────────────────────────────────

class TestPromptBuilder:
    @pytest.fixture
    def builder(self):
        return PromptBuilder()

    def test_build_basic(self, builder):
        system, user = builder.build([], "双指针", "算法", 3)
        assert "双指针" in user
        assert "3 道" in user
        assert "算法" in user
        assert "出题专家" in system

    def test_build_with_chunks(self, builder):
        chunks = [{"text": "哈希表可以在 O(n) 时间内完成查找。"}]
        system, user = builder.build(chunks, "哈希表", "单选题", 2)
        assert "哈希表" in user
        assert "参考资料" in user

    def test_build_limits_chunks(self, builder):
        chunks = [{"text": f"chunk {i}"} for i in range(10)]
        system, user = builder.build(chunks, "x", "算法", 2)
        for i in range(5):
            assert f"chunk {i}" in user
        assert "chunk 5" not in user

    def test_build_mode_text(self, builder):
        system, user = builder.build(
            [], "排序", "单选题", 2,
            mode=MODE_TEXT, source_text="快速排序是分治算法。",
        )
        assert "快速排序是分治算法" in user
        assert "参考资料" in user
        assert "排序" in user

    def test_build_mode_text_empty_source(self, builder):
        system, user = builder.build(
            [], "排序", "单选题", 2,
            mode=MODE_TEXT, source_text="",
        )
        assert "无参考资料" in user

    def test_build_mode_direct(self, builder):
        system, user = builder.build(
            [], "BFS", "算法", 3, mode=MODE_DIRECT,
        )
        assert "BFS" in user
        assert "3 道" in user
        assert "参考资料" not in user

    def test_build_backward_compat_default_rag(self, builder):
        """默认模式为 MODE_RAG，保持向后兼容。"""
        chunks = [{"text": "chunk A"}]
        system, user = builder.build(chunks, "K", "算法", 1)
        assert "chunk A" in user
        assert "参考资料" in user


# ── CRUD ──────────────────────────────────────────────────────

class TestCRUD:
    def test_add_manual_basic(self, tmp_bank):
        fn = tmp_bank.add_manual(
            title="T", content="C", q_type="算法",
            knowledge="K", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )
        assert fn.startswith("算法_K_")
        assert fn.endswith(".md")
        assert tmp_bank.count() == 1

    def test_add_creates_valid_file(self, tmp_bank):
        fn = tmp_bank.add_manual(
            title="两数之和", content="题干", q_type="算法",
            knowledge="双指针", answer="C",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )
        fp = tmp_bank.bank_dir / fn
        assert fp.exists()
        text = fp.read_text(encoding="utf-8")
        assert text.startswith("---")
        assert "type: 算法" in text
        assert "knowledge: 双指针" in text
        assert "question_id:" in text

    def test_add_invalid_type(self, tmp_bank):
        with pytest.raises(ValueError, match="不支持的题型"):
            tmp_bank.add_manual(
                title="T", content="C", q_type="论述题",
                knowledge="K", answer="A",
                options={"A": "1", "B": "2", "C": "3", "D": "4"},
            )

    def test_add_invalid_difficulty(self, tmp_bank):
        with pytest.raises(ValueError, match="不支持的难度"):
            tmp_bank.add_manual(
                title="T", content="C", q_type="算法",
                knowledge="K", answer="A",
                options={"A": "1", "B": "2", "C": "3", "D": "4"},
                difficulty="极难",
            )

    def test_get_existing(self, sample_question):
        bank, fn = sample_question
        qid = fn.replace(".md", "")
        item = bank.get(qid)
        assert item is not None
        assert item["title"] == "两数之和"
        assert item["knowledge"] == "双指针"
        assert "### 答案\n\nC" in item["body"]
        assert "双指针" in item["body"]

    def test_get_missing(self, tmp_bank):
        assert tmp_bank.get("bank_nonexistent") is None

    def test_list_all_empty(self, tmp_bank):
        assert tmp_bank.list_all() == []

    def test_list_all_filtered(self, tmp_bank):
        tmp_bank.add_manual(title="T1", content="C", q_type="算法",
                           knowledge="双指针", answer="A",
                           options={"A": "1", "B": "2", "C": "3", "D": "4"})
        tmp_bank.add_manual(title="T2", content="C", q_type="单选题",
                           knowledge="排序", answer="B",
                           options={"A": "1", "B": "2", "C": "3", "D": "4"})
        all_items = tmp_bank.list_all()
        assert len(all_items) == 2
        algo_items = tmp_bank.list_all(q_type="算法")
        assert len(algo_items) == 1
        assert algo_items[0]["knowledge"] == "双指针"

    def test_delete_existing(self, sample_question):
        bank, fn = sample_question
        qid = fn.replace(".md", "")
        assert bank.delete(qid) is True
        assert bank.count() == 0
        assert bank.get(qid) is None

    def test_delete_missing(self, tmp_bank):
        assert tmp_bank.delete("bank_nonexist") is False

    def test_count(self, tmp_bank):
        assert tmp_bank.count() == 0
        for i in range(3):
            tmp_bank.add_manual(
                title=f"T{i}", content="C", q_type="算法",
                knowledge="K", answer="A",
                options={"A": "1", "B": "2", "C": "3", "D": "4"},
            )
        assert tmp_bank.count() == 3
        assert tmp_bank.count(q_type="算法") == 3


# ── generate 管道 ─────────────────────────────────────────────

class TestGenerate:
    @pytest.fixture
    def bank_with_mock(self, tmp_path, monkeypatch):
        """带 mock LLM 的 QuestionBank。"""
        bank = QuestionBank(bank_dir=tmp_path)
        mock_raw = """\
---
## 哈希表查找

在 O(n) 时间内查找 target 的索引。

### 选项

**A.** 两层循环 O(n^2)
**B.** 排序后二分 O(n log n)
**C.** 哈希表 O(n)
**D.** 动态规划 O(n^2)

### 答案

C

### 解析

一次遍历，哈希表记录已访问元素及其索引。
---

## 快排分区

实现快速排序的分区函数。

### 选项

**A.** pivot 选首元素
**B.** pivot 选尾元素
**C.** pivot 随机选择
**D.** pivot 选中位数

### 答案

C

### 解析

随机 pivot 避免最坏情况 O(n^2)。
---
"""
        monkeypatch.setattr(bank, "_call_llm", lambda s, u: mock_raw)
        return bank

    def test_generate_saves_questions(self, bank_with_mock):
        result = bank_with_mock.generate(
            topic="哈希表", count=2, q_type="算法", difficulty="中等",
        )
        assert result["error"] is None
        assert len(result["saved"]) == 2
        assert len(result["validated"]) == 2
        assert result["rejected"] == []

    def test_generate_sets_metadata(self, bank_with_mock):
        result = bank_with_mock.generate(
            topic="排序", count=1, q_type="算法", difficulty="困难",
        )
        saved = result["validated"]
        assert len(saved) >= 1
        for s in saved:
            assert s["knowledge"] == "排序"
            assert s["difficulty"] == "困难"
            assert s["generated"] is True
            assert s["reviewed"] is False

    def test_generate_no_llm(self, tmp_path, monkeypatch):
        """litellm 不可用时返回 error。"""
        bank = QuestionBank(bank_dir=tmp_path)
        monkeypatch.setattr(bank, "_call_llm", lambda s, u: None)
        result = bank.generate(topic="x", count=1)
        assert result["error"] is not None
        assert result["saved"] == []

    def test_generate_rejects_bad_output(self, tmp_path, monkeypatch):
        bank = QuestionBank(bank_dir=tmp_path)
        monkeypatch.setattr(bank, "_call_llm", lambda s, u: "not a valid question format")
        result = bank.generate(topic="x", count=1)
        assert result["error"] is not None
        assert len(result["saved"]) == 0

    def test_generate_rejects_invalid_options_count(self, tmp_path, monkeypatch):
        bank = QuestionBank(bank_dir=tmp_path)
        raw = "## 题\n题干\n### 选项\n**A.** x\n**B.** y\n### 答案\nA\n### 解析\np\n"
        monkeypatch.setattr(bank, "_call_llm", lambda s, u: raw)
        result = bank.generate(topic="x", count=1)
        assert len(result["rejected"]) >= 1


# ── 三类提取管道 ──────────────────────────────────────────────

class TestExtractionPipelines:
    MOCK_RAW = """\
---
## 哈希表查找

在 O(n) 时间内查找 target 的索引。

### 选项

**A.** 两层循环 O(n^2)
**B.** 排序后二分 O(n log n)
**C.** 哈希表 O(n)
**D.** 动态规划 O(n^2)

### 答案

C

### 解析

一次遍历，哈希表记录已访问元素及其索引。
---
"""

    def test_rag_extract_saves(self, tmp_path, monkeypatch):
        bank = QuestionBank(bank_dir=tmp_path)
        monkeypatch.setattr(bank, "_call_llm", lambda s, u: self.MOCK_RAW)
        result = bank.rag_extract(topic="哈希表", count=1, q_type="算法")
        assert result["error"] is None
        assert len(result["saved"]) == 1

    def test_text_extract_saves(self, tmp_path, monkeypatch):
        bank = QuestionBank(bank_dir=tmp_path)
        monkeypatch.setattr(bank, "_call_llm", lambda s, u: self.MOCK_RAW)
        result = bank.text_extract(
            source_text="哈希表是 O(1) 查找的数据结构。",
            topic="哈希表", count=1, q_type="算法",
        )
        assert result["error"] is None
        assert len(result["saved"]) == 1

    def test_text_extract_passes_source_text(self, tmp_path, monkeypatch):
        """验证 source_text 出现在 prompt 中。"""
        bank = QuestionBank(bank_dir=tmp_path)
        captured = {}
        def mock_llm(system, user):
            captured["user"] = user
            return self.MOCK_RAW
        monkeypatch.setattr(bank, "_call_llm", mock_llm)
        bank.text_extract(
            source_text="快排平均 O(n log n)", topic="排序", count=1,
        )
        assert "快排平均 O(n log n)" in captured["user"]

    def test_direct_extract_saves(self, tmp_path, monkeypatch):
        bank = QuestionBank(bank_dir=tmp_path)
        monkeypatch.setattr(bank, "_call_llm", lambda s, u: self.MOCK_RAW)
        result = bank.direct_extract(topic="BFS", count=1, q_type="算法")
        assert result["error"] is None
        assert len(result["saved"]) == 1

    def test_direct_extract_no_context(self, tmp_path, monkeypatch):
        """验证直出模式 prompt 中无参考资料。"""
        bank = QuestionBank(bank_dir=tmp_path)
        captured = {}
        def mock_llm(system, user):
            captured["user"] = user
            return self.MOCK_RAW
        monkeypatch.setattr(bank, "_call_llm", mock_llm)
        bank.direct_extract(topic="DFS", count=1)
        assert "参考资料" not in captured["user"]

    def test_generate_equals_rag_extract(self, tmp_path, monkeypatch):
        """generate() 向后兼容，等价于 rag_extract()。两者共享管道。"""
        bank = QuestionBank(bank_dir=tmp_path)
        monkeypatch.setattr(bank, "_call_llm", lambda s, u: self.MOCK_RAW)
        r1 = bank.generate(topic="哈希表", count=1)
        assert r1["error"] is None
        assert len(r1["saved"]) == 1
        # 第二次调用同 topic，重复题目被去重拒绝
        r2 = bank.rag_extract(topic="哈希表", count=1)
        assert r2["error"] is None
        assert len(r2["saved"]) == 0  # 去重：已存在
        assert len(r2["rejected"]) >= 1

    def test_text_extract_no_llm(self, tmp_path, monkeypatch):
        bank = QuestionBank(bank_dir=tmp_path)
        monkeypatch.setattr(bank, "_call_llm", lambda s, u: None)
        result = bank.text_extract(source_text="x", topic="x", count=1)
        assert result["error"] is not None

    def test_direct_extract_no_llm(self, tmp_path, monkeypatch):
        bank = QuestionBank(bank_dir=tmp_path)
        monkeypatch.setattr(bank, "_call_llm", lambda s, u: None)
        result = bank.direct_extract(topic="x", count=1)
        assert result["error"] is not None


# ── ReviewGate ────────────────────────────────────────────────

class TestReviewGate:
    @pytest.fixture
    def gate_setup(self, tmp_path):
        """创建 bank + 一条完整题目 + ReviewGate。"""
        bank = QuestionBank(bank_dir=tmp_path)
        fn = bank.add_manual(
            title="两数之和", content="给定数组和目标值，找两数之和。",
            q_type="算法", knowledge="双指针", answer="C",
            options={"A": "暴力", "B": "排序", "C": "哈希", "D": "DP"},
            explanation="哈希表 O(n)。",
        )
        qid = fn.replace(".md", "")
        gate = ReviewGate(bank)
        return bank, gate, qid

    def test_approve_sets_reviewed(self, gate_setup):
        bank, gate, qid = gate_setup
        assert gate.approve(qid) is True
        item = bank.get(qid)
        assert item["reviewed"] is True

    def test_reject_sets_unreviewed(self, gate_setup):
        bank, gate, qid = gate_setup
        gate.approve(qid)
        assert gate.reject(qid) is True
        item = bank.get(qid)
        assert item["reviewed"] is False

    def test_approve_nonexistent(self, tmp_path):
        bank = QuestionBank(bank_dir=tmp_path)
        gate = ReviewGate(bank)
        assert gate.approve("nonexistent") is False

    def test_reject_nonexistent(self, tmp_path):
        bank = QuestionBank(bank_dir=tmp_path)
        gate = ReviewGate(bank)
        assert gate.reject("nonexistent") is False

    def test_review_gate_approve_valid(self, gate_setup):
        _, gate, qid = gate_setup
        result = gate.review_gate(qid)
        assert result["decision"] == "approve"
        assert result["reasons"] == []

    def test_review_gate_rejects_unreviewed(self, gate_setup):
        """未审核的题目通过 review_gate 自动校验。"""
        bank, gate, qid = gate_setup
        # 新建的题目 reviewed=False，review_gate 应做质量校验
        result = gate.review_gate(qid)
        # 这道题质量合格，应自动 approve
        assert result["decision"] == "approve"

    def test_review_gate_nonexistent(self, tmp_path):
        bank = QuestionBank(bank_dir=tmp_path)
        gate = ReviewGate(bank)
        result = gate.review_gate("no_such_id")
        assert result["decision"] == "reject"
        assert "不存在" in result["reasons"][0]

    def test_review_gate_roundtrip(self, gate_setup):
        """approve → review_gate → 自动 approve 流程。"""
        bank, gate, qid = gate_setup
        gate.approve(qid)
        result = gate.review_gate(qid)
        assert result["decision"] == "approve"


# ── 精确去重 ──────────────────────────────────────────────────

class TestDedup:
    def test_add_duplicate_stem_raises(self, tmp_path):
        """相同题干内容应触发去重（check_dup=True）。"""
        bank = QuestionBank(bank_dir=tmp_path)
        bank.add_manual(
            title="两数之和", content="给定数组和目标值，找两数之和。",
            q_type="算法", knowledge="双指针", answer="C",
            options={"A": "暴力", "B": "排序", "C": "哈希", "D": "DP"},
            check_dup=True,
        )
        with pytest.raises(ValueError, match="题目重复"):
            bank.add_manual(
                title="两数之和", content="给定数组和目标值，找两数之和。",
                q_type="算法", knowledge="双指针", answer="C",
                options={"A": "暴力", "B": "排序", "C": "哈希", "D": "DP"},
                check_dup=True,
            )

    def test_add_different_stem_allowed(self, tmp_path):
        """不同题干内容应允许添加。"""
        bank = QuestionBank(bank_dir=tmp_path)
        bank.add_manual(
            title="Q1", content="题目一的内容。",
            q_type="算法", knowledge="K", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )
        bank.add_manual(
            title="Q2", content="题目二完全不同。",
            q_type="算法", knowledge="K", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )
        assert bank.count() == 2

    def test_check_duplicate_no_match(self, tmp_path):
        bank = QuestionBank(bank_dir=tmp_path)
        assert bank.check_duplicate("全新题目内容") == []

    def test_check_duplicate_with_existing(self, tmp_path):
        bank = QuestionBank(bank_dir=tmp_path)
        bank.add_manual(
            title="T", content="已有题目。",
            q_type="算法", knowledge="K", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )
        reasons = bank.check_duplicate("已有题目。")
        assert len(reasons) == 1
        assert "重复" in reasons[0]

    def test_check_duplicate_empty_stem(self, tmp_path):
        bank = QuestionBank(bank_dir=tmp_path)
        assert bank.check_duplicate("") == []

    def test_stem_normalization(self, tmp_path):
        """不同空白/标点但核心内容相同的 stem 应匹配。"""
        bank = QuestionBank(bank_dir=tmp_path)
        bank.add_manual(
            title="T", content="给定一个数组，找出两数之和。",
            q_type="算法", knowledge="K", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )
        # 不同标点但内容相同
        reasons = bank.check_duplicate("给定一个数组 找出两数之和")
        assert len(reasons) == 1

    def test_short_stem_still_dedup(self, tmp_path):
        """短题干也能去重。"""
        bank = QuestionBank(bank_dir=tmp_path)
        bank.add_manual(
            title="T", content="什么是快排？",
            q_type="单选题", knowledge="排序", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )
        reasons = bank.check_duplicate("什么是快排？")
        assert len(reasons) == 1


# ── search ────────────────────────────────────────────────────

class TestSearch:
    def test_search_empty_bank(self, tmp_bank):
        assert tmp_bank.search("anything") == []

    def test_search_with_items(self, tmp_bank):
        tmp_bank.add_manual(
            title="两数之和", content="哈希表 O(n) 查找两数和",
            q_type="算法", knowledge="双指针", answer="C",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )
        results = tmp_bank.search("哈希表")
        assert len(results) >= 1
        assert results[0]["knowledge"] == "双指针"


# ── import_from_dir ───────────────────────────────────────────

class TestImportFromDir:
    def test_import_basic(self, tmp_path):
        bank = QuestionBank(bank_dir=tmp_path)
        src = tmp_path / "src"
        src.mkdir()

        q1 = "---\ntype: 算法\nknowledge: 二分查找\n---\n\n## 二分基础\n\n内容\n"
        q2 = "---\ntype: 单选题\nknowledge: 链表\n---\n\n## 链表反转\n\n内容\n"
        (src / "a.md").write_text(q1, encoding="utf-8")
        (src / "b.md").write_text(q2, encoding="utf-8")

        n = bank.import_from_dir(str(src))
        assert n == 2
        assert bank.count(q_type="算法") == 1
        assert bank.count(q_type="单选题") == 1

    def test_import_skips_existing(self, tmp_path):
        bank = QuestionBank(bank_dir=tmp_path)
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.md").write_text(
            "---\ntype: 算法\nknowledge: 二分查找\n---\n\n## Q\n\nC\n",
            encoding="utf-8",
        )

        bank.import_from_dir(str(src))
        n = bank.import_from_dir(str(src))
        assert n == 0  # already exists

    def test_import_skips_unknown_type(self, tmp_path):
        bank = QuestionBank(bank_dir=tmp_path)
        src = tmp_path / "src"
        src.mkdir()
        (src / "x.md").write_text(
            "---\ntype: 论述题\nknowledge: x\n---\n\n## Q\n\nC\n",
            encoding="utf-8",
        )
        n = bank.import_from_dir(str(src))
        assert n == 0

    def test_import_missing_dir(self, tmp_path):
        bank = QuestionBank(bank_dir=tmp_path)
        with pytest.raises(ValueError, match="目录不存在"):
            bank.import_from_dir(str(tmp_path / "nope"))


# ── add() dict 快捷方式 ────────────────────────────────────────

class TestAddDict:
    def test_add_from_dict(self, tmp_bank):
        fn = tmp_bank.add({
            "title": "DP 入门",
            "content": "动态规划描述",
            "type": "算法",
            "knowledge": "动态规划",
            "answer": "A",
            "options": {"A": "自顶向下", "B": "自底向上", "C": "贪心", "D": "回溯"},
            "explanation": "DP 是分治+记忆化",
        })
        assert fn.startswith("算法_动态规划_")
        assert tmp_bank.count() == 1
