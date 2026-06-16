---
name: review-tracker
description: >
  Use when checking exam preparation progress, generating review reports, identifying weak areas,
  or deciding what to study next. Triggers: "复习进度", "进度报告", "就绪度", "readiness",
  "还差什么", "薄弱环节", "今天复习什么", "考前看什么", "进度怎么样", "复习到哪了",
  "帮我看看进度", "还需要练什么", "哪些没复习到", "自评打分", "总结一下", "看看还差多少".
---

# Review Tracker

跨文件聚合备考进度，生成结构化复习报告，输出今日必做清单。
将 task_board、readiness_score、mistake_log、topic_checklist、daily logs 等分散数据源
汇总为一份可执行的进度报告，让用户在 2 分钟内知道"现在在哪、还差什么、下一步做什么"。

核心原则：**数据驱动复习决策** — 不凭感觉，凭 mistake_log 错误频率、topic_checklist 覆盖率、readiness_score 趋势做判断。

## When to Use

- 用户问"复习到哪了"、"还差什么"、"进度怎么样"
- 练习 session 结束后做总结
- 考前想快速看"只看这些就够了"
- 每日 session 开始时作为 first-step 进度感知

## When NOT to Use

- 用户想做题 → 用 `choice-q-create` / `choice-q-drill`
- 用户想解算法题 → 用 `solve-skeleton`
- 用户只想看某一个文件 → 直接 Read

## 数据源

| 文件 | 读取内容 | 报告章节 |
|------|---------|---------|
| `progress/task-board/task-board.md` | 任务状态 (Done/Today/Pending) | 任务进度 |
| `progress/study-planning/readiness-score.md` | 各维度自评分 + 考试策略 | 就绪度趋势 |
| `progress/exam-analysis/exam-style-analysis.md` | 出题风格、频率表、趋势预测、mock 成绩 | 出题风格分析 |
| `algorithms/mistake_log.md` | WA 记录、Root Cause 分布、Redo Date | 错题待修复清单 |
| `algorithms/topic_checklist.md` | P0/P1/P2 模式覆盖 | 知识点覆盖度 |
| `daily/YYYY-MM-DD.md` (今天) | Problem Log、正确率统计 | 今日练习总结 |
| `daily/YYYY-MM-DD.md` (昨天) | 对比昨天进度 | 进步/退步对比 |
| `progress/choice-questions/round*.md` | 选择题 Round 成绩 | 选择题趋势 |
| `progress/exam-analysis/exam-style-analysis.md` §6 | 知识点掌握进度表 | 掌握进度 |
| `progress/reviews/review-YYYY-MM-DD.md` | 周期性复习总结（可选） | 复习总结 |

## 工作流

### 阶段一：数据采集（Agent 并行）

> **为什么用 Agent**：本 skill 需要读取 6-8 个文件（task_board、readiness_score、mistake_log、topic_checklist、daily logs、choice-questions、exam-style-analysis）。如果逐文件读取进入主对话上下文，会占用大量 token 且包含大量无关内容。通过 Agent 并发读取 + 摘要返回，主上下文只接收结构化指标，显著压缩上下文长度。

```
digraph review {
  rankdir=TB;
  node [shape=box];

  agent_collect [label="Agent 并行采集\n读取全部数据源 → 返回结构化摘要"];
  aggregate [label="主会话汇总\n合成进度报告"];
  output [label="输出报告\n建议今日必做清单"];

  agent_collect -> aggregate -> output;
}
```

**执行方式**：

```python
# 在 review-tracker 被调用时，主会话执行以下操作：
# 1. 启动一个 Agent，传入数据采集任务
# 2. Agent 并行读取所有数据源文件，提取关键指标
# 3. Agent 返回紧凑的 JSON 摘要（非原始文件内容）
# 4. 主会话基于摘要生成报告
```

**Agent 数据采集任务**（作为 prompt 传入 Agent）：

```
你是进度数据采集助手。请读取以下文件并提取关键指标，返回紧凑的结构化摘要。

使用 Glob 查找文件路径（文件名可能含日期变体），然后读取每个文件提取以下指标：

1. progress/task-board/task-board.md
   返回：{ total: int, done: int, today: int, pending: int }

2. progress/study-planning/readiness-score.md
   返回：{ latest_date: str, scores: { 算法: x/50, 数学: x/15, AI_ML: x/25, 项目: x/5, 后勤: x/5 } }
   如果最新行是占位符（/50 等），取上一行有实际数字的行。

3. algorithms/mistake_log.md
   返回：{ total_entries: int, root_cause_counts: { pattern: n, proof: n, python: n },
           due_today: [ { problem, topic, root_cause, fix_rule } ],
           due_tomorrow: [ { problem, topic, root_cause, fix_rule } ] }
   Redo Date <= 今天 = due_today，= 明天 = due_tomorrow。

4. algorithms/topic_checklist.md
   返回：{ P0: { total, covered, uncovered_list },
           P1: { total, covered, uncovered_list },
           P2: { total, covered, uncovered_list } }
   "covered" = 有对应 solutions_batch.py 实现或 practice/ 文件。

5. daily/ 目录下今天的文件（如 daily/2026-06-15.md）
   返回：{ ac_count: int, total_count: int, new_wa: n, mock_score: str | null }

6. daily/ 目录下昨天的文件
   返回：{ ac_count: int, total_count: int } （用于对比）

7. progress/choice-questions/round*.md
   返回：{ rounds: [ { round, date, single_score, multi_score, total, main_errors } ] }

8. progress/exam-analysis/exam-style-analysis.md
   返回：{ mastery: { confirmed: n, struggling: n, blind_spot: n, unknown: n },
           mastery_details: { confirmed: [...], struggling: [...], blind_spot: [...], unknown: [...] },
           mock_score: str | null,
           coverage_gaps: [str] }

如果某个文件不存在或为空，对应字段返回 null。不要编造数据。
```

