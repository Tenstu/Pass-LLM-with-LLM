---
name: solve-skeleton
description: >
  Bare-bones Python solve() skeletons for AI Lab campus recruitment exam OJ problems.
  Use when the user asks for a solve() template, coding framework, OJ scaffold, or any of
  these Chinese trigger phrases: "解题框架", "解题模板", "solve骨架", "OJ模板", "ACM框架",
  "编程题结构", "solve()模板", "输入输出框架", "算法骨架", "解题规范", "代码模板", "框架代码",
  "答题模板", "刷题框架", "算法框架".
  Also use before starting any OJ problem implementation to provide the correct skeleton
  for the algorithm type. After the user fills in the TODOs, direct them to the
  `algo-annotation` skill for adding Chinese line-level comments.
  This skill provides structure only — no logic, no comments. For complete solutions,
  use `algorithms/python_oj_template.py` directly instead.
---

# Solve Skeleton Skill

Bare-bones Python solve() skeletons for ACM/OJ problems. No logic inside — only structure,
I/O plumbing, and TODO markers. After filling TODOs, use the `algo-annotation` skill to add
Chinese comments and `# [防错]` markers.

## 1. Core Convention

### I/O

```python
input = sys.stdin.readline
n = int(input())
nums = list(map(int, input().split()))
```

For strings: `s = input().strip()`. For output: `print(ans)` or `print("\n".join(out))`.
**Never** use `sys.stdin.buffer`, `iter(data) + next(it)`, or `.buffer.read().split()`.

### Stage Separator

Five dashes, 58 equal signs. No trailing content.

```
# ============================================================
```

### 5-Phase Structure

Every solve() follows this layout:

```
def solve():
    """Input format: ...
    Output format: ...
    """
    input = sys.stdin.readline

    # ============================================================
    # Preprocess
    # ============================================================

    # ============================================================
    # Algorithm
    # ============================================================

    # ============================================================
    # Output
    # ============================================================

if __name__ == "__main__":
    solve()
```

The docstring must state input and output format — this is the contract with the grader.

## 2. Anti-Pattern Checklist

Never do these when writing a skeleton. They cause WA/TLE that are hard to debug.

- **No `sys.stdin.buffer`** — returns bytes, requires `.decode()`, breaks on mixed string/numeric input.
- **No `input()` without alias** — bare `input()` is slow on large data; always `input = sys.stdin.readline`.
- **No `list.pop(0)`** in BFS — use `deque.popleft()` or you get O(n²) per pop.
- **No recursive `find()` in DSU** — Python recursion limit (~1000) causes RecursionError on deep chains. Use iterative find with path compression.
- **No missing 0-based conversion** — if input is 1-based, subtract 1 immediately after reading.
- **No `.strip()` omission on string reads** — `input().strip()` removes trailing `\n`; `input()` includes it.
- **No forgetting `if __name__ == "__main__"`** — some OJ platforms require the guard.
- **No stale heap entries in Dijkstra** — always skip with `if d != dist[u]: continue`.

## 3. Template Selection

Read the problem statement, match keywords, then copy the template from `references/`.

| Problem says... | Read this file |
|---|---|
| "shortest path", "grid", "maze", "min steps" | `references/algo-skeletons.md` §3a (BFS) |
| "connected", "traversal", "graph", "flood fill" | `references/algo-skeletons.md` §3b (DFS) |
| "merge", "disjoint sets", "union", "connected query" | `references/algo-skeletons.md` §3c (DSU) |
| "top K", "kth largest", "priority queue" | `references/algo-skeletons.md` §3d (Heap) |
| "weighted", "min cost", "non-negative edges" | `references/algo-skeletons.md` §3e (Dijkstra) |
| "range sum", "subarray sum", "interval query" | `references/algo-skeletons.md` §3f (Prefix Sum) |
| "subarray", "window", "fixed-length" | `references/algo-skeletons.md` §3g (Sliding Window) |
| "find boundary", "monotonic", "min/max satisfying" | `references/algo-skeletons.md` §3h (Binary Search) |
| "simulate", "state changes", "alternating" | `references/exam-patterns.md` §4a (State Machine) |
| "counter", "frequency", "tally", "count" | `references/exam-patterns.md` §4b (Counter) |
| "GCD merge", "coprime", "adjacent merge" | `references/exam-patterns.md` §4c (GCD Merge) |
| "modify string", "replace at position" | `references/exam-patterns.md` §4d (String Modify) |
| "bracket", "parentheses", "balanced", "valid" | `references/exam-patterns.md` §4e (Bracket Match) |
| "formula", "arithmetic", "prime", "modular" | `references/exam-patterns.md` §4f (Math Derivation) |
| None of the above — combine patterns or novel structure | Fallback: copy the 5-phase structure, fill Algorithm with raw loops + data structures |

### I/O Mode Selection

If the problem has multiple test cases or unusual input format, pick an I/O mode from
`references/io-modes.md` and replace the `input = sys.stdin.readline` line accordingly.

## 4. Workflow

1. **Read problem** — note input format, output format, constraint on n (determines O(n²) vs O(n log n)).
2. **Select template** — match keywords to the table above. Read only the relevant section from `references/`.
3. **Copy skeleton** — paste the template into the Algorithm phase. Keep all stage separators.
4. **Fill TODOs** — write only the missing logic. Do not add comments (algo-annotation does that later).
5. **Validate** — run the anti-pattern checklist. Confirm input/output matches the problem statement.
6. **Hand off** — once solve() is complete, invoke the `algo-annotation` skill for Chinese comments.

## 5. Cross-References

- `references/io-modes.md` — 5 I/O templates (single case, multi case, EOF, n-lines, grid)
- `references/algo-skeletons.md` — 8 algorithm templates with trigger keywords and complexity notes
- `references/exam-patterns.md` — 6 exam-specific patterns (simulation, stack GCD, bracket, etc.)
- `skills/algo-annotation.md` — adds Chinese line-level comments and `# [防错]` markers
- `algorithms/mistake_log.md` — WA patterns by topic; algo-annotation cross-references this
- `algorithms/python_oj_template.py` — utility function library (extended toolkit, not skeleton)
