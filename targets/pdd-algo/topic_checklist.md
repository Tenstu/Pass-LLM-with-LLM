# Algorithm Topic Checklist

> **优先级定义**：P0/P1/P2 优先级标准见 `progress/exam-analysis/exam-style-analysis.md` §4.1。本文件仅追踪各 topic 的覆盖状态。

## P0 Must Practice First

| Topic | Why It Matters | AC Standard |
|---|---|---|
| Hash / dict / set | 高频统计、去重、两数关系 | 20 分钟内写出 |
| Sorting | 贪心、双指针、区间题基础 | 能解释排序 key |
| Binary Search | 边界与二分答案常见 | 能写 `lower_bound` |
| Prefix Sum | 区间和、计数、差分基础 | 会结合哈希 |
| Sliding Window | 字符串和子数组高频 | 左右指针条件清楚 |
| Two Pointers | 排序数组、去重、合并 | 不漏边界 |

## P1 Need Solid Coverage

| Topic | Why It Matters | AC Standard |
|---|---|---|
| Greedy | 中等题常见 | 能说出局部选择 |
| BFS / DFS | 图、树、网格 | visited 时机正确 |
| Heap / Top-K | 排名、调度、流式数据 | 会用 `heapq` |
| Simple DP | 一维/二维基础 | 状态定义清晰 |
| String Processing | 输入、匹配、计数 | 注意下标和空串 |

## P2 Optional If Time Allows

| Topic | Why It Matters | AC Standard |
|---|---|---|
| Union Find | 连通性题 | 会路径压缩 |
| Monotonic Stack | 下一个更大/更小 | 识别模板 |
| Backtracking | 组合枚举 | 会剪枝 |
| Difference Array | 区间增减 | 会还原前缀 |

## Daily Target

- Minimum: 3 problems/day.
- Good: 4-5 problems/day.
- Mock day: 3-4 problems in one timed block.

## Pattern Recognition Prompts

- 能排序吗？
- 需要快速查找过去状态吗？
- 区间问题能不能前缀和？
- 连续子数组是否适合滑窗？
- 答案是否具有单调性？
- 图/网格是否要 BFS 最短路？
- 最优选择能否贪心证明？

## 编程题高频模式总览

| 模式 | 出现频次 | 代表题目 | 核心 invariant | 最小模板行数 |
|------|----------|----------|----------------|-------------|
| 模拟 + 映射 | ★★★★★ | LED、扩散 | 预计算→查表→累加 | 10 |
| 模拟 + 状态机 | ★★★★ | 扩散字符串 | boolean 状态 + 奇偶分支 | 20 |
| 模拟 + 计数器 | ★★★★ | 榨汁机 | 空时不计数 + 末尾补一次 | 15 |
| 栈 + GCD | ★★★ | 栈中熔合 | gcd 值递减，while 循环检查 | 20 |
| 数学推导 + 公式 | ★★★ | 循环指令糖果 | 不能真循环 k 次，用三角形数 | 25 |
| 字符串 + 栈 | ★★★ | 括号匹配 | 栈空匹配，结束栈空 | 15 |
| 字符串修改 | ★★★ | 按下标修改 | 转 list，注意 0-based | 10 |
| 模拟 + 博弈 | ★★★ | 井字棋 | 每步检查合法性 + 终局 | 30 |
| 贪心 + 排序 | ★★★ | 能力观赏 | 降序 + ceil(n/2) | 20 |
| 数论 + 质因数 | ★★★ | 质因子分解 | 试除到 √n，检查因子存在性 | 25 |
| MEX + 滑窗 | ★★ | mex 计数 | mex ≥ v ⇔ 含 [0,v-1] | 30 |
| 子串匹配 + 环形距离 | ★★ | 字母环变换 | 枚举对齐 + min(diff, 26-diff) | 20 |

