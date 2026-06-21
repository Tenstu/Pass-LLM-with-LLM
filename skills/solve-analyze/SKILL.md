---
name: solve-analyze
description: >
  Use when the user pastes their own solve() code and asks "分析一下我的代码",
  "帮我看看哪里错了", "对比一下", "review my solve", "check my code",
  "看看我的解法", "为什么WA", "为什么超时", "解法对比", "代码诊断".
  Also use when the user shares a completed solve() and wants a structured
  comparison against the standard template solution, root cause diagnosis,
  and automatic feedback to mistake_log / user_profile / exam-memory.
  This skill sits between solve-skeleton and algo-annotation in the pipeline:
  it diagnoses what went wrong, not how to annotate or how to build a skeleton.
  Handles both WA/TLE (full diagnosis) and AC code (lightweight style check).
---

# Solve Analyze Skill

Structured diagnosis layer that compares a user's solve() against a standard solution generated
by the solve-skeleton pipeline. Produces a side-by-side diff report, identifies root cause tags,
and triggers feedback loops into mistake_log, user_profile, and exam-memory MCP.
This skill does not teach and does not build skeletons -- it diagnoses "what you wrote vs
what you should have written."

## 1. Overview

### Pipeline Position

```
solve-skeleton (template)
  -> user fills logic
    -> ** solve-analyze (diagnosis) **   <-- this skill
      -> algo-annotation (# [防错] markers)
      -> mistake_log (error record)
      -> user_profile (weakness tracking)
      -> choice-q-create (targeted question generation)
```

### Purpose

When a user completes a solve() function and wants to know what went wrong, this skill:

1. Performs a quick triage to determine report depth (full diagnosis vs lightweight style check).
2. Statically analyzes the user's code for logic errors, anti-patterns, and suspicious lines.
3. Generates a reference solution via the solve-skeleton pipeline.
4. Produces a structured comparison report highlighting every meaningful difference.
5. Extracts root cause tags and feeds them back into the harness feedback loops.

The output is actionable: each identified issue maps to a specific root cause tag, a suggested
fix, and an automatic (or user-confirmed) write to the error tracking system.

### What This Skill Does NOT Do

- Does not provide algorithmic tutorials or conceptual explanations (use `algo-annotation`).
- Does not generate skeletons or templates (use `solve-skeleton`).
- Does not create choice questions (use `choice-q-create`, which reads mistake_log downstream).

## 2. Core Principle

Two parallel analysis paths that merge into a single comparison report:

```
                  +------------------------+
                  |   User's solve() code   |
                  +-----------+------------+
                              |
                  +-----------v------------+
                  |   solve-analyze Skill   |
                  +-----------+------------+
                              |
              +---------------+----------------+
              v                                v
   Agent A: Static Analysis          Agent B: Standard Solution
   - Line-by-line logic review       - Select template from
   - Identify algorithm pattern        solve-skeleton section 3
   - Mark suspicious lines           - Fill TODOs with correct logic
   - Check anti-patterns from        - Run anti-pattern checklist
     solve-skeleton section 2          from solve-skeleton section 2
   - Match known error patterns        (references/exam-patterns.md,
     from mistake_log.md               references/algo-skeletons.md)
              |                                |
              +----------------+---------------+
                               v
                     Comparison Report
                               |
              +----------------+----------------+
              v                 v                v
         mistake_log      user_profile     experience MCP
```

Agent A and Agent B run in parallel. Agent A reads the user's code directly. Agent B generates
the standard solution by invoking the solve-skeleton workflow internally (template selection,
TODO filling, anti-pattern validation). The merge step produces a structured diff of every
meaningful divergence between the two paths.

## 3. Workflow

Follow these six steps in order for every solve-analyze request.

### Step 1: Read User Code and Problem Statement

Collect from the user:
- Their `solve()` code (Python, ACM/OJ style).
- The problem statement or a reference to it (problem number, link, or description).

If the problem statement is missing, ask the user for it before proceeding.
Without the problem statement, Agent B cannot generate a correct standard solution.

