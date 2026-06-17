# Comparison Report Template

> solve-analyze skill 的对比报告模板。分析完成后按此模板生成结构化报告。
> 报告同时作为 mistake_log 回流和用户参考的依据。
> 占位符语法：`{{field_name}}` 表示由 agent 填充的变量字段。

---

## 解题对比报告

### 基本信息
- **题目**：{{problem_reference}}
- **识别模式**：{{algorithm_pattern}}（匹配 solve-skeleton 模板：{{template_name}}）
- **用户解法状态**：{{status}}（WA / TLE / AC 有隐患 / 逻辑正确但写法不优）
- **分析日期**：{{date}}

### 代码结构对比

| 区域 | 用户写法 | 标准写法 | 差异类型 | 严重度 |
|------|----------|----------|----------|--------|
{{comparison_rows}}

差异类型说明：
- **顺序错误**：操作执行顺序不正确
- **缺失**：必要的逻辑/边界处理缺失
- **冗余**：不必要的代码，可能影响性能
- **写法差异**：功能等价但不够简洁
- **逻辑错误**：核心算法逻辑有误

严重度说明：
- **P0**：直接导致 WA / TLE，必须修正
- **P1**：特定输入下会出错，强烈建议修正
- **P2**：不影响正确性但有隐患或风格问题

### 根因诊断

| 标签 | 含义 | 出现位置 | 贡献度 |
|------|------|----------|--------|
{{root_cause_rows}}

**主因**：{{primary_root_cause}}

### 建议修正

{{fix_suggestions}}

格式：
1. L{{line_start}}-L{{line_end}}：{{fix_description}}
2. ...

### 自动回流动作

- [{{mistake_log_status}}] mistake_log：{{mistake_log_action}}
- [{{profile_status}}] user_profile：{{profile_action}}
- [{{mcp_status}}] experience MCP：{{mcp_action}}

### 下一步建议

{{next_steps}}

选项：
- invoke `algo-annotation` — 为修正后的代码添加 `# [防错]` 标记
- invoke `solve-skeleton` — 重新从骨架开始
- 直接修正当前代码 — 仅修改标记的行

---

## 轻量快速检查模板（AC Fast Path）

当代码 AC 且仅有骨架规范差异时，使用此轻量模板替代完整对比报告。

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

差异类型仅限：I/O 模式、结构缺失、docstring 缺失、命名差异。
严重度均为 P2（不影响 AC）。

### 结论

逻辑正确，可直接 AC。差异仅在 solve-skeleton 编码规范层面。

### 下一步建议

