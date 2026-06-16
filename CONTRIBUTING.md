# 开发规范 - 协作指南

> 适用于本项目开源后的 PR 协作，不过度约束，保留 ACM 备考工程的轻量风格。

## 1. 项目性质

本项目是**备考执行工程**，不是库或框架。所有产出围绕"刷题 → 复盘 → 提分"闭环。
贡献前请阅读 `AGENTS.md` 了解完整的 Component Map 和 Skill Pipeline。

## 2. 分支与 PR

| 规则 | 说明 |
|------|------|
| 主分支 | `main`，始终保持可运行 |
| 功能分支 | `feat/xxx`（新功能）、`fix/xxx`（修复）、`docs/xxx`（文档） |
| PR 粒度 | 一个 PR 做一件事：一道算法题 / 一个 Skill 更新 / 一篇 cheatsheet |
| PR 描述 | 必须说明：改了什么、为什么改、影响哪些 Skill 或数据流 |

## 3. Python 代码规范

算法代码遵循 ACM/OJ 风格，**不引入工程化框架**：

```python
# 标准开头
import sys
input = sys.stdin.readline

def solve():
    # 解题逻辑
    ...

if __name__ == "__main__":
    solve()
```

- Python 3.10+，标准库为主，不用第三方包（除非 `python_oj_template.py` 已有）。
- 变量名简洁但可读：`n, m, arr, dp, res` 合适，`a, b, c` 仅用于短循环。
- 每个 `solve()` 函数必须能独立运行（可粘贴到 OJ 平台）。
- 复杂度注释写在函数上方一行：`# O(n log n) time, O(n) space`。

## 4. Skill 文件规范

Skill 是 Markdown 文件，存放于 `skills/`，格式要求：

```markdown
---
name: skill-name          # kebab-case，与文件名一致
description: 一句话说明
tools: [tool1, tool2]     # 依赖的 MCP 工具（如有）
---

# Skill 内容
...
```

- frontmatter 必须包含 `name` 和 `description`。
- 工作流步骤用有序列表，触发词用无序列表。
- 引用其他文件用相对路径：`algorithms/mistake_log.md`。

## 5. 目录归属规则

| 内容类型 | 存放位置 | 命名规则 |
|----------|----------|----------|
| 考试真题解答 | `algorithms/solutions_batch.py` | 统一编号 |
| 非考试练习题 | `algorithms/practice/{topic}.py` | 按算法专题命名 |
| 错误记录 | `algorithms/mistake_log.md` | 按主题分区，表格式 |
| 每日计划 | `daily/YYYY-MM-DD.md` | 日期命名 |
| 速记资料 | `llm/{topic}.md` | 主题命名 |
| Skill 定义 | `skills/{name}.md` 或 `skills/{name}/SKILL.md` | kebab-case |
| 进度追踪 | `progress/` | 项目内部管理 |

**不要**把练习题放进 `solutions_batch.py`，也不要考试题放进 `practice/`。

## 6. Commit Message

```
<type>: <简短描述>

类型：
  feat     新功能/新题/新 Skill
  fix      修复错误/修正解法
  docs     文档更新
  log      错误日志/复盘记录（mistake_log, mock_exam_log）
  refactor Skill 或模板重构
```

示例：
```
feat: add BFS skeleton for grid traversal
fix: correct sliding window off-by-one in solution #12
log: record WA on binary search boundary condition
docs: update GNN cheatsheet with message passing detail
```

## 7. PR Checklist

提交 PR 前确认：

- [ ] 算法题已走 solve-skeleton → algo-annotation 完整流程
- [ ] WA/TLE 错误已录入 `algorithms/mistake_log.md`
- [ ] 新 Skill 有完整的 frontmatter（name, description）
- [ ] 未引入不必要的第三方依赖
- [ ] 不涉及 `exam_memory/` 个人数据（该目录在 `.gitignore`）

## 8. 不做的事

以下**不在本项目范围内**，请勿贡献：

- 通用算法库封装（本项目是备考用，不是 LeetCode 题解库）
- CI/CD 流水线（过度工程化）
- 前端 UI / Web 界面
- 数据库迁移脚本
- 大规模重构目录结构（除非先开 Issue 讨论）