### Step 2: Identify Algorithm Pattern

Read the user's code and match it to the template table in
`solve-skeleton/SKILL.md` section 3 (Template Selection). The pattern determines:

- Which skeleton template Agent B will use.
- Which anti-pattern checklist to apply.
- Which root cause tag set is most likely relevant.

| User code contains... | Pattern | Skeleton source |
|---|---|---|
| BFS with deque, grid, distance array | BFS | `skills/solve-skeleton/references/algo-skeletons.md` section 3a |
| DFS with visited set, recursion stack | DFS | `skills/solve-skeleton/references/algo-skeletons.md` section 3b |
| parent[] array, union/find operations | DSU | `skills/solve-skeleton/references/algo-skeletons.md` section 3c |
| heapq, heappush/heappop | Heap | `skills/solve-skeleton/references/algo-skeletons.md` section 3d |
| weighted edges, dist[], priority queue | Dijkstra | `skills/solve-skeleton/references/algo-skeletons.md` section 3e |
| prefix sum array, range query | Prefix Sum | `skills/solve-skeleton/references/algo-skeletons.md` section 3f |
| two pointers (left/right), window | Sliding Window | `skills/solve-skeleton/references/algo-skeletons.md` section 3g |
| lo/hi/mid, monotonic condition | Binary Search | `skills/solve-skeleton/references/algo-skeletons.md` section 3h |
| state transitions, simulation loop | State Machine | `skills/solve-skeleton/references/exam-patterns.md` section 4a |
| Counter, frequency dict | Counter | `skills/solve-skeleton/references/exam-patterns.md` section 4b |
| GCD, adjacent merge | GCD Merge | `skills/solve-skeleton/references/exam-patterns.md` section 4c |
| string replace at index | String Modify | `skills/solve-skeleton/references/exam-patterns.md` section 4d |
| stack, bracket matching | Bracket Match | `skills/solve-skeleton/references/exam-patterns.md` section 4e |
| modular arithmetic, formula | Math Derivation | `skills/solve-skeleton/references/exam-patterns.md` section 4f |
| None of the above | Fallback | 5-phase structure, raw loops |

If the user's code does not cleanly match a single pattern, note the closest match
and proceed with that template. Mixed patterns are common in exam problems.

### Step 2.5: Triage — Determine Report Depth

Before launching parallel agents, perform a quick triage to avoid over-diagnosing AC code.

