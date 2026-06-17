"""question_bank.py — 题库 CRUD + LLM 生成管道（Phase 2.1）。

对齐 exam-memory V2 设计：
  - 文件格式：YAML frontmatter + Markdown body（与 experiences/ 平行）
  - 检索层：复用 hybrid_search，不独立建索引
  - 零强制依赖：LLM 生成可选（litellm），骨架可用无依赖

用法:
    from exam_memory.question_bank import QuestionBank
    bank = QuestionBank()
    bank.add_manual(type="算法", knowledge="双指针", title="两数之和",
                    content="...", answer="C", options={...}, explanation="...")
    results = bank.generate(topic="双指针", count=3, q_type="算法")
"""

from __future__ import annotations

import glob
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any

import yaml

from exam_memory.frontmatter import parse_frontmatter as _parse_frontmatter
from exam_memory.frontmatter import body_text as _body

logger = logging.getLogger(__name__)

# ── 路径常量 ──────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
BANK_DIR = BASE_DIR / "bank"

# ── 题型映射 ──────────────────────────────────────────────────

TYPE_PREFIX: dict[str, str] = {
    "单选题": "单选题",
    "多选题": "多选题",
    "算法": "算法",
}

DIFFICULTY_OPTIONS = ("简单", "中等", "困难")

# ── 提取模式 ──────────────────────────────────────────────────

MODE_RAG = "rag"        # 从 hybrid_search 检索 chunks 作为上下文
MODE_TEXT = "text"      # 直接使用提供的文本内容作为上下文
MODE_DIRECT = "direct"  # 无上下文，纯知识出题


# ── 文件工具 ──────────────────────────────────────────────────


def _validate_id(question_id: str, base_dir: Path) -> Path:
    """验证 question_id 不含路径穿越。返回安全的 resolved Path。"""
    target = (base_dir / f"{question_id}.md").resolve()
    if not target.is_relative_to(base_dir.resolve()):
        raise ValueError(f"非法 question_id（路径穿越）: {question_id}")
    return target


def _next_seq(prefix: str, bank_dir: Path = BANK_DIR) -> int:
    """扫描 bank/ 目录，返回下一个自增序号。"""
    pattern = str(bank_dir / f"{prefix}_*.md")
    existing = glob.glob(pattern)
    max_n = 0
    for fp in existing:
        m = re.search(r"_(\d{3})(?:_[0-9a-f]{6})?\.md$", fp)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def _build_filename(q_type: str, knowledge: str, bank_dir: Path = BANK_DIR, seq: int | None = None) -> str:
    """构造标准文件名：{type}_{knowledge}_{seq:03d}_{uuid6}.md"""
    prefix = TYPE_PREFIX.get(q_type, q_type)
    if seq is None:
        seq = _next_seq(prefix, bank_dir=bank_dir)
    safe_knowledge = re.sub(r'[^\w一-鿿-]', '_', knowledge).strip("_")
    short_id = uuid.uuid4().hex[:6]
    return f"{prefix}_{safe_knowledge}_{seq:03d}_{short_id}.md"


# ── LLM 生成管道 ──────────────────────────────────────────────

