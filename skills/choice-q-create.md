---
name: choice-q-create
description: >
  Generate targeted multiple-choice question sets for the AI Lab campus recruitment exam.
  Use this skill whenever the user asks for new practice questions — even casual requests
  like "出几道题练练" or "帮我准备一下选择题" or "再来一套". Trigger phrases: "准备选择题",
  "出题", "新题", "选择题制作", "generate choice questions", "new mock", "新一轮选择题",
  "choice q round", "再出一套", "出一套新题", "出几道", "准备一套", "mock", "刷题题库",
  "帮我出题", "选题". Also use when the user wants targeted practice on specific weak topics
  (e.g. "帮我出几道GNN的题"), or when combining web search + historical patterns +
  mistake_log to create targeted practice material. After generation, direct the user to
  `choice-q-drill` for interactive answering.
---

# Choice Question Creation Skill

Generate targeted multiple-choice question sets for the AI Lab campus recruitment exam.
Combines web search, historical problem bank, mistake_log, and cross-session experience
patterns from the exam-memory MCP server to create high-quality practice material.
Outputs a self-contained markdown file ready for the `choice-q-drill` skill.

The create skill reads from two feedback sources: `mistake_log.md` (local, quick-reference)
and `list_experiences` MCP (cross-session, structured by type/knowledge). Topics appearing
in both sources get highest priority because they represent persistent weak points that
haven't been resolved yet.

## 1. Exam Format Reference

| Item | Value |
|------|-------|
| 单选题 | 8 题 × 3 分 = 24 分 |
| 不定项选择题 | 7 题 × 4 分 = 28 分 |
| 选择题合计 | 15 题, 52 分 |
| 时间建议 | 30 分钟 |
| 多选策略 | 漏选比多选扣分少，不确定不选 |

## 2. Topic Pool

Draw questions from these 12 domains, balanced across rounds:

| Category | Key Topics | Source |
|----------|-----------|--------|
| 线性代数 | 特征值、SVD、正交/正定、行列式 | `llm/math_fundamentals.md` |
| 概率统计 | 贝叶斯、分布、独立vs不相关 | `llm/math_fundamentals.md` |
| 微积分/优化 | 链式法则、梯度、凸函数、SGD | `llm/math_fundamentals.md` |
| DL 基础 | Softmax、BN、CNN、参数量计算 | `llm/llm_core_cheatsheet.md` |
| Transformer | 注意力、位置编码、KV cache | `llm/llm_core_cheatsheet.md` |
| LLM 架构 | LLaMA3、GQA/MQA、RoPE、SwiGLU | `llm/llm_core_cheatsheet.md` |
| 微调/对齐 | LoRA/QLoRA、RLHF/DPO | `llm/llm_core_cheatsheet.md` |
| RAG/Agent | RAG流程、ReAct、Function Calling | `llm/llm_core_cheatsheet.md` |
| GNN | GCN vs GAT、过平滑、消息传递 | `llm/gnn_diffusion_cheatsheet.md` |
| 扩散模型 | DDPM/DDIM、CFG、Latent Diffusion | `llm/gnn_diffusion_cheatsheet.md` |
| 推理优化 | KV Cache、量化、FlashAttention | `llm/llm_core_cheatsheet.md` |
| 数据结构 | 栈/队列、排序、哈希 | `algorithms/mistake_log.md` |

## 3. Question Quality Rules

### Single-choice (单选, 3 分)
- Exactly 4 options (A/B/C/D), exactly 1 correct.
- Distractors must be plausible — based on common misconceptions from `mistake_log.md`.
- Each question tests ONE clear concept.
- Prefer "下列说法**错误**的是" or "下列说法**正确**的是" format.

### Multi-choice (不定项, 4 分)
- Exactly 4 options (A/B/C/D), 1-4 correct.
- Clearly state: "漏选得 2 分，多选/错选 0 分".
- Options should be independently evaluable — each is a standalone true/false claim.
- At least one question should be "全选" or "单选" to test confidence.

### Difficulty distribution per round
- 60% concept recall (direct knowledge test)
- 30% application (calculate, compare, reason)
- 10% trap (subtle distinction, common misconception)