**Triage checklist** (run Agent A's static analysis first, lightweight):

1. Check anti-patterns from `solve-skeleton/SKILL.md` section 2 — any violations?
2. Check logic correctness — are the core algorithm steps sound?
3. Check complexity — is the approach O(...) within problem constraints?
4. Check convention — does the code follow solve-skeleton I/O and structure norms?

**Routing decision:**

```
Triage result                    → Report depth          → Skip to
─────────────────────────────────────────────────────────────────────
Logic errors / WA suspected      → Full diagnosis        → Step 3 (parallel agents)
TLE / complexity issues          → Full diagnosis        → Step 3 (parallel agents)
Anti-patterns that risk WA       → Full diagnosis        → Step 3 (parallel agents)
AC + only convention deviations  → Lightweight style check → Step 3-lite (below)
AC + no issues found             → Lightweight style check → Step 3-lite (below)
```

**When the user explicitly states "WA" or "TLE" or pastes error output, always use full
diagnosis regardless of triage result.** The triage only applies when the user's code
status is unknown or the user asks for a general review.

### Step 3: Launch Parallel Analysis (Full Diagnosis Path)

Run two analysis tracks concurrently. **Only used when triage routes to full diagnosis.**

**Agent A -- Static Analysis of User Code:**

1. Read the user's solve() line by line.
2. For each section (Preprocess, Algorithm, Output), identify what the code does and flag
   suspicious logic.
3. Cross-check against the anti-pattern checklist in `solve-skeleton/SKILL.md` section 2:
   - `sys.stdin.buffer` usage (bytes vs string confusion)
   - Missing `input = sys.stdin.readline` alias
   - `list.pop(0)` in BFS instead of `deque.popleft()`
   - Recursive `find()` in DSU (recursion depth risk)
   - Missing 0-based conversion for 1-based input
   - Missing `.strip()` on string reads
   - Missing `if __name__ == "__main__"` guard
   - Stale heap entries in Dijkstra (missing `if d != dist[u]: continue`)
4. Cross-check against `targets/{target}/mistake_log.md` for known WA/TLE patterns in the same
   algorithm topic.
5. Mark each suspicious line with a line reference and a preliminary root cause tag.

**Agent B -- Standard Solution Generation:**

1. Use the pattern identified in Step 2 to select the correct skeleton template from
   `solve-skeleton/references/`.
2. Fill in the TODO markers with correct logic for the given problem.
3. Run the anti-pattern checklist from `solve-skeleton/SKILL.md` section 2 against the
   generated solution.
4. The result is a complete, correct solve() function for the same problem.

### Step 4: Merge into Comparison Report

Combine Agent A and Agent B outputs into a structured comparison report.
Use the template defined in `references/comparison-template.md`.

The report must include:

- **Basic info**: problem reference, identified pattern, user code status estimate
  (WA / TLE / AC-with-risk / OK).
- **Side-by-side diff table**: for each meaningful region, show the user's approach vs
  the standard approach, with a difference type label (missing logic, wrong order,
  wrong condition, unnecessary code, complexity issue, etc.).
- **Suspicious lines**: numbered references to the user's original code with one-line
  explanations.
- **Root cause tags**: extracted in Step 5.
- **Suggested fixes**: specific, line-level corrections the user can apply.

Do not include trivial style differences (variable naming, whitespace). Focus only on
differences that affect correctness or complexity.

### Step 5: Extract Root Cause Tags

From the comparison report, extract one or more root cause tags matching the definitions
in `references/root-cause-tags.md`. Each tag must have:

- A short identifier (e.g., `order_dependency`, `off_by_one`).
- A one-line description of how it manifests in the user's code.
- A reference to the specific line range in the user's code.

If a user's error does not match any existing tag, use `misc_logic` as the fallback tag
and note that a new tag should be added to the root cause tag library.

### Step 6: Trigger Feedback Loops

After the comparison report is complete, execute the feedback loops described in section 5 below.
Report the status of each feedback action to the user at the end of the comparison report
(see the "Automatic Feedback Actions" section in `references/comparison-template.md`).

### Step 3-lite: Lightweight Style Check (AC Fast Path)

**Used when triage routes to lightweight check** — code is AC with only convention/style deviations.

This path skips parallel agent dispatch and produces a condensed summary instead of a full
diagnosis report. The goal is to quickly identify what the user should fix for consistency,
then hand off to `algo-annotation` for `# [防错]` markers.

**Process:**

1. List convention deviations in a compact table (same as full report but limited to this section).
2. Confirm logic is correct — one sentence, no deep analysis.
3. Skip root cause tag extraction (no errors to tag).
4. Skip all feedback loops (no mistake_log / MCP writes for AC code).
5. Offer handoff to `algo-annotation` for adding `# [防错]` markers based on the algorithm topic.

**Output format:**

```markdown
## 解题快速检查

### 基本信息
- **题目**：{{problem_reference}}
- **识别模式**：{{algorithm_pattern}}
- **用户解法状态**：AC（逻辑正确）

### 骨架规范差异

| 区域 | 用户写法 | 标准写法 | 差异类型 | 严重度 |
|------|----------|----------|----------|--------|
{{convention_diff_rows}}

### 结论

逻辑正确，可直接 AC。差异仅在 solve-skeleton 编码规范层面。

### 下一步建议

- invoke `algo-annotation` — 为代码添加 `# [防错]` 标记和中文行级注释
- 按骨架规范重写 — 使用 5-phase 结构 + readline 别名（可选，不影响 AC）
```

**When NOT to use the fast path:**
- User explicitly says "WA", "TLE", "超时", "答案错误"
- User pastes error output or failing test case
- Triage found anti-patterns that could cause WA on edge cases
- User asks "哪里错了" (implies something is wrong)

## 4. Input / Output Specification

### Input

The user provides:
- Their `solve()` code as a Python code block or plain text.
- The problem statement (full text, problem number, or a reference the skill can resolve).

Optional context the user may provide:
- Which test case failed (WA on sample 3, TLE on large input, etc.).
- Their own hypothesis about what is wrong.

### Output

A structured comparison report in markdown, following the template in
`references/comparison-template.md`. The report is self-contained and does not require
the user to read any other file to understand the diagnosis.

The report ends with a summary table of feedback actions taken:

```markdown
### Automatic Feedback Actions

| Action | Target | Status |
|--------|--------|--------|
| mistake_log append | `targets/{target}/mistake_log.md` | Done / Skipped |
| user_profile update | MCP `mcp__exam-memory__update_user_profile` | Done / Skipped (MCP unavailable) |
| experience check | MCP `mcp__exam-memory__list_experiences` | Match found (inc) / New (asked user) / Skipped |
```

## 5. Feedback Loop Integration

This is the core value of solve-analyze: turning diagnosis into persistent improvement signals
across the entire harness.

### 5a. -> mistake_log.md (Automatic)

Root cause tags are appended to `targets/{target}/mistake_log.md` under the matching topic section.

**Append logic:**

1. Find the topic section in mistake_log.md that matches the algorithm type (e.g.,
   "## 滑动窗口", "## BFS / 无权最短路"). If no matching section exists, create one
   following the existing format.
2. Append a new row to the table with these fields:

| Field | Value |
|-------|-------|
| Date | Today's date (MM-DD format) |
| Problem | Problem reference from the user's input |
| Topic | Algorithm topic name |
| Result | `WA` for logic errors, `TLE` for complexity issues, `AC(with risk)` for anti-patterns that pass but are fragile |
| Mastery | `WA` for new errors (matching existing convention) |
| Root Cause | The extracted root cause tag identifier |
| Fix Rule | One-line fix description from the comparison report |
| Redo Date | Today + 1 day (default redo interval) |

3. Check if a `### 防错规则：...` line already exists for this root cause tag under the
   same topic section. If not, append one with the fix rule description.
4. Update the "## Root Cause 汇总" table at the top: increment the count for the matching
   tag, or add a new row if the tag is not yet present.

**Deduplication:** Before appending, scan the existing rows in the topic section. If a row
with the same Problem reference already exists, do not duplicate it. Instead, update the
existing row's Mastery field if the new analysis provides additional information.

### 5b. -> user_profile (Automatic via MCP)

Update the user's profile to reflect the identified weakness.

1. Call `mcp__exam-memory__update_user_profile()` with:
   - `weaknesses`: increment the count for the algorithm topic identified in Step 2.
2. After updating, check the user_profile for this topic's weakness count. If the same
   root cause tag has appeared in 3 or more different problems, mark it as a
   `persistent_weakness` in the profile.
3. If the MCP call fails or the MCP server is unavailable, skip silently. Do not report
   an error to the user.

### 5c. -> exam-memory MCP (Needs User Confirmation)

Check whether the identified error pattern already exists in the experience database.

1. Call `mcp__exam-memory__list_experiences(type="算法")` to search for matching
   experiences by topic and knowledge area.
2. **If a matching experience is found**: call `mcp__exam-memory__inc_error_count()` to
   increment the error count for that experience. This is automatic and does not require
   user confirmation.
3. **If no matching experience is found** (new pattern): ask the user:
   "是否将此错误模式存入经验库？" On user confirmation, call
   `mcp__exam-memory__save_experience()` with the experience details
   (title, content, type="算法", knowledge=topic name).
4. If the MCP server is unavailable, skip silently. Do not report an error to the user.

### 5d. -> choice-q-create (Indirect)

No direct MCP call is needed. After writing to mistake_log.md (step 5a), the
`choice-q-create` skill automatically reads mistake_log.md in its next session to
prioritize weak topics. The feedback happens passively through the shared file.

### 5e. -> algo-annotation (Downstream)

After the solve-analyze report is produced, the user can invoke `algo-annotation` to add
`# [防错]` markers to their code. The root cause tags and fix rules from the solve-analyze
report directly inform which `# [防错]` lines to add and where.

To facilitate this handoff, the comparison report should include a section at the end
listing the recommended `# [防错]` annotations in the format expected by algo-annotation:

```markdown
### Recommended # [防错] Annotations

- Line XX: `# [防错] <fix rule description>`
- Line YY: `# [防错] <fix rule description>`
```

The user can then invoke algo-annotation and reference this section, or the agent can
automatically offer to invoke algo-annotation after the report is delivered.

## 6. Cross-References

| File | Relationship | Usage |
|------|-------------|-------|
| `skills/solve-skeleton/SKILL.md` | Upstream | Template selection logic (section 3), anti-pattern checklist (section 2), 5-phase structure (section 1) |
| `skills/solve-skeleton/references/algo-skeletons.md` | Upstream | 8 algorithm templates used by Agent B to generate standard solutions |
| `skills/solve-skeleton/references/exam-patterns.md` | Upstream | 6 exam-specific patterns used by Agent B when standard algo templates do not match |
| `skills/solve-skeleton/references/io-modes.md` | Upstream | I/O mode templates for generating correct input/output in the standard solution |
| `skills/algo-annotation.md` | Downstream | Adds `# [防错]` markers to code using root cause tags from this skill's report |
| `targets/{target}/mistake_log.md` | Feedback target | Error patterns by topic; this skill appends new entries and updates root cause summary |
| `skills/solve-analyze/references/root-cause-tags.md` | Internal | Root cause tag definitions and matching rules |
| `skills/solve-analyze/references/comparison-template.md` | Internal | Markdown template for the structured comparison report |

## 7. MCP Dependency Matrix

| MCP Tool | Required? | Graceful Degradation |
|----------|-----------|---------------------|
| `mcp__exam-memory__list_experiences` | Optional | Skip experience matching; report "MCP unavailable" in feedback summary |
| `mcp__exam-memory__save_experience` | Optional | Skip persistence; user's error pattern remains in mistake_log only |
| `mcp__exam-memory__inc_error_count` | Optional | Skip frequency tracking; error count stays stale |
| `mcp__exam-memory__update_user_profile` | Optional | Skip profile update; weakness data not recorded |

**Rules:**

- All MCP calls use the full prefix `mcp__exam-memory__<tool_name>`.
- On any MCP failure (connection refused, timeout, tool not found), degrade silently.
  Do not report MCP errors as skill failures to the user.
- The comparison report and mistake_log write are the primary deliverables.
  MCP persistence is a secondary enhancement.
- If the MCP server is completely unavailable, the skill still produces a complete
  diagnosis report. The only lost signal is cross-session persistence.

**MCP Pre-flight Check:**

Before attempting any MCP call, verify availability:
1. Check if `mcp__exam-memory__*` tools appear in the available tool list.
2. If not listed → MCP is unavailable for this session. Skip all MCP steps silently.
3. Do NOT attempt MCP calls that will fail — this wastes time and clutters output.

**MCP Unavailable — Execution Summary:**

When MCP is unavailable, the skill still runs all local steps:

| Step | MCP Available | MCP Unavailable |
|------|--------------|-----------------|
| Parallel analysis (Agent A + B) | Runs normally | Runs normally |
| Comparison report | Full report | Full report |
| Root cause tag extraction | Runs normally | Runs normally |
| mistake_log.md write | Automatic | Automatic (local file) |
| user_profile update | `mcp__exam-memory__update_user_profile` | **Skipped silently** |
| Experience matching | `mcp__exam-memory__list_experiences` | **Skipped silently** |
| Error count increment | `mcp__exam-memory__inc_error_count` | **Skipped silently** |
| New experience save | `mcp__exam-memory__save_experience` (with user confirm) | **Skipped silently** |

The only observable difference is the feedback summary table at the end of the report:
all MCP actions show "Skipped (MCP unavailable)" instead of "Done".
