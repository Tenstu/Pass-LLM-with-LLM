---
name: algo-annotation
description: >
  Use when the user pastes algorithm code and asks "what does this mean", "explain it",
  "add comments", "annotate", "why is it written this way", "how does this work",
  "walk me through this", "I don't get this logic", "this code is confusing",
  "teach me this algorithm", "what's going on here", or "break down this solution".
  Also use when the user shares a Python solve() function and wants a commented
  version with step-by-step reasoning — covers BFS/DFS, Dijkstra, DP, binary search,
  greedy, sliding window, union-find, heap, and backtracking in ACM/OJ style.
  Use when the user is stuck on a specific line or concept in contest-style code
  and needs both conceptual explanation and annotated code.
---

# Algorithm Annotation Skill

Generate detailed, learner-oriented annotations and explanations for ACM-style algorithm code.
The skill focuses on making the *why* visible, not just the *what*.

## Overview

When invoked, the skill produces annotated Python code with Chinese comments and, when needed,
natural-language explanations of algorithm logic. Annotations follow the repository's established
style: stage-separator comments, line-level Chinese comments, and `# [防错]` (pitfall) markers
linked to `algorithms/mistake_log.md`.

## Core Principles

Apply these principles when generating annotations or explanations.

1. Identify the user's specific confusion first — which line, which concept, what they find
   unintuitive. Do not dump full knowledge at once.
2. Explain algorithm logic in plain language before annotating code.
3. Distinguish the conceptual model from the code representation. State both and note
   that they describe the same thing from different perspectives.
4. Correct misconceptions precisely — name the exact step that is wrong and give the
   correct understanding. Avoid vague phrases like "you might be confused."
5. Close each explanation with a single sentence that captures the core invariant or trick.
6. Always cross-reference `algorithms/mistake_log.md` for the algorithm's known WA patterns
   and annotate relevant lines with `# [防错]`.

## Annotation Checklist

For every annotated code block, cover these elements where applicable:

- Data structure dual role — point out when a variable or array serves a second purpose
  (visited marker, sentinel, cache). Example: `dist[x][y]` stores distance, and `-1`
  simultaneously means "not yet visited."
- Boundary and initialization rationale — explain why the initial value is `inf`, `-1`,
  or `0` in context.
- Loop invariant — describe the property maintained by each iteration.
- Termination condition — explain why the condition guarantees a correct answer without
  missing cases.
- Common pitfalls — preempt typical beginner errors, pulling from `mistake_log.md`
  when entries exist for the algorithm.

## Algorithm Quick Reference

Reference this section to know which pitfalls and invariants apply to each pattern.

### BFS / Unweighted shortest path
- First visit yields shortest distance → `if dist[nx][ny] == -1` prevents re-enqueue.
- `deque` gives O(1) popleft vs O(n) for `list.pop(0)`.
- Direction arrays: `DIR4 = [(1,0),(-1,0),(0,1),(0,-1)]`.
- Queue distances are non-decreasing (loop invariant).
- Pitfalls: forgetting 0-based coordinate conversion; reversed boundary checks;
  initializing `dist` to `0` instead of `-1` so the start cell gets skipped.

### Dijkstra (weighted graph)
- Priority queue may hold stale entries → skip with `if d != dist[u]: continue`.
- Only enqueue when `nd < dist[v]`.
- Pitfalls: forgetting the stale-entry skip causes WA; using Dijkstra with negative
  edge weights (use Bellman-Ford or SPFA instead).

### DFS backtracking
- State restoration is mandatory: `path.pop()` / `used[i] = False`.
- Deep-copy results: `res.append(path[:])` to avoid later mutations.
- Pitfalls: forgetting to restore state corrupts sibling branches;
  Python recursion depth limit (~1000) causes RecursionError on deep trees.

### Dynamic programming
- Traversal order matters: forward for unbounded knapsack, reverse for 0/1 knapsack.
- 1D array space compression replaces `dp[i-1]` with `dp[j]` read in reverse.
- Pitfalls: missing base-case initialization; reversed state transition;
  0/1 knapsack traversed forward (allows repeated items).

### Binary search
- `lo <= hi` → closed interval; `lo < hi` → half-open.
- `mid = (lo + hi) // 2` with `lo = mid + 1` / `hi = mid - 1` to avoid infinite loops.
- Pitfalls: off-by-one from `mid` not advancing; `mid + 1` exceeding `hi` boundary.

### Sliding window
- Shrink condition must be explicit and correct in the `while` clause.
- Pitfalls: reversed inequality (`<` vs `<=`); wrong window length formula
  (`right - left + 1` vs `right - left`).

### Greedy
- Sort key must have a clear correctness argument.
- Pitfalls: choosing the wrong sort key (value vs ratio); skipping the proof of why
  local optimality implies global optimality.

### Union-Find (DSU)
- Path compression + union-by-size.
- `union` returns `True` for a new merge, `False` if already in the same set.
- Pitfalls: skipping path compression causes TLE; recursive `find` hits depth limit.

## Workflow

Follow these steps in order for each annotation request.

1. Pinpoint the confusion. Read the user's message and the code. Identify which line or
   concept they are asking about.
2. Explain the algorithm logic in plain language, without referencing code identifiers.
3. Annotate the code. Apply the Annotation Checklist to the code. Use the Algorithm
   Quick Reference for algorithm-specific points. Use `#` for Python comments.
4. Trace a small example manually when the logic is non-trivial. Show the state after
   each significant step.
5. Summarize in one sentence — the core invariant, trick, or key insight.
6. Cross-reference `algorithms/mistake_log.md`. If the algorithm has recorded WA patterns,
   add `# [防错]` annotations to the relevant lines. If no entry exists, proceed without
   forcing a pitfall note.

## Annotation Format

```python
# ---------- 1. Stage name ----------

# Stage-level explanation of what happens here and why.

dist[x][y] = 0                # Start cell: distance to itself is 0
dist = [[-1] * m for _ in range(n)]  # [双重角色] stores distance AND unvisited flag

if d != dist[u]:              # [防错] stale entry in heap — skip to avoid WA
    continue
```

- Use `# ---------- N. Stage ----------` as stage separators.
- Line comments explain both the action and the rationale.
- Tag dual-role data with `# [双重角色]` and pitfall guards with `# [防错]`.
- Keep comment language in Chinese to match the repository convention.
