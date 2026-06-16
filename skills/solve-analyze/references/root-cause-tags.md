# Root Cause Tag Library

> solve-analyze skill 的根因标签库。分析报告中引用这些标签来分类错误根因。
> 标签与 `algorithms/mistake_log.md` 的 Root Cause 列对齐。
> 新增标签需同步更新本文件和 comparison-template.md 的标签说明。
> 创建日期：2026-06-16 | 基于 mistake_log.md 23 条实际错误提取

---

## Tag Registry

| Tag | Display Name | 含义 | 常见场景 | 严重度 | 建议动作 |
|-----|-------------|------|----------|--------|----------|
| `pattern` | 题型模式盲区 | 看到题型不知道怎么下笔，缺乏标准解题模板 | 行列式乘法、贝叶斯公式、CNN感受野递推、KV Cache公式、RAG流程排序 | High | 整理该题型的标准解题模板，反复练习同类题 |
| `proof` | 概念/性质记混 | 概念记混或性质记错，知识理解有偏差 | 对称矩阵逆性质、独立vs不相关、位置编码添加方式、缩放因子作用、GAT多头策略、FlashAttention机制 | High | 回归定义，用对比表厘清易混概念，写防错规则 |
| `python` | 数值/常识记错 | 数值型知识点记忆不准确 | 正态分布 68-95-99.7 法则的具体数值 | Medium | 整理常考数值速查表，考前集中复习 |
| `order_dependency` | 操作顺序依赖错误 | 代码中操作顺序与正确逻辑不一致 | 滑窗先减后判断 vs 先判断后减；更新状态与边界判断顺序颠倒 | High | 用注释标注每步的前置条件，再决定顺序 |
| `off_by_one` | 边界偏移 | 索引或区间边界差 1 | 数组索引越界、区间开闭混淆 `[0,n)` vs `[0,n]`、循环终止条件 `< n` vs `<= n` | Medium | 画索引图辅助判断，统一使用左闭右开 |
| `missing_boundary` | 边界条件缺失 | 未处理特殊输入或边界情况 | 空输入、单元素数组、n=0、全负数、k > len | Medium | 写完主体逻辑后单独检查：空/0/1/满/溢 |
| `wrong_complexity` | 复杂度不达标 | 算法时间/空间复杂度超出题目限制 | 嵌套循环 O(n^2) 应为 O(n)；未用前缀和/单调队列优化 | High | 先估算复杂度再写代码，不达标时换算法思路 |
| `missing_dedup` | 去重遗漏 | 排序或遍历后未跳过重复元素 | 排序后相邻相同未跳过；集合类问题未去重导致重复结果 | Medium | 排序后立刻写 `while i < n and nums[i] == nums[i-1]: i += 1` |
| `type_mismatch` | 类型处理错误 | 变量类型混用或转换遗漏 | int/str 拼接报错；整除 `/` vs `//`；浮点精度问题 | Low | 写类型注解；关键运算后 `assert type(x)` |
| `infinite_loop` | 死循环 | 循环条件不收敛导致无限循环 | while 条件永远为真；递归无终止条件；指针未移动 | High | 写循环时同时写终止断言；递归加 depth 保护 |
| `greedy_fallacy` | 贪心不成立 | 误用贪心策略，局部最优非全局最优 | 区间调度排序键错误；背包问题用贪心；活动选择反例 | High | 先证明贪心性质或举反例，无法证明则换 DP |

---

## Per-Tag Detail

### `pattern` — 题型模式盲区

