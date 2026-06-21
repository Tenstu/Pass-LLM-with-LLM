"""review_builder.py — Build review queue items from existing harness data.

Sources:
  - targets/{target}/mistake_log.md
  - targets/{target}/topic_checklist.md
  - targets/{target}/progress/choice-questions/round*.md
"""

from __future__ import annotations

import re
import threading
from datetime import date, datetime
from typing import Sequence

from exam_memory.review_schedule import ReviewItem


def _next_id(today: date | None = None) -> str:
    """Generate the next review ID in format RQ-YYYYMMDD-NNN."""
    today = today or date.today()
    return f"RQ-{today.strftime('%Y%m%d')}-{_SEQ[0]:03d}"


_SEQ = [1]
_SEQ_LOCK = threading.Lock()


def _reset_seq(n: int = 1) -> None:
    with _SEQ_LOCK:
        _SEQ[0] = n


def _take_id(today: date | None = None) -> str:
    with _SEQ_LOCK:
        rid = _next_id(today)
        _SEQ[0] += 1
        return rid


# ── Mistake log parser ──────────────────────────────────


_MISTAKE_TABLE_RE = re.compile(
    r"^\|\s*(?P<date>\d{4}-\d{2}-\d{2}|\d{6})\s*\|\s*(?P<problem>\S+)\s*\|\s*(?P<topic>\S[\w\-/]+)\s*\|\s*(?P<root_cause>\S[\w\-/ ]+?)\s*\|",
    re.MULTILINE,
)


def build_review_items_from_mistakes(text: str, today: date | None = None) -> list[ReviewItem]:
    """Parse mistake_log.md table rows into ReviewItems.

    Each unique (topic, root_cause) pair produces one review item.
    All mistake items get P0 priority.
    """
    review_date = today or date.today()
    items: list[ReviewItem] = []
    seen: set[tuple[str, str]] = set()
    # Group by (topic, root_cause)
    for m in _MISTAKE_TABLE_RE.finditer(text):
        topic_raw = m.group("topic").strip()
        root_cause_raw = m.group("root_cause").strip()
        # Skip header and separator rows
        if topic_raw.lower() in ("topic", "---") or root_cause_raw.lower() in ("root cause", "---"):
            continue
        topic = topic_raw.lower().replace(" ", "-")
        root_cause = root_cause_raw.lower().replace(" ", "-")
        key = (topic, root_cause)
        if key in seen:
            continue
        seen.add(key)
        items.append(
            ReviewItem(
                review_id=_take_id(review_date),
                source_type="mistake",
                topic=topic,
                root_cause=root_cause,
                priority="P0",
                created_at=review_date,
                next_review_at=review_date,
                prompt=f"Review {topic} (previous mistake: {root_cause}). Practice related problems.",
                success_rule=f"Solve 2 problems on {topic} correctly.",
            )
        )
    return items


# ── Topic checklist parser ──────────────────────────────


_TOPIC_SECTION_RE = re.compile(r"^##\s+(?P<priority>P[0-9]).*$", re.MULTILINE)
_TOPIC_ROW_RE = re.compile(r"^\|\s*(?P<topic>\S[\w\-/\s,]+?)\s*\|", re.MULTILINE)


def build_review_items_from_topic_checklist(text: str, today: date | None = None) -> list[ReviewItem]:
    """Parse topic_checklist.md priority sections into ReviewItems."""
    review_date = today or date.today()
    items: list[ReviewItem] = []
    seen_topics: set[str] = set()
    lines = text.split("\n")
    current_priority = "P2"
    for line in lines:
        sm = _TOPIC_SECTION_RE.search(line)
        if sm:
            current_priority = sm.group("priority")
            continue
        rm = _TOPIC_ROW_RE.search(line)
        if rm:
            topic = rm.group("topic").strip().lower().replace(" ", "-")
            topic = re.sub(r"\s+", "-", topic)
            # Skip header/separator rows
            if topic in ("topic", "---", "") or topic.startswith("---"):
                continue
            if topic in seen_topics:
                continue
            seen_topics.add(topic)
            items.append(
                ReviewItem(
                    review_id=_take_id(review_date),
                    source_type="topic_coverage",
                    topic=topic,
                    priority=current_priority,
                    created_at=review_date,
                    next_review_at=review_date,
                    prompt=f"Practice {topic} problems to ensure solid coverage.",
                    success_rule=f"AC 2 {topic} problems at medium difficulty.",
                )
            )
    return items


# ── Choice rounds parser ────────────────────────────────


_CHOICE_ROW_RE = re.compile(
    r"^\|\s*(?P<qnum>\d+)\s*\|\s*(?P<topic>\S[\w\-/]+)\s*\|\s*(?P<result>correct|wrong|partial)\s*\|(?:\s*(?P<error>\S[\w\-/ ]+?))?\s*\|",
    re.MULTILINE,
)


def build_review_items_from_choice_rounds(text: str, today: date | None = None) -> list[ReviewItem]:
    """Parse choice-question round files into ReviewItems for wrong answers.

    Repeated wrong answers on the same topic increase priority.
    """
    review_date = today or date.today()
    items: list[ReviewItem] = []
    topic_counts: dict[str, int] = {}
    for m in _CHOICE_ROW_RE.finditer(text):
        result = m.group("result").strip().lower()
        if result == "correct":
            continue
        topic = m.group("topic").strip().lower().replace(" ", "-")
        error = (m.group("error") or "unknown").strip().lower().replace(" ", "-")
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    for topic, count in topic_counts.items():
        priority = "P0" if count >= 2 else "P1"
        items.append(
            ReviewItem(
                review_id=_take_id(review_date),
                source_type="choice_question",
                topic=topic,
                priority=priority,
                created_at=review_date,
                next_review_at=review_date,
                prompt=f"Review {topic} choice questions ({count} previous errors).",
                success_rule="Answer 3 related choice questions correctly.",
            )
        )
    return items


# ── Dedup ───────────────────────────────────────────────


def dedupe_review_items(items: Sequence[ReviewItem]) -> list[ReviewItem]:
    """Deduplicate review items by (topic, root_cause)."""
    seen: set[tuple[str, str]] = set()
    result: list[ReviewItem] = []
    for item in items:
        key = (item.topic, item.root_cause)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
