# 解题分析 Skill 规划

> 创建日期：2026-06-15 | 状态：规划中

## 目标

新增 `solve-analyze` Skill，在用户自行解题后，自动对比用户解法与标准解法的差异，定位错误根因，并将分析结果回流到用户画像、错题库和后续出题策略。

## 定位

```
solve-skeleton（骨架）
  → 用户填逻辑
    → ★ solve-analyze（对比分析）★  ← 新增
      → algo-annotation（标注）
      → mistake_log（记录）
      → user_profile（画像更新）
      → choice-q-create（调整出题）
```

`solve-analyze` 位于用户解题与记录之间，是**诊断层**，不做教学，只做"你写了什么 vs 应该写什么"的结构化对比。

## 工作流

### 输入

用户提供：
- 自己的 `solve()` 代码
- 题目描述（或题号引用）

### 过程（Agent 驱动）

使用 Agent 并行执行两条路径，再汇合对比：

```
                    ┌──────────────────────┐
                    │   User's solve()     │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  solve-analyze Skill  │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                                 ▼
   Agent A: 静态分析                    Agent B: 标准解法生成
   - 逐行审查逻辑                       - 用 solve-skeleton 重新生成
   - 识别模式标签                        - 填充正确逻辑
   - 标记可疑行                          - 走完反模式检查
              │                                 │
              └────────────┬────────────────────┘
                           ▼
                   对比分析报告
                           │
              ┌────────────┼────────────────┐
              ▼            ▼                ▼
         mistake_log   user_profile    experience MCP
```

### 输出：对比报告

```markdown
## 解题对比报告

### 基本信息
- 题目：[题目引用]
- 模式：滑动窗口
- 用户解法状态：WA / TLE / AC（有隐患）

### 逐行对比

| 区域 | 用户写法 | 标准写法 | 差异类型 |
|------|----------|----------|----------|
| 窗口滑出判断 | 先减再判断 | 先判断再减 | 顺序错误 |
| 边界处理 | 未处理空窗口 | `if window_size > 0` | 缺失 |

### 根因标签（从标签库匹配）

- `order_dependency`：操作顺序依赖错误（本次主因）
- `missing_boundary`：边界条件缺失

### 建议修正
1. L58-60：将 `cnt_a[out_v] -= 1` 移到 if 判断之后
2. L52：初始窗口需单独判断 `m <= n`

### 自动回流动作
- [x] mistake_log：追加 `order_dependency` 条目
- [x] user_profile：weaknesses["滑动窗口"] +1
- [ ] experience MCP：新模式，需用户确认保存
```

## 根因标签库

维护一份标准错误标签，供分析报告引用和 mistake_log 分类：

| 标签 | 含义 | 常见场景 |
|------|------|----------|
| `order_dependency` | 操作顺序依赖错误 | 滑窗先减后判断 vs 先判断后减 |
| `off_by_one` | 边界偏移 | 数组索引、区间开闭 |
| `missing_boundary` | 边界条件缺失 | 空输入、单元素、n=0 |
| `wrong_complexity` | 复杂度不达标 | 嵌套循环应为 O(n) |
| `missing_dedup` | 去重遗漏 | 排序后未跳过重复 |
| `type_mismatch` | 类型处理错误 | int/str 混用 |
| `infinite_loop` | 死循环 | while 条件不收敛 |
| `greedy_fallacy` | 贪心不成立 | 局部最优非全局最优 |

标签库存放：`skills/solve-analyze/references/root-cause-tags.md`

## 与下游 Skill 联动

### 1. → mistake_log（自动）

根因标签直接追加到 `algorithms/mistake_log.md` 对应主题分区，格式与现有一致。

### 2. → user_profile（自动）

根据根因标签更新用户画像：
- `weaknesses`：该算法主题 +1
- 若同一标签在 3 次不同题目中出现 → 标记为 `persistent_weakness`

### 3. → exam-memory MCP（需确认）

- 匹配已有经验：`inc_error_count`
- 新根因模式：询问用户"是否存入经验库"→ `save_experience`

### 4. → choice-q-create（间接）

分析结果写入 mistake_log 后，choice-q-create 在下次出题时自动读取并加权。

### 5. → algo-annotation（前置）

analyze 报告产出后，再调用 annotation 添加 `# [防错]` 标记，防错内容直接引用 analyze 的根因标签。

## 目录结构

```
skills/
  solve-analyze/
    SKILL.md                        # Skill 定义（工作流、触发词）
    references/
      root-cause-tags.md            # 根因标签库
      comparison-template.md        # 对比报告模板
```

## 触发词

- "分析一下我的代码"
- "帮我看看哪里错了"
- "对比一下"
- "review my solve"
- "check my code"
- 用户粘贴代码 + "看看"

## 实施条件

- [x] `solve-skeleton` 已稳定（当前已完成）
- [x] `algo-annotation` 已稳定（当前已完成）
- [ ] `exam-memory` MCP 已实现（V1 即可）
- [x] 根因标签库初版（从 mistake_log 现有条目反向提取）

## 实施记录

> 实施日期：2026-06-16

已完成交付物：
- `skills/solve-analyze/SKILL.md` — 主 Skill 定义（7 节：概述、核心原理、工作流、输入输出、反馈回流、交叉引用、MCP 矩阵）
- `skills/solve-analyze/references/root-cause-tags.md` — 11 个根因标签（3 知识类 + 8 算法代码类），含检测规则和修正建议
- `skills/solve-analyze/references/comparison-template.md` — 对比报告模板，含状态判定规则、回流动作模板和完整示例
- `AGENTS.md` 已更新：Component Map、Skill Pipeline、Data Flow、MCP 矩阵、Skill Invocation Protocol、OJ Practice Workflow、MCP 降级行为