**含义**: 看到某种题型不知道怎么下笔，缺乏该题型的标准解题模板或公式
**典型场景**:
1. 行列式乘法：不知道 `det(AB) = det(A)det(B)`，无从下手计算 `det(A^2)`
2. CNN 感受野：不知道递推公式 `RF = RF_prev + (k-1)*stride`，凭直觉猜 n^2
3. KV Cache 显存：不知道完整公式 `2 * layers * heads * head_dim * seq_len * bytes`，漏乘 K+V 或层数
4. RAG 流程排序：不知道标准流程 Chunk -> Embed -> Retrieval -> Rerank -> LLM，顺序搞混
5. 贝叶斯公式：只看分子 P(B|A)P(A)，忘了除以分母 P(B)
**检测规则**: 用户代码缺少该题型的核心公式/步骤；逻辑框架与标准解法差异 > 50%；用户自述"不知道怎么写"
**建议修正**: 整理该题型的标准解题模板（公式 + 步骤），写入防错规则，反复练习同类变体题
**关联算法主题**: 线性代数、概率统计、CNN 感受野、KV Cache 计算、RAG 架构、推理优化

### `proof` — 概念/性质记混

**含义**: 对某个概念的性质理解有偏差，记混了两个相似但不同的概念，或记错了关键性质
**典型场景**:
1. 独立 vs 不相关：记混方向 —— 独立 => 不相关（对），不相关 => 独立（错）。E[X+Y]=E[X]+E[Y] 不需要独立，Var(X+Y)=Var(X)+Var(Y) 需要独立
2. 正交 vs 正定：正交矩阵特征值模为1但可含复数（旋转 e^{i*theta}），正定矩阵特征值才全正实数
3. 过平滑 vs 过拟合：GNN 过平滑是节点表征趋同（表达力退化），不是过拟合
4. GAT 多头策略：中间层用 concat，输出层用 mean，不是全 concat
5. FlashAttention vs KV Cache：FlashAttention 改 IO 模式（tiling），不改 KV Cache 大小；KV Cache 减小靠 GQA/MQA
6. 位置编码：只在输入层加一次，不是每层都有；LayerNorm 才是每层都有
**检测规则**: 用户代码/选项中的概念使用与定义不符；混淆两个相似术语；声称某性质成立但实际不成立
**建议修正**: 制作易混概念对比表（概念A vs 概念B），写入防错规则，考前重点复习
**关联算法主题**: 线性代数（矩阵性质）、概率统计（独立性）、Transformer（位置编码、缩放因子）、GNN（GAT/GCN）、推理优化（FlashAttention、LoRA）

### `python` — 数值/常识记错

**含义**: 对具体数值或常识性知识点记忆不准确
**典型场景**:
1. 正态分布：68-95-99.7 法则记混，P(|X|>1) 约 0.32 而非 0.05，P(X>2) 约 0.0228 而非 0.05
2. （潜在）常见数学常数、对数近似值记错
3. （潜在）模型参数量级估算偏差（如 BERT-base 110M、GPT-2 1.5B）
**检测规则**: 用户写的数值与标准值偏差 > 10%；声称某数值近似但实际偏差较大
**建议修正**: 整理常考数值速查表（分布表、常数、参数量），考前 30 分钟快速过一遍
**关联算法主题**: 概率统计（分布表）、机器学习（模型参数量）、数学常数

### `order_dependency` — 操作顺序依赖错误

**含义**: 代码中多个操作的执行顺序与正确逻辑不一致，导致状态计算错误
**典型场景**:
1. 滑动窗口：先执行 `cnt[out_val] -= 1` 再判断窗口是否合法，应先判断再减
2. 前缀和：先累加再减去左边，与先减再累加结果不同
3. BFS/DFS：入队标记 vs 出队标记访问，顺序影响正确性
**检测规则**: 代码中存在连续的状态修改语句；修改顺序与标准解法不一致；调换顺序后结果正确
**建议修正**: 用注释标注每步操作的前置依赖关系；画状态转移图确认顺序
**关联算法主题**: 滑动窗口、BFS/DFS、前缀和、动态规划状态转移

### `off_by_one` — 边界偏移