- invoke `algo-annotation` — 为代码添加 `# [防错]` 标记和中文行级注释
- 按骨架规范重写 — 使用 5-phase 结构 + readline 别名（可选，不影响 AC）
```

**使用条件**：
- 逻辑正确（Agent A 确认无 WA/TLE 风险）
- 差异全部为 P2 级别（仅风格/规范，无逻辑/复杂度问题）
- 不触发任何反馈回流（不写 mistake_log、不更新 MCP）

**不使用条件**：
- 用户明确说 "WA" / "TLE" / "超时"
- 存在 P0/P1 级差异（逻辑错误、复杂度不达标）
- 用户问 "哪里错了"（隐含认为有问题）

---

## 使用说明

### 状态判定规则

| 用户代码表现 | 状态值 | mistake_log Result | Mastery |
|------------|--------|-------------------|---------|
| 有明确逻辑错误 | WA | WA | WA |
| 逻辑正确但超时 | TLE | TLE | WA |
| 逻辑正确但有隐患 | AC(有风险) | WA | struggling |
| 逻辑正确写法不优 | AC(可优化) | (不记录) | confirmed |

### 回流动作模板

**mistake_log 追加行格式**：
```
| {{date}} | {{problem}} | {{topic}} | {{result}} | {{mastery}} | {{root_cause_tag}} | {{fix_rule}} | {{redo_date}} |
```

字段映射：
- `{{date}}` — 当天日期，格式 MM-DD
- `{{problem}}` — 题目简短引用（如 "LC127 单词接龙"）
- `{{topic}}` — 算法主题（如 "BFS/最短路径"），对应 mistake_log 的 section 分区
- `{{result}}` — 取自状态判定规则表的 "mistake_log Result" 列
- `{{mastery}}` — 取自状态判定规则表的 "Mastery" 列
- `{{root_cause_tag}}` — 主因标签（从根因标签库 `root-cause-tags.md` 匹配）
- `{{fix_rule}}` — 一句话修正规则（从建议修正中提炼，不超过 60 字）
- `{{redo_date}}` — 按 Mastery 级别参考计算（WA/lucky_pass/struggling → +1 天，confirmed → 不设）

**防错规则追加格式**（仅当该标签尚无防错规则时）：
```
### 防错规则：{{prevention_rule}}
```

追加到 mistake_log 对应主题分区的末尾，格式与现有条目一致。

**`mcp__exam-memory__save_experience` 参数**：
- title: `{{topic}}: {{short_error_description}}`
- content: full comparison report
- type: "算法"
- knowledge: "{{topic}}"
- difficulty: "{{difficulty}}"

### 填充流程

1. **分析阶段**：Agent A 静态分析用户代码，Agent B 用 solve-skeleton 生成标准解法
2. **对比阶段**：逐区域对比，标记差异类型和严重度
3. **诊断阶段**：从 `root-cause-tags.md` 标签库匹配根因，标注贡献度
4. **生成阶段**：按本模板填充所有 `{{placeholder}}` 字段
5. **回流阶段**：根据状态判定规则，自动执行 mistake_log、user_profile、MCP 回流

---

## 示例：已填充的完整报告

以下是一份针对 BFS 网格最短路径问题的完整报告，展示所有字段的实际值。

### 示例背景

LC127 "单词接龙"：给定 beginWord、endWord 和字典 wordList，每次变换一个字母，求从 beginWord 到 endWord 的最短变换序列长度。用户代码在 BFS 层级计数和邻居生成上存在两处问题，最终 WA。

---

> ## 解题对比报告
>
> ### 基本信息
> - **题目**：LC127 单词接龙
> - **识别模式**：BFS/最短路径（匹配 solve-skeleton 模板：`bfs-unweighted-shortest`）
> - **用户解法状态**：WA
> - **分析日期**：2026-06-16
>
> ### 代码结构对比
>
> | 区域 | 用户写法 | 标准写法 | 差异类型 | 严重度 |
> |------|----------|----------|----------|--------|
> | 层级计数 | `step = 1` 在入队前设置，每次 pop 时 `step += 1` | `step` 以层为单位递增：每处理完一层（`for _ in range(len(q))`) 后 `step += 1` | 逻辑错误 | P0 |
> | 邻居生成 | 遍历 wordList 对每个词做字符串比较 O(L*n) | 对当前词的每个位置尝试 26 个字母 O(L*26) | 冗余 | P1 |
> | 访问标记 | 出队时才标记 visited | 入队时立即标记 visited，避免重复入队 | 顺序错误 | P1 |
>
> 差异类型说明：
> - **顺序错误**：操作执行顺序不正确
> - **缺失**：必要的逻辑/边界处理缺失
> - **冗余**：不必要的代码，可能影响性能
> - **写法差异**：功能等价但不够简洁
> - **逻辑错误**：核心算法逻辑有误
>
> ### 根因诊断
>
> | 标签 | 含义 | 出现位置 | 贡献度 |
> |------|------|----------|--------|
> | `order_dependency` | 操作顺序依赖错误 | L22-25：出队标记导致同层节点可重复入队 | 60% |
> | `wrong_complexity` | 复杂度不达标 | L30-38：O(L*n) 邻居枚举，大数据 TLE | 25% |
> | `off_by_one` | 边界偏移 | L15：step 初始值和递增时机导致结果偏移 1 | 15% |
>
> **主因**：`order_dependency` — 入队标记 vs 出队标记的顺序错误导致层级计算混乱
>
> ### 建议修正
>
> 1. L15-L25：重构层级计数为 `step = 0`，每层 `for _ in range(len(q))` 循环后 `step += 1`
> 2. L22：将 `visited.add(word)` 从出队处移到入队前，紧跟 `q.append()`
> 3. L30-L38：替换邻居生成为位置枚举法 `for i in range(L): for c in 'abcdefghijklmnopqrstuvwxyz'`
>
> ### 自动回流动作
>
> - [x] mistake_log：追加 `order_dependency` 条目到 BFS/最短路径 分区
> - [x] user_profile：weaknesses["BFS/最短路径"] +1
> - [ ] experience MCP：新模式，需用户确认保存
>
> ### 下一步建议
>
> 建议按优先级处理：
> 1. 先修正层级计数逻辑（P0，直接影响正确性）
> 2. 再修正入队标记顺序（P1，避免重复入队的隐患）
> 3. 可选：优化邻居生成方式（P1，提升性能但不影响正确性）
>
> 选项：
> - invoke `algo-annotation` — 为修正后的代码添加 `# [防错]` 标记
> - invoke `solve-skeleton` — 重新从骨架开始
> - 直接修正当前代码 — 仅修改标记的行
>
> ---
>
> ### 对应 mistake_log 追加行
>
> ```
> | 06-16 | LC127 单词接龙 | BFS/最短路径 | WA | WA | order_dependency | BFS层级计数用for-range(len(q))逐层递增，入队即标记visited | 06-17 |
> ```
>
> ### 对应防错规则（追加到 BFS/最短路径 分区末尾）
>
> ```
> ### 防错规则：BFS 层级计数 = 每层 for _ in range(len(q)) 后 step += 1，不要每次 pop 都 +1。入队即标记 visited，不要等到出队。
> ```