**降级规则**：Agent 不可用时，主会话回退到逐文件读取（降级为无 agent 模式）。

### 阶段二：汇总生成报告

报告分为 8 个固定章节（见下方"报告格式"）。核心是三个决策输出：

1. **就绪度评分**：5 个维度加权汇总
2. **错题待修复清单**：按 Redo Date 排序，优先到期条目
3. **今日必做清单**：从错题 + 覆盖缺口中推导

### 阶段三：输出

## 降级处理（数据源缺失时）

任何一个数据源文件缺失或为空时，**跳过对应章节并在报告中标注"暂无数据"**，不要编造数字。

| 缺失文件 | 对应章节 | 处理方式 |
|----------|---------|---------|
| `mistake_log.md` 为空或无条目 | 三、错题待修复 | 输出"暂无错题记录"，今日必做清单跳过错题修复项 |
| 今天无 `daily/YYYY-MM-DD.md` | 六、今日练习总结 | 输出"今日尚无练习记录" |
| 昨天无 `daily/YYYY-MM-DD.md` | 二、就绪度趋势 | 跳过对比，仅输出最新分数 |
| 无 `choice_q_round*.md` | 五、选择题趋势 | 输出"暂无选择题模拟记录" |
| `readiness_score.md` 全部行为占位符 | 二、就绪度趋势 | 输出"未自评——建议先执行自评打分" |
| `topic_checklist.md` 缺失 | 四、知识点覆盖度 | 输出"暂无知识点清单" |
| `exam_style_analysis.md` 缺失 | 出题风格分析 | 跳过该章节，从 task_board.md 提取简要风格信息 |
| `exam-style-analysis.md` §6 无 mastery 数据 | mastery 分布章节 | 输出"暂无掌握进度数据——建议先完成一轮选择题 drill" |
| `task_board.md` 缺失 | 一、任务进度 | 输出"暂无任务看板" |
| Agent 并行采集不可用 | 全部章节 | 回退到主会话逐文件读取（降级模式，上下文会增大） |

**核心原则**：宁可章节空白，不要编造数据。缺失信息会在今日必做清单中体现为待补项。

## 报告格式

```markdown
## 进度报告（YYYY-MM-DD）

### 一、任务进度

| 指标 | 值 |
|------|---|
| 已完成 | X/Y |
| 今日待办 | N 项 |
| 总体进度 | XX% |

### 二、就绪度趋势

| 日期 | 算法 | 数学 | AI/ML | 项目 | 后勤 | 总分 |
|------|------|------|-------|------|------|------|
| MM-DD | /50 | /15 | /25 | /5 | /5 | /100 |
| **今日自评** | /50 | /15 | /25 | /5 | /5 | /100 |

自评打分依据：[简述各维度判断标准]

### 三、错题待修复（按 Redo Date 排序）

| 优先级 | 题目 | 主题 | Root Cause | 防错规则 | Redo Date |
|--------|------|------|------------|---------|-----------|
| 🔴 到期 | ... | ... | ... | ... | MM-DD |
| 🟡 明天 | ... | ... | ... | ... | MM-DD |
| ⚪ 未到 | ... | ... | ... | ... | MM-DD |

Root Cause 分布：pattern(X) / proof(X) / python(X)

### 四、知识点覆盖度

| 优先级 | 总数 | 已覆盖 | 未覆盖 | 缺口 |
|--------|------|--------|--------|------|
| P0 | N | N | N | [列出未覆盖项] |
| P1 | N | N | N | [列出未覆盖项] |
| P2 | N | N | N | [可选] |

### 四-b、出题风格分析（from exam_style_analysis.md）

| 维度 | 结论 | 数据来源 |
|------|------|----------|
| 模式偏好 | 模拟类 36%、字符串 29%、数论 21%、栈 21% | §2 频率表 |
| 出题风格 | 轻数据结构、重逻辑包装；边界陷阱多 | §3 风格特征 |
| 补考概率 | 双指针+滑窗、BFS/DFS 真题缺席但 OJ 高频 | §4 趋势预测 |
| Mock 分数 | X/52（最近一次） | §5 mock 成绩 |
| 覆盖缺口 | [对比 checklist 已覆盖 vs 频率表高频未覆盖] | §2 + topic_checklist |

### 五、选择题趋势

| Round | 日期 | 单选 | 多选 | 总分 | 主要错因 |
|-------|------|------|------|------|---------|
| R1 | MM-DD | X/24 | X/28 | X/52 | ... |
| R2 | MM-DD | X/24 | X/28 | X/52 | ... |

### 七、今日练习总结（如有 Problem Log）

- AC：X/Y 题
- 新增 WA：N 条
- 薄弱点：[列表]

### 六-b、知识点掌握分布

| Mastery | 数量 | 知识点 |
|---------|------|--------|
| confirmed | X | [列出] |
| struggling | X | [列出] |
| blind_spot | X | [列出] |
| unknown | X | [列出] |

**建议**：优先处理 blind_spot（立即重做同知识点变体），其次是 struggling（安排明日 Redo）。

### 七、今日必做清单

1. [ ] **错题修复**：重做到期错题 [题名]
2. [ ] **模式练习**：补齐 [未覆盖的 P0/P1 模式]
3. [ ] **模板默写**：[根据 checklist 中 AC 标准未达标的项]
4. [ ] **选择题**：针对 [薄弱主题] 做专项练习
5. [ ] **知识口述**：[根据 AI/ML 维度最低分项]
6. [ ] **盲区修复**：重做 [blind_spot 知识点] 的变体题
7. [ ] **易错点巩固**：[struggling 知识点] 安排明日 Redo
```

