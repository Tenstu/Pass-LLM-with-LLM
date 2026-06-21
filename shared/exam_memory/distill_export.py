"""distill_export.py — 蒸馏数据导出模块。

从 bank/*.distill.jsonl 加载 logprobs 样本，导出为训练就绪格式。
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import math
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ── 数据模型 ────────────────────────────────────────────────────

@dataclass
class DistillationSample:
    question_id: str
    stem: str
    options: dict[str, str] = field(default_factory=dict)
    answer: str = ""
    logprobs: list[dict[str, Any]] = field(default_factory=list)
    model: str | None = None
    captured_at: str | None = None

    def to_training_dict(self) -> dict[str, Any]:
        """导出为训练格式 dict，含软标签（正确答案 token 概率）。"""
        return {
            "question_id": self.question_id,
            "stem": self.stem,
            "options": self.options,
            "answer": self.answer,
            "answer_probability": self._estimate_answer_probability(),
            "logprobs": self.logprobs,
            "model": self.model,
            "captured_at": self.captured_at,
        }

    def _estimate_answer_probability(self) -> float | None:
        """将正确答案 token 的 logprob 转为概率（math.exp）。"""
        if not self.logprobs or not self.answer:
            return None
        answer_letter = self.answer.strip().upper()
        option_text = self.options.get(answer_letter, "")
        if not option_text:
            return None
        tokens = [t.get("token", "") for t in self.logprobs]
        # 查找选项文本中第一个 token 的 logprob
        for t in self.logprobs:
            if t.get("token") and option_text.startswith(t.get("token", "")):
                lp = t.get("logprob")
                if lp is not None:
                    return math.exp(lp)
        # 回退：查找第一个含答案字母的 token
        for i, tok in enumerate(tokens):
            if answer_letter in tok and i < len(self.logprobs):
                lp = self.logprobs[i].get("logprob")
                if lp is not None:
                    return math.exp(lp)
        return None

    @property
    def sidecar_bytes(self) -> int:
        return len(json.dumps(self.logprobs, ensure_ascii=False).encode("utf-8"))


# ── 加载 / 导出 ────────────────────────────────────────────────

def load_from_bank(bank_dir: str | Path) -> list[DistillationSample]:
    """扫描 bank/*.distill.jsonl，逐行加载为 DistillationSample 列表。"""
    bank_dir = Path(bank_dir)
    if not bank_dir.is_dir():
        return []
    samples: list[DistillationSample] = []
    for fp in sorted(glob.glob(str(bank_dir / "*.distill.jsonl"))):
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    samples.append(DistillationSample(**{
                        k: v for k, v in data.items()
                        if k in DistillationSample.__dataclass_fields__
                    }))
                except (json.JSONDecodeError, TypeError) as exc:
                    logger.warning("跳过无效蒸馏记录 %s: %s", fp, exc)
    return samples


def export_jsonl(samples: list[DistillationSample], path: str | Path) -> int:
    """导出 JSONL。返回写入行数。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(path, "w", encoding="utf-8") as fh:
        for s in samples:
            fh.write(json.dumps(s.to_training_dict(), ensure_ascii=False) + "\n")
            count += 1
    return count


def export_json(samples: list[DistillationSample], path: str | Path) -> int:
    """导出 JSON 数组。返回写入样本数。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [s.to_training_dict() for s in samples]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    return len(data)


def export_summary(samples: list[DistillationSample]) -> str:
    """打印数据集统计摘要，返回摘要字符串。"""
    if not samples:
        return "无蒸馏样本。"
    total_lps = sum(len(s.logprobs) for s in samples)
    probs = [s._estimate_answer_probability() for s in samples if s._estimate_answer_probability() is not None]
    total_bytes = sum(s.sidecar_bytes for s in samples)
    avg_prob = sum(probs) / len(probs) if probs else 0.0
    lines = [
        f"蒸馏样本数: {len(samples)}",
        f"总 logprob 条目: {total_lps}",
        f"平均答案概率: {avg_prob:.4f}",
        f"概率可计算样本: {len(probs)}/{len(samples)}",
        f"侧信道总字节: {total_bytes}",
    ]
    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────

import logging

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="蒸馏数据导出工具")
    parser.add_argument("--bank-dir", default="bank/", help="bank 目录路径（默认 bank/）")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument(
        "--format", choices=["jsonl", "json"], default="jsonl",
        help="输出格式（默认 jsonl）",
    )
    parser.add_argument("--summary", action="store_true", help="打印统计摘要")
    args = parser.parse_args()

    samples = load_from_bank(args.bank_dir)
    if not samples:
        print("无蒸馏样本。")
        return

    if args.output:
        if args.format == "jsonl":
            n = export_jsonl(samples, args.output)
            print(f"已导出 {n} 条到 {args.output}")
        else:
            n = export_json(samples, args.output)
            print(f"已导出 {n} 条到 {args.output}")

    if args.summary:
        print(export_summary(samples))


if __name__ == "__main__":
    main()