class PromptBuilder:
    """构造题库生成 prompt（system + user context + format spec）。"""

    SYSTEM_TEMPLATE = """\
你是算法面试题库出题专家。根据提供的参考资料，生成高质量的考试题目。

要求：
1. 题干清晰，无歧义，答案唯一确定
2. 选项设计有区分度（常见错误选项应反映典型误区）
3. 解析详细，包含解题思路、关键步骤和复杂度分析
4. 严格遵循输出格式"""

    FORMAT_TEMPLATE = """\
对每道题，按以下格式输出（每道题用 --- 分隔）：

---
## 题干
题目描述

### 选项
**A.** 选项A
**B.** 选项B
**C.** 选项C
**D.** 选项D

### 答案
C

### 解析
详细解析
---

数量：{count} 道
题型：{q_type}
知识点：{topic}"""

    def build(
        self,
        chunks: list[dict],
        topic: str,
        q_type: str,
        count: int,
        mode: str = MODE_RAG,
        source_text: str = "",
    ) -> tuple[str, str]:
        """返回 (system_prompt, user_prompt)。

        mode:
          MODE_RAG   — chunks 来自检索，拼接为参考资料（默认，向后兼容）
          MODE_TEXT  — source_text 直接作为上下文，忽略 chunks
          MODE_DIRECT — 无上下文，纯知识出题
        """
        if mode == MODE_TEXT:
            ctx = source_text.strip() if source_text else "（无参考资料，请根据你的知识出题）"
        elif mode == MODE_DIRECT:
            ctx = ""
        else:  # MODE_RAG
            ctx = "\n\n".join(
                f"[参考资料 {i+1}]\n{c.get('text', '')}"
                for i, c in enumerate(chunks[:5])
            ) if chunks else "（无参考资料，请根据你的知识出题）"

        system = self.SYSTEM_TEMPLATE
        if mode == MODE_DIRECT:
            user = (
                f"知识点：{topic}\n\n"
                + self.FORMAT_TEMPLATE.format(count=count, q_type=q_type, topic=topic)
            )
        else:
            user = (
                f"知识点：{topic}\n\n"
                f"参考资料：\n{ctx}\n\n"
                + self.FORMAT_TEMPLATE.format(count=count, q_type=q_type, topic=topic)
            )
        return system, user

