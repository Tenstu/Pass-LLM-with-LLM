"""tests/test_distill_export.py — 蒸馏导出模块测试。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from exam_memory.distill_export import (
    DistillationSample,
    export_json,
    export_jsonl,
    export_summary,
    load_from_bank,
)


def _sample(**overrides):
    """构造测试用 DistillationSample。"""
    data = {
        "question_id": "算法_双指针_001_a7f3e2",
        "stem": "给定数组，找出两数之和。",
        "options": {"A": "暴力", "B": "排序", "C": "哈希", "D": "DP"},
        "answer": "C",
        "logprobs": [
            {"token": "\n", "logprob": -0.1},
            {"token": "哈希", "logprob": -0.8},
        ],
        "model": "deepseek/deepseek-chat",
        "captured_at": "2026-06-20T10:00:00+00:00",
    }
    data.update(overrides)
    return DistillationSample(**data)


class TestLoadFromBank:
    def test_load_from_bank(self, tmp_path):
        sidecar = tmp_path / "算法_双指针_001_a7f3e2.distill.jsonl"
        record = {
            "question_id": "算法_双指针_001_a7f3e2",
            "stem": "题干",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "answer": "B",
            "logprobs": [{"token": "B", "logprob": -0.5}],
            "model": "test/model",
            "captured_at": "2026-06-20T10:00:00+00:00",
        }
        sidecar.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

        samples = load_from_bank(tmp_path)
        assert len(samples) == 1
        assert samples[0].question_id == "算法_双指针_001_a7f3e2"
        assert samples[0].answer == "B"
        assert len(samples[0].logprobs) == 1

    def test_load_multiple(self, tmp_path):
        for i in range(3):
            sidecar = tmp_path / f"q_{i:03d}.distill.jsonl"
            sidecar.write_text(
                json.dumps({"question_id": f"q_{i}", "stem": f"s{i}",
                            "options": {}, "answer": "",
                            "logprobs": [], "model": None, "captured_at": None},
                           ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        samples = load_from_bank(tmp_path)
        assert len(samples) == 3

    def test_load_skips_invalid(self, tmp_path, caplog):
        (tmp_path / "bad.distill.jsonl").write_text("not json\n", encoding="utf-8")
        samples = load_from_bank(tmp_path)
        assert samples == []

    def test_load_empty_dir(self, tmp_path):
        assert load_from_bank(tmp_path) == []

    def test_load_nonexistent_dir(self):
        assert load_from_bank("/nonexistent/path/12345") == []


class TestExportJsonl:
    def test_export_jsonl(self, tmp_path):
        samples = [_sample()]
        out = tmp_path / "out.jsonl"
        n = export_jsonl(samples, out)
        assert n == 1
        assert out.exists()
        lines = out.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["question_id"] == "算法_双指针_001_a7f3e2"
        assert "answer_probability" in record

    def test_export_jsonl_multiple(self, tmp_path):
        samples = [_sample(), _sample(question_id="q2")]
        out = tmp_path / "out.jsonl"
        n = export_jsonl(samples, out)
        assert n == 2
        lines = out.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2


class TestExportJson:
    def test_export_json(self, tmp_path):
        samples = [_sample()]
        out = tmp_path / "out.json"
        n = export_json(samples, out)
        assert n == 1
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["question_id"] == "算法_双指针_001_a7f3e2"

    def test_export_json_array(self, tmp_path):
        samples = [_sample(), _sample(question_id="q2")]
        out = tmp_path / "out.json"
        export_json(samples, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 2


class TestExportSummary:
    def test_summary_content(self):
        samples = [_sample(), _sample(question_id="q2")]
        summary = export_summary(samples)
        assert "蒸馏样本数: 2" in summary
        assert "总 logprob 条目" in summary
        assert "平均答案概率" in summary
        assert "侧信道总字节" in summary

    def test_summary_empty(self):
        assert export_summary([]) == "无蒸馏样本。"

    def test_summary_with_probabilities(self):
        """包含可计算概率的样本应出现在统计中。"""
        s = _sample(
            logprobs=[{"token": "C", "logprob": -0.1}],
            answer="C",
            options={"C": "哈希表 O(n)"},
        )
        summary = export_summary([s])
        assert "概率可计算样本: 1/1" in summary


class TestDistillationSample:
    def test_estimate_answer_probability_found(self):
        """答案 token 在 logprobs 中匹配时返回概率。"""
        s = _sample(
            logprobs=[{"token": "C", "logprob": -0.6931}],
            answer="C",
            options={"C": "哈希表"},
        )
        prob = s._estimate_answer_probability()
        assert prob is not None
        assert abs(prob - 0.5) < 0.01  # exp(-0.6931) ≈ 0.5

    def test_estimate_answer_probability_not_found(self):
        """logprobs 为空时返回 None。"""
        s = _sample(logprobs=[])
        assert s._estimate_answer_probability() is None

    def test_estimate_answer_probability_no_answer(self):
        """answer 为空时返回 None。"""
        s = _sample(answer="", logprobs=[])
        assert s._estimate_answer_probability() is None

    def test_to_training_dict(self):
        s = _sample()
        d = s.to_training_dict()
        assert d["question_id"] == s.question_id
        assert "answer_probability" in d
        assert d["answer_probability"] is not None

    def test_sidecar_bytes(self):
        s = _sample(
            logprobs=[{"token": "A", "logprob": -0.5, "bytes": [65]}] * 10,
        )
        # sidecar_bytes 应反映 logprobs 的 JSON 序列化大小
        assert s.sidecar_bytes > 0
