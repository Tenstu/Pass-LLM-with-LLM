"""tests/test_semantic_dedup.py — 语义去重测试。

覆盖: check_semantic_duplicate / check_duplicate(use_semantic=True) /
       add_manual(check_dup=True) 语义重复拦截 / 不可用时降级
运行: pytest tests/test_semantic_dedup.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure shared/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from exam_memory.question_bank import QuestionBank


# ── Helpers ──────────────────────────────────────────────────

def _vec(vals: list[float]) -> np.ndarray:
    """构造 L2 归一化向量。"""
    a = np.array(vals, dtype=np.float32)
    n = float(np.linalg.norm(a))
    return a / n if n > 0 else a


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def tmp_bank(tmp_path):
    return QuestionBank(bank_dir=tmp_path)


# ── check_semantic_duplicate ──────────────────────────────────

class TestCheckSemanticDuplicate:
    """直接测试 check_semantic_duplicate 方法。"""

    def test_unavailable_returns_empty(self, tmp_bank, monkeypatch):
        """embedding 不可用时返回空列表。"""
        monkeypatch.setattr(tmp_bank, "_semantic_available", False)
        monkeypatch.setattr(tmp_bank, "_ensure_semantic_ready", lambda: False)
        result = tmp_bank.check_semantic_duplicate("任意文本")
        assert result == []

    def test_empty_bank_returns_empty(self, tmp_bank, monkeypatch):
        """空题库应返回空列表（无内容可匹配）。"""
        monkeypatch.setattr(tmp_bank, "_semantic_available", True)
        monkeypatch.setattr(
            tmp_bank, "_semantic_index",
            np.empty((0, 0), dtype=np.float32),
        )
        monkeypatch.setattr(tmp_bank, "_semantic_ids", [])
        result = tmp_bank.check_semantic_duplicate("任意文本")
        assert result == []

    def test_above_threshold_match(self, tmp_bank, monkeypatch):
        """相似度 >= 阈值应返回对应 question_id（相同向量 cosine=1.0）。"""
        v = _vec([1.0, 0.5, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0])

        monkeypatch.setattr(tmp_bank, "_semantic_available", True)
        monkeypatch.setattr(
            tmp_bank, "_semantic_index",
            np.vstack([v.reshape(1, -1)]).astype(np.float32),
        )
        monkeypatch.setattr(tmp_bank, "_semantic_ids", ["Q_001"])
        # 相同的向量 -> cosine = 1.0
        monkeypatch.setattr(
            "exam_memory.embedding.encode_safe",
            lambda text, **kw: v.copy(),
        )

        hits = tmp_bank.check_semantic_duplicate("相同内容的stem", threshold=0.9)
        assert "Q_001" in hits

    def test_below_threshold_no_match(self, tmp_bank, monkeypatch):
        """相似度 < 阈值应返回空列表。"""
        # 索引中存向量 [1, 0, 0, ...]，查询返回正交向量 [0, 1, 0, ...] -> cosine = 0
        v_idx = _vec([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        v_query = _vec([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        monkeypatch.setattr(tmp_bank, "_semantic_available", True)
        monkeypatch.setattr(
            tmp_bank, "_semantic_index",
            np.vstack([v_idx.reshape(1, -1)]).astype(np.float32),
        )
        monkeypatch.setattr(tmp_bank, "_semantic_ids", ["Q_001"])
        monkeypatch.setattr(
            "exam_memory.embedding.encode_safe",
            lambda text, **kw: v_query.copy(),
        )

        hits = tmp_bank.check_semantic_duplicate("完全不同的话题", threshold=0.9)
        assert hits == []

    def test_encode_failure_returns_empty(self, tmp_bank, monkeypatch):
        """encode_safe 返回 None 时应降级为空列表。"""
        monkeypatch.setattr(tmp_bank, "_semantic_available", True)
        monkeypatch.setattr(
            tmp_bank, "_semantic_index",
            np.empty((0, 0), dtype=np.float32),
        )
        monkeypatch.setattr(tmp_bank, "_semantic_ids", [])
        monkeypatch.setattr(
            "exam_memory.embedding.encode_safe",
            lambda text, **kw: None,
        )
        result = tmp_bank.check_semantic_duplicate("任意文本")
        assert result == []


# ── check_duplicate(use_semantic=True) ────────────────────────

class TestCheckDuplicateSemantic:
    """测试 check_duplicate 的 use_semantic 参数。"""

    def test_use_semantic_false_default(self, tmp_bank):
        """默认 use_semantic=False，行为不变。"""
        tmp_bank.add_manual(
            title="T", content="已有题目。",
            q_type="算法", knowledge="K", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )
        reasons = tmp_bank.check_duplicate("已有题目。", use_semantic=False)
        assert len(reasons) == 1
        assert "前缀重复" in reasons[0]

    def test_use_semantic_true_with_match(self, tmp_bank, monkeypatch):
        """use_semantic=True 且命中时应包含语义匹配。"""
        tmp_bank.add_manual(
            title="T", content="已有题目内容。",
            q_type="算法", knowledge="K", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )
        v = _vec([1.0, 0.5, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0])

        monkeypatch.setattr(tmp_bank, "_semantic_available", True)
        monkeypatch.setattr(
            tmp_bank, "_semantic_index",
            np.vstack([v.reshape(1, -1)]).astype(np.float32),
        )
        monkeypatch.setattr(tmp_bank, "_semantic_ids", ["算法_K_001_xxxxxx"])
        monkeypatch.setattr(
            "exam_memory.embedding.encode_safe",
            lambda text, **kw: v.copy(),
        )

        reasons = tmp_bank.check_duplicate("已有题目内容", use_semantic=True)
        assert any("语义相似" in r for r in reasons)

    def test_use_semantic_true_no_match(self, tmp_bank, monkeypatch):
        """use_semantic=True 但语义不匹配时，无语义原因。"""
        tmp_bank.add_manual(
            title="T", content="已有题目。",
            q_type="算法", knowledge="K", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )
        v_idx = _vec([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        v_query = _vec([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        monkeypatch.setattr(tmp_bank, "_semantic_available", True)
        monkeypatch.setattr(
            tmp_bank, "_semantic_index",
            np.vstack([v_idx.reshape(1, -1)]).astype(np.float32),
        )
        monkeypatch.setattr(tmp_bank, "_semantic_ids", ["算法_K_001_xxxxxx"])
        monkeypatch.setattr(
            "exam_memory.embedding.encode_safe",
            lambda text, **kw: v_query.copy(),
        )

        reasons = tmp_bank.check_duplicate("完全不同的话题", use_semantic=True)
        assert not any("语义相似" in r for r in reasons)

    def test_use_semantic_true_unavailable_graceful(self, tmp_bank, monkeypatch):
        """use_semantic=True 但不可用时静默降级，不抛异常。"""
        tmp_bank.add_manual(
            title="T", content="已有题目。",
            q_type="算法", knowledge="K", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )
        monkeypatch.setattr(tmp_bank, "_semantic_available", False)
        monkeypatch.setattr(tmp_bank, "_ensure_semantic_ready", lambda: False)
        reasons = tmp_bank.check_duplicate("已有题目。", use_semantic=True)
        assert isinstance(reasons, list)


# ── add_manual / add 集成 ──────────────────────────────────────

class TestSemanticDedupIntegration:
    """集成测试：语义重复在 add_manual(add) 中被拦截。"""

    def test_add_raises_on_semantic_duplicate(self, tmp_bank, monkeypatch):
        """语义重复时 add_manual(check_dup=True) 应抛 ValueError。"""
        tmp_bank.add_manual(
            title="T1", content="这是第一道题目的内容。",
            q_type="算法", knowledge="K", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )

        v = _vec([1.0, 0.5, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0])
        monkeypatch.setattr(tmp_bank, "_semantic_available", True)
        monkeypatch.setattr(
            tmp_bank, "_semantic_index",
            np.vstack([v.reshape(1, -1)]).astype(np.float32),
        )
        monkeypatch.setattr(tmp_bank, "_semantic_ids", ["算法_K_001_xxxxxx"])
        monkeypatch.setattr(
            "exam_memory.embedding.encode_safe",
            lambda text, **kw: v.copy(),
        )

        with pytest.raises(ValueError, match="题目重复"):
            tmp_bank.add_manual(
                title="T2", content="这是第一道题目的内容。",
                q_type="算法", knowledge="K", answer="A",
                options={"A": "1", "B": "2", "C": "3", "D": "4"},
                check_dup=True,
            )

    def test_add_allows_non_duplicate(self, tmp_bank, monkeypatch):
        """语义不匹配时允许添加。"""
        tmp_bank.add_manual(
            title="T1", content="第一道题。",
            q_type="算法", knowledge="K", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
        )

        v_idx = _vec([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        v_new = _vec([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        monkeypatch.setattr(tmp_bank, "_semantic_available", True)
        monkeypatch.setattr(
            tmp_bank, "_semantic_index",
            np.vstack([v_idx.reshape(1, -1)]).astype(np.float32),
        )
        monkeypatch.setattr(tmp_bank, "_semantic_ids", ["算法_K_001_xxxxxx"])
        monkeypatch.setattr(
            "exam_memory.embedding.encode_safe",
            lambda text, **kw: v_new.copy() if "第二道" in text else v_idx.copy(),
        )

        fn = tmp_bank.add_manual(
            title="T2", content="第二道完全不同的题。",
            q_type="算法", knowledge="K", answer="B",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
            check_dup=True,
        )
        assert fn is not None
        assert tmp_bank.count() == 2

    def test_add_increments_semantic_index(self, tmp_bank, monkeypatch):
        """成功添加后，语义索引应增加。"""
        v = _vec([1.0, 0.5, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0])
        monkeypatch.setattr(tmp_bank, "_semantic_available", True)
        monkeypatch.setattr(
            tmp_bank, "_semantic_index",
            np.empty((0, 8), dtype=np.float32),
        )
        monkeypatch.setattr(tmp_bank, "_semantic_ids", [])

        encode_calls: list = []
        def fake_encode(text, **kw):
            encode_calls.append(text)
            return v.copy()

        monkeypatch.setattr("exam_memory.embedding.encode_safe", fake_encode)

        tmp_bank.add_manual(
            title="T1", content="第一题。",
            q_type="算法", knowledge="K", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
            check_dup=False,
        )
        assert len(encode_calls) == 1, f"Expected 1 encode call, got {len(encode_calls)}"
        assert len(tmp_bank._semantic_ids) == 1, f"Expected 1 id, got {len(tmp_bank._semantic_ids)}"
        assert tmp_bank._semantic_index is not None
        assert tmp_bank._semantic_index.shape[0] == 1

    def test_semantic_unavailable_does_not_crash_add(self, tmp_bank, monkeypatch):
        """embedding 不可用时，add_manual 正常工作。"""
        monkeypatch.setattr(tmp_bank, "_semantic_available", False)
        monkeypatch.setattr(tmp_bank, "_ensure_semantic_ready", lambda: False)
        fn = tmp_bank.add_manual(
            title="T", content="内容",
            q_type="算法", knowledge="K", answer="A",
            options={"A": "1", "B": "2", "C": "3", "D": "4"},
            check_dup=True,
        )
        assert fn is not None
        assert tmp_bank.count() == 1