class QuestionParser:
    """将 LLM 原始输出解析为结构化题目列表。

    输入格式（每道题用 --- 分隔）：
    ---
    ## <标题>
    题干内容（Markdown，到 ### 选项 前）
    ### 选项
    **A.** ...
    **B.** ...
    **C.** ...
    **D.** ...
    ### 答案
    C
    ### 解析
    详细解析
    ---
    """

    SEP_PATTERN = re.compile(r"^---\s*$", re.MULTILINE)
    ANSWER_PATTERN = re.compile(
        r"^###\s*(?:答案|Answer)\s*\n(.*?)(?=^###\s*(?:解析|Explanation)|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    EXPLANATION_PATTERN = re.compile(
        r"^###\s*(?:解析|Explanation)\s*\n(.*?)(?=^---\s*$|^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    OPTIONS_BLOCK_PATTERN = re.compile(
        r"^###\s*(?:选项|Options)\s*\n(.*?)(?=^###\s*(?:答案|Answer))",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    OPTION_LINE_PATTERN = re.compile(r"^\s*\*\*([A-D])\.\*\*\s*(.+)$", re.MULTILINE)

    def parse(self, raw_output: str) -> list[dict[str, Any]]:
        """解析 LLM 输出，返回 [{stem, options, answer, explanation}, ...] 列表。"""
        blocks = self.SEP_PATTERN.split(raw_output)
        questions: list[dict[str, Any]] = []

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            title_match = re.search(r"^##\s+.+$", block, re.MULTILINE)
            options_match = self.OPTIONS_BLOCK_PATTERN.search(block)

            if options_match:
                stem_start = title_match.end() if title_match else 0
                raw_stem = block[stem_start:options_match.start()].strip()
                stem = re.sub(r"^##\s*.+\n?", "", raw_stem).strip()
            else:
                stem = ""

            options_raw = options_match.group(1) if options_match else ""
            answer = self._extract(block, self.ANSWER_PATTERN)
            explanation = self._extract(block, self.EXPLANATION_PATTERN)

            options = self._parse_options(options_raw)
            if not stem or not answer:
                logger.warning("解析跳过（缺题干或答案）：%s", stem[:30] if stem else "N/A")
                continue

            questions.append({
                "stem": stem,
                "options": options,
                "answer": answer.strip().upper(),
                "explanation": explanation,
            })

        return questions

    def _extract(self, text: str, pattern) -> str:
        m = pattern.search(text)
        return m.group(1).strip() if m else ""

    def _parse_options(self, raw: str) -> dict[str, str]:
        options: dict[str, str] = {}
        for m in self.OPTION_LINE_PATTERN.finditer(raw):
            options[m.group(1)] = m.group(2).strip()
        return options

class QualityValidator:
    """题目质量校验：过滤不合格条目。"""

    def __init__(
        self,
        min_options: int = 4,
        require_single_answer: bool = True,
        require_explanation: bool = True,
    ):
        self.min_options = min_options
        self.require_single_answer = require_single_answer
        self.require_explanation = require_explanation

    def validate(self, questions: list[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
        """返回 (valid, invalid) 元组。"""
        valid, invalid = [], []
        for q in questions:
            reasons = self._check(q)
            if reasons:
                q["_reject_reason"] = "; ".join(reasons)
                invalid.append(q)
            else:
                valid.append(q)
        return valid, invalid

    def _check(self, q: dict) -> list[str]:
        reasons: list[str] = []
        answer = q.get("answer", "")
        options = q.get("options", {})

        if not q.get("stem"):
            reasons.append("题干为空")
        if len(options) < self.min_options:
            reasons.append(f"选项不足 {self.min_options} 个（实际 {len(options)}）")
        if self.require_single_answer:
            if len(answer) != 1:
                reasons.append(f"答案格式错误：{answer!r}")
            if answer not in "ABCD":
                reasons.append(f"答案超出范围：{answer!r}")
        if self.require_explanation and not q.get("explanation"):
            reasons.append("解析为空")

        return reasons


# ── 审核门控 ──────────────────────────────────────────────────

class ReviewGate:
    """题目审核门控：自动校验 + 人工 approve/reject。

    用法:
        gate = ReviewGate(bank)
        result = gate.review_gate("算法_双指针_001")
        # result = {"decision": "approve"|"reject", "reasons": [...]}
        gate.approve("算法_双指针_001")   # 人工确认通过
        gate.reject("算法_双指针_001")    # 人工拒绝
    """

    def __init__(self, bank: "QuestionBank"):
        self._bank = bank
        self._validator = QualityValidator()

    def review_gate(self, question_id: str) -> dict[str, Any]:
        """自动审核一道题。返回 {"decision": "approve"|"reject", "reasons": [...]}。"""
        item = self._bank.get(question_id)
        if item is None:
            return {"decision": "reject", "reasons": [f"题目不存在：{question_id}"]}

        reasons: list[str] = []

        # 已审核通过的不重复审核
        if item.get("reviewed"):
            return {"decision": "approve", "reasons": ["已审核通过"]}

        # 构造 validator 可检查的 dict
        q_for_check = {
            "stem": item.get("body", ""),
            "options": self._extract_options(item.get("body", "")),
            "answer": item.get("answer", ""),
            "explanation": self._extract_explanation(item.get("body", "")),
        }
        check_reasons = self._validator._check(q_for_check)
        reasons.extend(check_reasons)

        decision = "approve" if not reasons else "reject"
        return {"decision": decision, "reasons": reasons}

    def approve(self, question_id: str) -> bool:
        """人工审核通过：设置 reviewed=True。返回是否成功。"""
        return self._set_reviewed(question_id, True)

    def reject(self, question_id: str) -> bool:
        """人工拒绝：设置 reviewed=False。返回是否成功。"""
        return self._set_reviewed(question_id, False)

    def _set_reviewed(self, question_id: str, reviewed: bool) -> bool:
        """更新 frontmatter 的 reviewed 字段。"""
        target = _validate_id(question_id, self._bank.bank_dir)
        if not target.exists():
            return False
        text = target.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        fm["reviewed"] = reviewed
        body = _body(text)
        doc = QuestionBank._render(fm, body)
        target.write_text(doc, encoding="utf-8")
        return True

    @staticmethod
    def _extract_options(body: str) -> dict[str, str]:
        """从正文中提取选项。"""
        options: dict[str, str] = {}
        for m in re.finditer(r"^\s*\*\*([A-D])\.\*\*\s*(.+)$", body, re.MULTILINE):
            options[m.group(1)] = m.group(2).strip()
        return options

    @staticmethod
    def _extract_explanation(body: str) -> str:
        """从正文中提取解析。"""
        m = re.search(
            r"^###\s*(?:解析|Explanation)\s*\n(.*?)(?=^##\s|\Z)",
            body, re.MULTILINE | re.DOTALL,
        )
        return m.group(1).strip() if m else ""


# ── 主类 ──────────────────────────────────────────────────────

class QuestionBank:
    """题库 CRUD + 生成管道。

    不强制依赖 litellm；generate() 在 litellm 不可用时
    返回原始文本，由调用方处理。
    """

    def __init__(self, bank_dir: str | Path | None = None):
        if bank_dir:
            self.bank_dir = Path(bank_dir)
        else:
            self.bank_dir = BANK_DIR
        self.bank_dir.mkdir(parents=True, exist_ok=True)
        self._parser = QuestionParser()
        self._validator = QualityValidator()
        self._stem_prefix_len = 50  # 去重：题干前 N 字符比对

    # ── 去重 ──────────────────────────────────────────────────

    def check_duplicate(self, stem: str, question_id: str = "") -> list[str]:
        """检查是否存在重复题目。返回重复原因列表（空 = 无重复）。

        规则：
        - stem 前缀比对（前 50 字符标准化后完全匹配）
        - question_id 唯一性（如果传入）
        """
        reasons: list[str] = []
        norm_stem = self._normalize_stem(stem)
        if not norm_stem:
            return reasons

        for fp in self.bank_dir.glob("*.md"):
            item = self._load_file(fp)
            if item is None:
                continue

            # question_id 唯一性
            if question_id and item.get("question_id") == question_id:
                reasons.append(f"question_id 已存在：{question_id}")
                continue

            # stem 前缀比对
            existing_body = item.get("body", "")
            existing_title = _extract_title(existing_body) or ""
            # 从 body 提取 stem（## 标题行后到 ### 之间的内容）
            stem_match = re.search(
                r"^##\s+[^\n]+\n(.*?)(?=^###|\Z)", existing_body,
                re.MULTILINE | re.DOTALL,
            )
            existing_stem_text = stem_match.group(1).strip() if stem_match else existing_title
            norm_existing = self._normalize_stem(existing_stem_text)

            if norm_stem == norm_existing:
                reasons.append(
                    f"题干前缀重复：'{norm_stem[:30]}...' 与 {item.get('question_id', '?')} 相同"
                )

        return reasons

    def _normalize_stem(self, stem: str) -> str:
        """标准化题干：去除空白和标点，取前 N 字符。"""
        s = re.sub(r'\s+', '', stem)
        s = re.sub(r'[，。？！、；：""''【】《》（）]', '', s)
        return s[:self._stem_prefix_len]

    # ── CRUD ────────────────────────────────────────────────

    def add_manual(
        self,
        title: str,
        content: str,
        q_type: str,
        knowledge: str,
        answer: str,
        options: dict[str, str] | None = None,
        explanation: str = "",
        difficulty: str = "中等",
        source: str = "manual",
        source_url: str = "",
        tags: list[str] | None = None,
        reviewed: bool = False,
        generated: bool = False,
        check_dup: bool = False,
    ) -> str:
        """人工录入一道题。返回写入的文件名。

        check_dup: True 时检查 stem 前缀重复（默认 False，保持向后兼容）。
        """
        if q_type not in TYPE_PREFIX:
            raise ValueError(f"不支持的题型：{q_type}（支持：{list(TYPE_PREFIX)}）")
        if difficulty not in DIFFICULTY_OPTIONS:
            raise ValueError(f"不支持的难度：{difficulty}（支持：{DIFFICULTY_OPTIONS}）")

        # 去重检查（opt-in）
        if check_dup:
            dup_reasons = self.check_duplicate(content)
            if dup_reasons:
                raise ValueError(f"题目重复：{'; '.join(dup_reasons)}")

        filename = _build_filename(q_type, knowledge, bank_dir=self.bank_dir)
        filepath = self.bank_dir / filename

        today = _today()
        fm: dict[str, Any] = {
            "type": q_type,
            "knowledge": knowledge,
            "difficulty": difficulty,
            "source": source,
            "generated": generated,
            "reviewed": reviewed,
            "question_id": filename.replace(".md", ""),
            "tags": tags or [],
            "created": today,
        }
        if source_url:
            fm["source_url"] = source_url

        options = options or {}
        option_lines = "\n".join(
            f"**{k}.** {v}" for k, v in sorted(options.items())
        )

        body = (
            f"## {title}\n\n"
            f"{content}\n\n"
            f"### 选项\n\n{option_lines}\n\n"
            f"### 答案\n\n{answer}\n\n"
            f"### 解析\n\n{explanation}\n"
        )

        doc = self._render(fm, body)
        filepath.write_text(doc, encoding="utf-8")
        logger.info("已保存题目: %s", filename)
        return filename

    def add(self, question: dict, check_dup: bool = True) -> str:
        """从 dict 保存一道题。

        支持两种输入格式：
        - 完整格式（add_manual 调用方）: title, content, type, knowledge, answer, ...
        - 解析器格式（generate 管道）: stem, options, answer, explanation, type, knowledge

        check_dup: 默认 True，自动检查 stem 重复。管道调用时启用。
        """
        if "stem" in question:
            return self.add_manual(
                title=question.get("stem", "未命名题目")[:50],
                content=question["stem"],
                q_type=question["type"],
                knowledge=question["knowledge"],
                answer=question["answer"],
                options=question.get("options"),
                explanation=question.get("explanation", ""),
                difficulty=question.get("difficulty", "中等"),
                source=question.get("source", "llm"),
                source_url=question.get("source_url", ""),
                tags=question.get("tags", []),
                reviewed=False,
                generated=True,
                check_dup=check_dup,
            )
        return self.add_manual(
            title=question["title"],
            content=question["content"],
            q_type=question["type"],
            knowledge=question["knowledge"],
            answer=question["answer"],
            options=question.get("options"),
            explanation=question.get("explanation", ""),
            difficulty=question.get("difficulty", "中等"),
            source=question.get("source", "llm"),
            source_url=question.get("source_url", ""),
            tags=question.get("tags", []),
            reviewed=False,
            check_dup=check_dup,
        )

    def get(self, question_id: str) -> dict | None:
        """按 question_id 读取题目。"""
        target = _validate_id(question_id, self.bank_dir)
        if not target.exists():
            return None
        return self._load_file(target)

    def list_all(
        self,
        q_type: str | None = None,
        knowledge: str | None = None,
    ) -> list[dict]:
        """列出题库，支持题型/知识点过滤。"""
        results: list[dict] = []
        for fp in sorted(self.bank_dir.glob("*.md")):
            item = self._load_file(fp)
            if q_type and item.get("type") != q_type:
                continue
            if knowledge and item.get("knowledge") != knowledge:
                continue
            results.append(item)
        return results

    def delete(self, question_id: str) -> bool:
        """删除题目。返回是否成功。"""
        target = _validate_id(question_id, self.bank_dir)
        if not target.exists():
            return False
        target.unlink()
        logger.info("已删除: %s", question_id)
        return True

    def count(self, q_type: str | None = None) -> int:
        """统计题目数（可过滤题型）。"""
        if q_type:
            return len(self.list_all(q_type=q_type))
        return len(list(self.bank_dir.glob("*.md")))

    # ── 生成管道 ────────────────────────────────────────────

    def generate(
        self,
        topic: str,
        count: int = 3,
        q_type: str = "算法",
        difficulty: str = "中等",
        top_k: int = 5,
    ) -> dict[str, Any]:
        """RAG + LLM 生成题目管道（向后兼容入口）。

        等价于 rag_extract()。保留用于已有调用方。
        """
        return self.rag_extract(topic, count, q_type, difficulty, top_k)

    def rag_extract(
        self,
        topic: str,
        count: int = 3,
        q_type: str = "算法",
        difficulty: str = "中等",
        top_k: int = 5,
    ) -> dict[str, Any]:
        """RAG 模式：hybrid_search 检索 → prompt → LLM → 解析 → 校验 → 保存。"""
        chunks = self._retrieve(topic, q_type, top_k)
        system_prompt, user_prompt = PromptBuilder().build(
            chunks, topic, q_type, count, mode=MODE_RAG,
        )
        return self._run_pipeline(system_prompt, user_prompt, topic, q_type, difficulty)

    def text_extract(
        self,
        source_text: str,
        topic: str,
        count: int = 3,
        q_type: str = "算法",
        difficulty: str = "中等",
    ) -> dict[str, Any]:
        """文本模式：直接使用提供的文本内容作为上下文出题。"""
        system_prompt, user_prompt = PromptBuilder().build(
            [], topic, q_type, count,
            mode=MODE_TEXT, source_text=source_text,
        )
        return self._run_pipeline(system_prompt, user_prompt, topic, q_type, difficulty)

    def direct_extract(
        self,
        topic: str,
        count: int = 3,
        q_type: str = "算法",
        difficulty: str = "中等",
    ) -> dict[str, Any]:
        """直出模式：无上下文，纯靠 LLM 知识出题。"""
        system_prompt, user_prompt = PromptBuilder().build(
            [], topic, q_type, count, mode=MODE_DIRECT,
        )
        return self._run_pipeline(system_prompt, user_prompt, topic, q_type, difficulty)

    def _run_pipeline(
        self,
        system_prompt: str,
        user_prompt: str,
        topic: str,
        q_type: str,
        difficulty: str,
    ) -> dict[str, Any]:
        """共享管道：call_llm → parse → validate → save。"""
        result: dict[str, Any] = {
            "saved": [],
            "validated": [],
            "rejected": [],
            "raw_llm_output": None,
            "error": None,
        }

        raw = self._call_llm(system_prompt, user_prompt)
        if raw is None:
            result["error"] = "LLM 不可用（litellm 未安装或未配置 API key）"
            return result
        result["raw_llm_output"] = raw

        questions = self._parser.parse(raw)
        if not questions:
            result["error"] = "LLM 输出未解析出任何题目"
            return result

        valid, rejected = self._validator.validate(questions)
        result["rejected"] = rejected

        for q in valid:
            q["type"] = q_type
            q["knowledge"] = topic
            q["difficulty"] = difficulty
            try:
                fname = self.add(q)
            except ValueError as e:
                q["_reject_reason"] = str(e)
                result["rejected"].append(q)
                continue
            result["saved"].append(fname)
            loaded = self._load_file(self.bank_dir / fname)
            if loaded:
                result["validated"].append(loaded)

        return result

    # ── 检索 ─────────────────────────────────────────────────

    def search(
        self,
        query: str,
        limit: int = 5,
        q_type: str | None = None,
    ) -> list[dict]:
        """复用 hybrid_search 搜索题库（不独立建索引）。

        扫描 bank/ 的 frontmatter 做过滤，返回完整题目内容。
        """
        try:
            from exam_memory.hybrid_search import hybrid_search
            from exam_memory.fts_store import FTSStore
            from exam_memory.vector_store import NumpyVectorStore

            fts = FTSStore()
            vec = NumpyVectorStore()
            hits = hybrid_search(query, fts, vec, limit=limit, exp_type=q_type)
            fts.close()
        except Exception as e:
            logger.debug("hybrid_search 失败，降级为全文扫描：%s", e)
            hits = []

        if not hits:
            return self._fallback_search(query, limit, q_type)

        results: list[dict] = []
        for hit in hits:
            text = hit.get("text", "")
            meta = hit.get("metadata", {})
            qid = meta.get("file_name", "").replace(".md", "")
            if qid:
                full = self.get(qid)
                if full:
                    results.append(full)
                    continue
            results.append({
                "question_id": qid or "",
                "title": meta.get("title", ""),
                "text": text,
                "score": hit.get("score"),
            })
        return results

    def import_from_dir(self, path: str | Path) -> int:
        """批量导入 Markdown 题库文件到 bank/。返回导入条数。"""
        src = Path(path)
        if not src.is_dir():
            raise ValueError(f"目录不存在：{path}")

        # 建立已有文件的索引: (type, knowledge) -> filename
        existing: set[tuple[str, str]] = set()
        for fp in self.bank_dir.glob("*.md"):
            text = fp.read_text(encoding="utf-8")
            em = _parse_frontmatter(text)
            existing.add((em.get("type", ""), em.get("knowledge", "")))

        imported = 0
        for fp in sorted(src.glob("*.md")):
            text = fp.read_text(encoding="utf-8")
            fm = _parse_frontmatter(text)
            body = _body(text)

            q_type = fm.get("type", "")
            if q_type not in TYPE_PREFIX:
                logger.warning("跳过（未知题型 %s）：%s", q_type, fp.name)
                continue

            knowledge = fm.get("knowledge", "未分类")
            if (q_type, knowledge) in existing:
                logger.debug("已存在（%s / %s），跳过", q_type, knowledge)
                continue

            filename = _build_filename(q_type, knowledge, bank_dir=self.bank_dir)
            fm.setdefault("question_id", filename.replace(".md", ""))
            fm.setdefault("imported", True)
            fm.setdefault("source", fm.get("source", fp.name))

            doc = self._render(fm, body)
            (self.bank_dir / filename).write_text(doc, encoding="utf-8")
            existing.add((q_type, knowledge))
            imported += 1

        logger.info("导入完成：%d 条 -> %s", imported, self.bank_dir)
        return imported

    # ── 内部方法 ─────────────────────────────────────────────

    def _retrieve(self, topic: str, q_type: str, top_k: int) -> list[dict]:
        """从 experiences/ + bank/ 检索相关 chunks。"""
        try:
            from exam_memory.hybrid_search import hybrid_search
            from exam_memory.fts_store import FTSStore
            from exam_memory.vector_store import NumpyVectorStore

            fts = FTSStore()
            vec = NumpyVectorStore()
            hits = hybrid_search(topic, fts, vec, limit=top_k, exp_type=q_type)
            fts.close()
            return hits
        except Exception as e:
            logger.debug("检索失败：%s", e)
            return []

    def _call_llm(self, system: str, user: str) -> str | None:
        """调用 LLM（litellm），失败返回 None。"""
        try:
            from litellm import completion
        except ImportError:
            logger.info("litellm 未安装，跳过 LLM 调用（pip install '.[generate]'）")
            return None

        try:
            resp = completion(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.7,
                max_tokens=4000,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.error("LLM 调用失败：%s", e)
            return None

    def _fallback_search(
        self, query: str, limit: int, q_type: str | None
    ) -> list[dict]:
        """hybrid_search 不可用时的降级：全文扫描 + 简单关键词匹配。"""
        results: list[dict] = []
        q_lower = query.lower()
        for fp in sorted(self.bank_dir.glob("*.md")):
            if len(results) >= limit:
                break
            item = self._load_file(fp)
            if q_type and item.get("type") != q_type:
                continue
            text_blob = f"{item.get('title','')} {item.get('body','')}".lower()
            if q_lower in text_blob or not q_lower:
                results.append(item)
        return results

    def _load_file(self, fp: Path) -> dict | None:
        """读取 .md 文件，返回含 frontmatter + body + raw 的 dict。"""
        text = fp.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        body = _body(text)
        answer_match = re.search(r"^###\s*答案\s*\n(.+?)(?:\n\n|\Z)", body, re.MULTILINE)
        return {
            "question_id": fm.get("question_id", fp.stem),
            "file_name": fp.name,
            "type": fm.get("type", ""),
            "knowledge": fm.get("knowledge", ""),
            "difficulty": fm.get("difficulty", "中等"),
            "source": fm.get("source", ""),
            "source_url": fm.get("source_url", ""),
            "generated": fm.get("generated", False),
            "reviewed": fm.get("reviewed", False),
            "tags": fm.get("tags", []),
            "created": fm.get("created", ""),
            "title": _extract_title(text) or fm.get("knowledge", fp.stem),
            "body": body,
            "answer": answer_match.group(1).strip() if answer_match else "",
            "raw": text,
        }

    @staticmethod
    def _render(fm: dict, body: str) -> str:
        yaml_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False)
        return f"---\n{yaml_str}---\n\n{body}"


# ── 辅助函数 ──────────────────────────────────────────────────

def _extract_title(text: str) -> str | None:
    """提取正文第一个 ## 标题。"""
    m = re.search(r"^##\s+(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def _today() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")