## 4. Weak Point Targeting

0. **Read mastery data** — check `progress/exam-analysis/exam-style-analysis.md` §6 "知识点掌握进度" for mastery levels per topic. Also read `algorithms/mistake_log.md` Mastery column. This is the **canonical source** for mastery info; prefer it over re-querying exam-memory MCP.

Before generating, read `progress/exam-analysis/exam-style-analysis.md` §2 频率表 and §4 趋势预测 to calibrate
the topic allocation ratio — simulated类 36%, 字符串 29%, 数论/栈 各 21% are the empirical baseline.
Use §4.2 选择题预测 to identify which domains to overweight based on historical exam patterns.
Then read `algorithms/mistake_log.md` and check:
1. Which topics have the most errors? → Allocate 2-3 questions there.
2. Which errors have `Redo Date` that hasn't passed? → Include reinforcement questions.
3. **Cross-session experience patterns** — call `mcp__exam-memory__list_experiences(type="单选题", limit=5)` and `mcp__exam-memory__list_experiences(type="多选题", limit=5)` to retrieve persistent error patterns from the exam-memory MCP server. These patterns survive across sessions and capture errors that may not yet be in mistake_log.md. If the MCP exposes mastery levels (e.g. per-knowledge mastery scores), also query them — but note that `progress/exam-analysis/exam-style-analysis.md` §6 is the canonical source and should be preferred. If exam-memory does not yet expose mastery levels, use `error_count` as a proxy for `struggling` topics. Merge these with mistake_log findings — topics appearing in BOTH sources get highest priority. **MCP 不可用时跳过此步骤**。
4. **Mastery-driven allocation** — For each topic, determine mastery level:
   - `blind_spot` → allocate 2-3 questions (highest priority, user doesn't really know it)
   - `struggling` → allocate 2 questions (high priority)
   - `partial` → allocate 1 question + 1 variant (medium priority)
   - `confirmed` → allocate 0-1 question (low priority, just for reinforcement)
   - `unknown` → allocate 1 question (exploration)

   Phase-aware adjustment (if user specified a phase in last drill session):
   - Phase 1 (主攻盲区): blind_spot + struggling get 70% of questions
   - Phase 2 (补盲+拓展): 50% blind_spot/struggling + 50% new
   - Phase 3 (全真模拟): even distribution across 12 domains
   - Phase 4 (考前冲刺): only high-frequency mistake_log topics
5. Which `Root Cause` tags appear most (pattern/proof/python)? → Balance question types.

Also check `progress/choice-questions/round*.md` for previously used questions — **never duplicate**.

## 5. Web Search Integration

Use WebSearch for current/recent topics:
- "LLaMA3 architecture details 2024" — latest model specifics
- "GNN over-smoothing solutions" — new research angles
- "DDPM vs DDIM vs DPM-Solver" — sampling method comparisons
- "LoRA variants 2024 QLoRA DoRA" — new fine-tuning methods
- "RAG pipeline best practices" — latest retrieval patterns

Only search when a topic needs fresh material or the user requests it.

## 6. Output Format

Write the question set to `progress/choice-questions/roundN.md` (N = next available number).
Use this exact structure:

```markdown
# AI Lab 选择题模拟 — Round N

> 上海人工智能实验室 | 基座模型算法 | 考前模拟
> 时间：30 分钟 | 单选 8 题 × 3 分 = 24 分 + 不定项 7 题 × 4 分 = 28 分 | 满分 52 分
> 策略：单选每题 ≤ 2 分钟，多选每题 ≤ 3 分钟，不确定的多选宁可漏选不多选

---

## Part A：单选题（每题 3 分，选唯一正确答案）

### Q1. [Topic Tag]

[Question text]

A. ...
B. ...
C. ...
D. ...

---
(repeat for Q2-Q8)

## Part B：不定项选择题（每题 4 分，漏选得 2 分，多选/错选 0 分）

### Q9. [Topic Tag]

[Question text]

A. ...
B. ...
C. ...
D. ...

---
(repeat for Q10-Q15)

---

# 参考答案与解析

## Part A 单选题

### Q1 答案：X

**解析**：
- A：... ✓/✗
- B：... ✓/✗
- **C**：... ✓/✗ (bold the correct one)
- D：... ✓/✗

> **防错**：[one-line pitfall note from mistake_log if applicable]

---
(repeat for all questions)

## 成绩统计表

| 题号 | 你的答案 | 正确答案 | 得分 |
|------|----------|----------|------|
| Q1 | | X | /3 |
...
| **总分** | | | **/52** |

## 覆盖知识点与错题溯源

| 题号 | 知识点 | 对应错题/薄弱点 |
|------|--------|----------------|
| Q1 | ... | ... |
...
```

## 7. Workflow

### 阶段一：数据采集（Agent 并行）

> **为什么用 Agent**：出题前需要读取多个数据源（exam-style-analysis、mistake_log、历史 round 文件、llm/ 笔记、MCP 经验）。这些文件体积大、内容多，逐文件进入主上下文会导致 token 浪费。通过 Agent 并行采集 + 摘要返回，主会话只拿到结构化出题参数。

```python
# 在 choice-q-create 被调用时，主会话启动 Agent 执行数据采集：
# Agent 读取全部数据源 → 返回出题参数 JSON → 主会话基于 JSON 出题
```

**Agent 数据采集任务**：

```
你是选择题出题数据助手。请读取以下文件并提取出题所需的结构化摘要，返回 JSON。

1. progress/exam-analysis/exam-style-analysis.md
   返回：{
     frequency_table: [{模式, 频次, 占比, 代表题}],
     style_features: [str],
     trend_prediction: { 选择题预测: [str], 编程题预测: [str] },
     mock_scores: [{ round, date, score, total }],
     mastery_progress: {
       confirmed: [{topic, details}],
       struggling: [{topic, details}],
       blind_spot: [{topic, details}],
       unknown: [{topic, details}]
     }
   }

2. algorithms/mistake_log.md
   返回：{
     error_topics: [{topic, count, root_cause, fix_rule, redo_date}],
     root_cause_summary: { pattern: n, proof: n, python: n },
     high_frequency_errors: [{topic, count}]  # count >= 2
   }

3. progress/choice-questions/round*.md
   返回：{
     existing_rounds: [{round, date, questions_covered: [topic_tags]}],
     used_topics: [str]  # 所有已出现过的知识点标签，用于去重
   }

4. llm/math_fundamentals.md（如果存在）
   返回：{ available_topics: [str], key_formulas: [str] }

5. llm/llm_core_cheatsheet.md（如果存在）
   返回：{ available_topics: [str] }

6. llm/gnn_diffusion_cheatsheet.md（如果存在）
   返回：{ available_topics: [str] }

7. 调用 MCP（如果可用）：list_experiences(type="单选题", limit=5) 和 list_experiences(type="多选题", limit=5)
   返回：{ single_choice_experiences: [{title, knowledge, error_count}],
           multi_choice_experiences: [{title, knowledge, error_count}] }

如果某个文件不存在或为空，对应字段返回 null 或空数组。不要编造数据。
```

**降级规则**：Agent 不可用时，主会话回退到逐文件读取（降级模式）。

### 阶段二：出题
7. **Write questions** — generate all 15 based on the collected data
8. **Write answers & analysis** — full explanations with 防错 markers
9. **Save file** — `progress/choice-questions/roundN.md`
10. **Report** — tell user the file is ready, suggest invoking `choice-q-drill`

### 阶段三：输出

## 8. Cross-References

- `choice-q-drill` — interactive quiz mode for answering the generated questions
- `progress/exam-analysis/exam-style-analysis.md` — 集中式出题风格分析：频率表、趋势预测、mock 成绩（**核心输入**）
- `algorithms/mistake_log.md` — error patterns to target and update
- `sources/ai_lab_history_problems.md` — historical question patterns and high-frequency topics
- `llm/llm_core_cheatsheet.md` — LLM/DL source material
- `llm/gnn_diffusion_cheatsheet.md` — GNN/diffusion source material
- `llm/math_fundamentals.md` — math source material
- `exam-memory` MCP tools — cross-session persistent error patterns (mcp__exam-memory__list_experiences)
- `skills/exam-assistant.md` — MCP-backed exam assistant with full experience workflow
