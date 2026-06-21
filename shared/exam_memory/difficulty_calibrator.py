"""difficulty_calibrator.py — 基于答题历史的难度校准器。

维护 (knowledge, difficulty) -> {total, correct} 计数器。
新题目入池时，根据同知识点下的用户正确率动态调整难度标记。

零强制新依赖，纯统计校准。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DifficultyCalibrator:
    """基于答题历史的难度校准器。

    维护一个 ``(knowledge, difficulty) -> {total, correct}`` 计数器。
    新题目入池时，根据同知识点下的用户正确率动态调整难度标记。

    数据持久化到 JSON 文件（difficulty_stats.json）。
    """

    DIFFICULTY_OPTIONS = ("简单", "中等", "困难")
    THRESHOLDS: dict[str, float] = {
        "简单": 0.8,
        "中等": 0.5,
        "困难": 0.0,
    }

    def __init__(self, stats_path: str | Path | None = None) -> None:
        """初始化校准器。

        stats_path: 持久化 JSON 文件路径。None 表示不持久化。
        """
        self._stats_path: Path | None = Path(stats_path) if stats_path else None
        self._data: dict[str, dict[str, dict[str, int]]] = {}
        self.load()

    def record_result(self, knowledge: str, difficulty: str, correct: bool) -> None:
        """记录一次答题结果，更新计数。"""
        if knowledge not in self._data:
            self._data[knowledge] = {}
        if difficulty not in self._data[knowledge]:
            self._data[knowledge][difficulty] = {"total": 0, "correct": 0}
        entry = self._data[knowledge][difficulty]
        entry["total"] += 1
        if correct:
            entry["correct"] += 1
        logger.debug(
            "记录答题结果: knowledge=%s, difficulty=%s, correct=%s, total=%d",
            knowledge, difficulty, correct, entry["total"],
        )
        self.save()

    def calibrate(self, knowledge: str, suggested_difficulty: str) -> str:
        """根据历史数据校准难度。无历史数据时返回 ``suggested_difficulty``。"""
        if knowledge not in self._data:
            return suggested_difficulty

        # 聚合该 knowledge 下所有难度的 total/correct
        total = 0
        correct = 0
        for d_entry in self._data[knowledge].values():
            total += d_entry["total"]
            correct += d_entry["correct"]

        if total == 0:
            return suggested_difficulty

        rate = correct / total
        # 正确率 >= 阈值则保留该难度（从高到低匹配）
        if rate >= self.THRESHOLDS["简单"]:
            calibrated = "简单"
        elif rate >= self.THRESHOLDS["中等"]:
            calibrated = "中等"
        else:
            calibrated = "困难"

        logger.debug(
            "难度校准: knowledge=%s, rate=%.2f, suggested=%s, calibrated=%s",
            knowledge, rate, suggested_difficulty, calibrated,
        )
        return calibrated

    def load(self) -> None:
        """从 JSON 文件加载计数器。文件不存在时从空状态初始化。"""
        if not self._stats_path:
            return
        try:
            if self._stats_path.exists():
                raw = self._stats_path.read_text(encoding="utf-8")
                self._data = json.loads(raw)
                logger.debug(
                    "难度统计已加载: %d knowledge 条目", len(self._data),
                )
            else:
                self._data = {}
                logger.debug("难度统计文件不存在，使用空状态")
        except Exception as exc:
            logger.warning("加载难度统计失败（降级为空状态）: %s", exc)
            self._data = {}

    def save(self) -> None:
        """将计数器写入 JSON 文件。未配置路径时静默跳过。"""
        if not self._stats_path:
            return
        try:
            self._stats_path.parent.mkdir(parents=True, exist_ok=True)
            self._stats_path.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("保存难度统计失败: %s", exc)

    def get_stats(self, knowledge: str | None = None) -> dict[str, Any]:
        """获取统计信息。

        传入 knowledge 返回该知识点的详细数据；
        不传则返回全部数据。
        """
        if knowledge is not None:
            return self._data.get(knowledge, {})
        return self._data

    def clear(self) -> None:
        """清空所有计数（用于测试）。"""
        self._data = {}
        self.save()