**含义**: 索引或区间边界差 1，导致少算或多算一个元素
**典型场景**:
1. 循环边界：`for i in range(n)` vs `for i in range(n+1)`，少处理/多处理一个
2. 区间开闭：题目说 `[l, r]` 闭区间，代码写成 `[l, r)` 半开区间
3. 数组索引：`nums[n]` 越界，应为 `nums[n-1]`
**检测规则**: 循环边界与题目区间定义不一致；结果比正确答案少1或多1个元素；数组越界异常
**建议修正**: 统一使用左闭右开 `[0, n)` 风格；画索引图辅助判断；用 `assert` 检查边界
**关联算法主题**: 二分查找、滑动窗口、数组遍历、树遍历

### `missing_boundary` — 边界条件缺失

**含义**: 未处理特殊输入或边界情况，导致空输入崩溃、单元素异常等
**典型场景**:
1. 空输入：未检查 `len(nums) == 0` 直接访问 `nums[0]`
2. 单元素：`n == 1` 时循环不执行，返回值未初始化
3. 特殊值：`n == 0`、`k == 0`、全负数、k > len 等极端情况
**检测规则**: 代码缺少输入合法性检查；没有处理空/0/1 的分支；在极端输入下崩溃或返回错误值
**建议修正**: 写完主体逻辑后逐项检查：空、0、1、满、溢 五种边界
**关联算法主题**: 数组、链表、树、递归

### `wrong_complexity` — 复杂度不达标

**含义**: 算法的时间或空间复杂度超出题目限制，导致 TLE 或 MLE
**典型场景**:
1. 嵌套循环：两层 `for` 遍历 O(n^2)，但题目要求 O(n) —— 应用滑动窗口或双指针
2. 暴力搜索：未用前缀和/哈希表优化，重复计算子区间和
3. 未优化数据结构：用列表做频繁查找 O(n) 应换哈希表 O(1)
**检测规则**: 嵌套循环层数 > 题目复杂度允许；重复计算相同子问题；结果 TLE
**建议修正**: 先估算复杂度再写代码；不达标时换思路（哈希表/双指针/单调栈/前缀和）
**关联算法主题**: 滑动窗口、前缀和、哈希表、单调栈/队列、动态规划

### `missing_dedup` — 去重遗漏

**含义**: 排序或遍历后未跳过重复元素，导致结果包含重复项或计算多余
**典型场景**:
1. 排序后遍历：相邻元素相同未跳过，导致子集/排列结果重复
2. 两数之和变体：排序双指针未跳过重复值
3. 组合问题：同层递归未去重
**检测规则**: 排序后代码中没有 `while i < n and nums[i] == nums[i-1]` 跳过逻辑；输出包含重复结果
**建议修正**: 排序后立即在遍历中加入去重 `while`；组合/排列问题用 `used` 数组或排序去重
**关联算法主题**: 回溯（子集/排列/组合）、双指针、排序后遍历

### `type_mismatch` — 类型处理错误

**含义**: 变量类型混用或类型转换遗漏，导致计算结果错误或运行时报错
**典型场景**:
1. 整除混淆：Python 中 `/` 返回 float，`//` 返回 int，结果不同
2. 字符串与数字：`str + int` 拼接报错，应先 `str(int)`
3. 浮点精度：`0.1 + 0.2 != 0.3`，应使用 `math.isclose()`
**检测规则**: 运算结果类型与预期不符；出现 TypeError；浮点比较用 `==` 而非 `math.isclose()`
**建议修正**: 写类型注解；关键运算后 `assert isinstance(x, expected_type)`；浮点用 `math.isclose()`
**关联算法主题**: 数学计算、字符串处理、Python 特性

### `infinite_loop` — 死循环

**含义**: 循环条件不收敛或递归无终止条件，导致程序无限运行
**典型场景**:
1. while 条件：`while left < right` 但 `left` 或 `right` 未更新
2. 递归：缺少 base case 或递归参数未趋近终止值
3. 指针移动：快慢指针在某些输入下停滞不动
**检测规则**: 循环体内没有修改循环变量的语句；递归缺少终止条件；程序运行超时无输出
**建议修正**: 写循环时同步写终止断言（如 `assert steps < max_steps`）；递归加 depth 保护
**关联算法主题**: 双指针、二分查找、递归、图遍历

