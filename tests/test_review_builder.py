"""Tests for review_builder.py — build review items from harness data."""

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from exam_memory.review_builder import (
    build_review_items_from_mistakes,
    build_review_items_from_topic_checklist,
    build_review_items_from_choice_rounds,
    dedupe_review_items,
)


# ── Fixtures ──────────────────────────────────────────────

MISTAKE_LOG = """\
# Mistake Log

| Date | Problem | Topic | Root Cause | Fix |
|------|---------|-------|-----------|-----|
| 2026-06-15 | P001 | sliding-window | boundary | ... |
| 2026-06-15 | P002 | binary-search | off-by-one | ... |
| 2026-06-16 | P003 | sliding-window | boundary | ... |
| 2026-06-16 | P004 | greedy | pattern | ... |
"""

TOPIC_CHECKLIST = """\
# Algorithm Topic Checklist

## P0 Must Practice First

| Topic | Why It Matters | AC Standard |
|-------|---------------|-------------|
| Hash / dict / set | 高频统计 | 20 分钟内写出 |
| Binary Search | 边界常见 | 能写 lower_bound |
| Sliding Window | 高频 | 左右指针清楚 |

## P1 Need Solid Coverage

| Topic | Why It Matters |
|-------|---------------|
| Greedy | 中等题常见 |
| BFS / DFS | 图、树 |
"""

CHOICE_ROUND = """\
# 选择题模拟 — Round 1

| Q# | Topic | Result | Error |
|----|-------|--------|-------|
| 1 | transformer | correct | |
| 2 | probability | wrong | bayes |
| 3 | transformer | wrong | attention |
| 4 | linear-algebra | correct | |
"""


# ── Mistake builder ──────────────────────────────────────


class TestBuildFromMistakes:
    def test_parses_markdown_table(self):
        items = build_review_items_from_mistakes(MISTAKE_LOG)
        # sliding-window+boundary appears twice but gets deduped
        assert len(items) == 3

    def test_item_has_correct_fields(self):
        items = build_review_items_from_mistakes(MISTAKE_LOG)
        item = items[0]
        assert item.topic == "sliding-window"
        assert item.root_cause == "boundary"
        assert item.priority == "P0"
        assert item.source_type == "mistake"

    def test_groups_by_topic(self):
        items = build_review_items_from_mistakes(MISTAKE_LOG)
        topics = {i.topic for i in items}
        assert "sliding-window" in topics
        assert "binary-search" in topics
        assert "greedy" in topics

    def test_empty_log_returns_empty(self):
        assert build_review_items_from_mistakes("") == []

    def test_no_table_returns_empty(self):
        assert build_review_items_from_mistakes("# Just a header") == []


# ── Topic checklist builder ──────────────────────────────


class TestBuildFromTopicChecklist:
    def test_parses_p0_topics(self):
        items = build_review_items_from_topic_checklist(TOPIC_CHECKLIST)
        p0_items = [i for i in items if i.priority == "P0"]
        assert len(p0_items) == 3

    def test_parses_p1_topics(self):
        items = build_review_items_from_topic_checklist(TOPIC_CHECKLIST)
        p1_items = [i for i in items if i.priority == "P1"]
        assert len(p1_items) == 2

    def test_item_has_source_type(self):
        items = build_review_items_from_topic_checklist(TOPIC_CHECKLIST)
        assert all(i.source_type == "topic_coverage" for i in items)

    def test_empty_text_returns_empty(self):
        assert build_review_items_from_topic_checklist("") == []

    def test_no_priority_sections_returns_empty(self):
        assert build_review_items_from_topic_checklist("Nothing here") == []


# ── Choice rounds builder ────────────────────────────────


class TestBuildFromChoiceRounds:
    def test_parses_wrong_answers(self):
        items = build_review_items_from_choice_rounds(CHOICE_ROUND)
        assert len(items) == 2

    def test_ignores_correct_answers(self):
        items = build_review_items_from_choice_rounds(CHOICE_ROUND)
        topics = {i.topic for i in items}
        assert "transformer" in topics
        assert "linear-algebra" not in topics

    def test_item_fields(self):
        items = build_review_items_from_choice_rounds(CHOICE_ROUND)
        for item in items:
            assert item.source_type == "choice_question"
            assert item.priority == "P1"

    def test_empty_text_returns_empty(self):
        assert build_review_items_from_choice_rounds("") == []


# ── Dedup ────────────────────────────────────────────────


class TestDedupe:
    def test_dedupes_same_topic_and_root_cause(self):
        from exam_memory.review_schedule import ReviewItem
        items = [
            ReviewItem(review_id="A1", topic="sliding-window", root_cause="boundary"),
            ReviewItem(review_id="A2", topic="sliding-window", root_cause="boundary"),
            ReviewItem(review_id="A3", topic="binary-search", root_cause="boundary"),
        ]
        deduped = dedupe_review_items(items)
        assert len(deduped) == 2

    def test_preserves_first_item(self):
        from exam_memory.review_schedule import ReviewItem
        items = [
            ReviewItem(review_id="A1", topic="sliding-window", root_cause="boundary"),
            ReviewItem(review_id="A2", topic="sliding-window", root_cause="boundary"),
        ]
        deduped = dedupe_review_items(items)
        assert deduped[0].review_id == "A1"

    def test_different_topics_kept_separate(self):
        from exam_memory.review_schedule import ReviewItem
        items = [
            ReviewItem(review_id="A1", topic="sliding-window", root_cause="boundary"),
            ReviewItem(review_id="A2", topic="greedy", root_cause="pattern"),
        ]
        deduped = dedupe_review_items(items)
        assert len(deduped) == 2


class TestReviewIdGeneration:
    def test_take_id_unique_under_concurrent_calls(self, monkeypatch):
        import exam_memory.review_builder as rb

        rb._reset_seq(1)
        original_next_id = rb._next_id

        def slow_next_id(today=None):
            rid = original_next_id(today)
            time.sleep(0.001)
            return rid

        monkeypatch.setattr(rb, "_next_id", slow_next_id)
        worker_count = 24
        review_date = date(2026, 6, 21)

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            ids = list(executor.map(lambda _: rb._take_id(review_date), range(worker_count)))

        assert len(ids) == worker_count
        assert len(set(ids)) == worker_count
        seqs = sorted(int(review_id.rsplit("-", 1)[1]) for review_id in ids)
        assert seqs == list(range(1, worker_count + 1))