## 自评打分规则

当用户说"自评打分"或需要更新 readiness_score.md 时，按以下标准评估：

### 算法维度（/50 分）

| 项目 | 满分 | 达标标准 |
|------|------|---------|
| 模拟类 AC 稳定 | 12 | solutions_batch.py 中模拟题模板可默写 |
| 栈操作熟练 | 8 | GCD 熔合 + 括号匹配 5 分钟写出 |
| 数论模板 | 6 | 质因数分解 sqrt(n) 试除可快速套用 |
| 双指针 + 滑窗 | 6 | practice/ 中有对应实现且理解不变量 |
| BFS/DFS 网格搜索 | 6 | BFS 模板 3 分钟默写，visited 时机正确 |
| ACM IO 不出错 | 5 | 多组输入/EOF/空行处理正确 |
| 贪心 + 排序 + 前缀和 | 4 | 降序 + ceil 累加无 bug |
| 数学推导直觉 | 3 | 等差数列求和、大数 k 替代暴力 |

评分方法：
- 每项对照 solutions_batch.py 和 practice/ 中的实现
- 有 AC 记录 + 模板可默写 = 满分
- 有实现但不能独立默写 = 60%
- 仅看过模板 = 30%
- 完全未覆盖 = 0%

### 数学维度（/15 分）

基于 mistake_log.md 中数学类 Root Cause 修复率：
- 已修复条目数 / 总条目数 × 满分
- 加上微积分未测项的折扣（未测 = 假设 50%）

### AI/ML 维度（/25 分）

基于口述能力自评：
- 能 2 句话讲清核心概念 = 该项满分
- 能说出关键词但讲不清 = 60%
- 完全不会 = 0%

### 项目维度（/5 分）和后勤维度（/5 分）

用户自评，skill 不自动打分。

## 考前速查模式

当日期距离考试 ≤ 1 天时，报告自动切换为**考前速查模式**：
- 省略趋势分析，只输出"只看这些就够了"
- 错题清单只保留 Top 10 防错规则
- 知识点覆盖只列出 P0 缺口
- 今日必做清单精简为 3 项最高优先级

判断逻辑：
```
if today >= exam_date - 1:
    使用考前速查模式
else:
    使用完整报告模式
```

## 输出路径

| 输出内容 | 路径 | 说明 |
|---------|------|------|
| 自评打分 | `progress/study-planning/readiness-score.md` | 已有，保持不变 |
| 周期性复习总结 | `progress/reviews/review-YYYY-MM-DD.md` | 周期性 review 时写入 |
| 考前速查模式 | 对话中（不写文件） | 保持轻量 |
| 进度报告 | 对话中（不写文件） | 每次调用时即时生成 |

## Cross-References

- `choice-q-create` — 读取本 skill 识别的薄弱主题，调整出题重点
- `choice-q-drill` — 答题结束后可调用本 skill 生成 session 总结
- `algo-annotation` — 读取 mistake_log 中的防错规则，与本 skill 共享数据源
- `exam-assistant` — MCP 增强的经验检索，本 skill 纯本地
- `progress/exam-analysis/exam-style-analysis.md` — 出题风格、频率表、趋势预测（**新增核心数据源**）
- `progress/study-planning/readiness-score.md` — 本 skill 可更新自评分
- `progress/task-board/task-board.md` — 本 skill 读取任务状态
- `algorithms/mistake_log.md` — 核心错题数据源
- `progress/reviews/review-YYYY-MM-DD.md` — 周期性复习总结输出
- `algorithms/topic_checklist.md` — 知识点覆盖数据源