### `greedy_fallacy` — 贪心不成立

**含义**: 误用贪心策略，局部最优选择不能保证全局最优
**典型场景**:
1. 区间调度：按开始时间排序贪心选，应按结束时间排序
2. 背包问题：按性价比贪心选，分数背包可行但 0-1 背包不行
3. 活动选择：反例存在，如先选最短的活动反而阻塞更多
**检测规则**: 贪心策略在某些输入下得到非最优解；无法给出贪心正确性证明；题目有"最大/最小总和"表述且涉及取舍
**建议修正**: 先尝试构造贪心反例；无法证明正确性时换动态规划
**关联算法主题**: 贪心算法、动态规划、区间问题、背包问题

---

## Tag Selection Guide

When analyzing user code, apply tags in this priority order:

1. **First check for `wrong_complexity`** — most impactful, determines if the approach is viable at all
2. **Then check for `infinite_loop`** — breaks everything, runtime cannot produce output
3. **Then check for `order_dependency`** — subtle but fatal, logic may look correct but ordering kills it
4. **Then check for `off_by_one` and `missing_boundary`** — common edge case failures
5. **Then check for `greedy_fallacy`, `missing_dedup`, `type_mismatch`** — approach-level or cleanup-level issues
6. **For knowledge-based errors, use `pattern` / `proof` / `python`** as catch-all categories:
   - `pattern` — user does not know the standard approach for this problem type at all
   - `proof` — user knows the general area but confuses specific concepts or properties
   - `python` — user gets the concept right but recalls wrong numerical values

**Multi-tag rule**: A single error MAY have multiple tags. For example, a sliding window bug could be both `order_dependency` AND `missing_boundary`. Apply all relevant tags; the primary tag (listed first) should be the root cause.

**Exclusivity rule**: `pattern`, `proof`, and `python` are reserved for knowledge/recall errors. If the user's code logic is correct but they chose the wrong approach due to a knowledge gap, use these instead of the algo-specific tags (`off_by_one`, etc.).

---

## Tag-Mistake Log Alignment

This table shows how tags in this file map to the Root Cause column in `algorithms/mistake_log.md`:

| Root Cause in mistake_log | Tag in root-cause-tags.md | Category | Count |
|--------------------------|--------------------------|----------|-------|
| pattern | `pattern` | Knowledge gap (approach unknown) | 7 |
| proof | `proof` | Knowledge gap (concept confused) | 15 |
| python | `python` | Knowledge gap (value wrong) | 1 |
| (algo-only, no mistake_log entries yet) | `order_dependency` | Code logic (ordering) | 0 |
| (algo-only, no mistake_log entries yet) | `off_by_one` | Code logic (boundary) | 0 |
| (algo-only, no mistake_log entries yet) | `missing_boundary` | Code logic (boundary) | 0 |
| (algo-only, no mistake_log entries yet) | `wrong_complexity` | Code logic (approach) | 0 |
| (algo-only, no mistake_log entries yet) | `missing_dedup` | Code logic (cleanup) | 0 |
| (algo-only, no mistake_log entries yet) | `type_mismatch` | Code logic (type) | 0 |
| (algo-only, no mistake_log entries yet) | `infinite_loop` | Code logic (convergence) | 0 |
| (algo-only, no mistake_log entries yet) | `greedy_fallacy` | Code logic (approach) | 0 |

**Notes**:
- Tags `pattern`, `proof`, `python` are the only ones with current mistake_log entries (23 total). These cover knowledge/recall errors from choice questions.
- Tags `order_dependency` through `greedy_fallacy` are algo-code tags with 0 current entries. They will be populated as users submit `solve()` code for analysis.
- When a new algo-code error is recorded in mistake_log, its Root Cause column should use one of the 8 algo-code tags above.
- If none of the 11 existing tags fit, propose a new tag and update this file + comparison-template.md.
