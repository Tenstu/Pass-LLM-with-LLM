# Progress 目录索引

按主题分类存放备考进度文件。新增文件时请参照下表选择目录。

## 目录结构

| 目录 | 用途 | 文件示例 |
|------|------|---------|
| `choice-questions/` | 选择题刷题记录，按轮次编号 | `round2.md`, `round3.md` |
| `study-planning/` | 学习计划、每日复盘、准备度自评 | `readiness-score.md`, `daily-plan-review-summary.md` |
| `exam-analysis/` | 出题风格分析、频率表、趋势预测、mock 成绩 | `exam-style-analysis.md` |
| `task-board/` | 跨域任务追踪（Sprint 任务、P0/P1/P2 优先级） | `task-board.md`, `task-board.example.md` |
| `reviews/` | 周期性复习总结（review-tracker 输出） | `review-YYYY-MM-DD.md` |

## 存放规则

- **选择题轮次记录**：写入 `choice-questions/roundN.md`（N 自增）。
- **学习计划 / 复盘 / 自评**：写入 `study-planning/`。
- **出题风格分析**：写入 `exam-analysis/exam-style-analysis.md`（唯一文件，追加更新）。
- **任务看板**：写入 `task-board/task-board.md`（唯一文件，追加更新）。
- **周期性复习总结**：写入 `reviews/review-YYYY-MM-DD.md`。
- **错题记录**：仍存放在 `targets/{target}/mistake_log.md`，不在此目录。

## 公开策略

- 可公开：`README.md`、任意子目录 `.gitkeep`、去个人化的 `*.example.md` / `*.template.md`。
- 不公开：真实运行态进度文件，例如 `task-board/task-board.md`、选择题轮次、准备度自评、复盘总结。
- 若需要给公开用户展示格式，请新增模板文件，不要提交真实进度记录。

## 历史文件

旧版扁平路径已迁移到子目录，技能文件中的引用路径已同步更新。

## Round 编号说明

选择题轮次编号不从 1 开始：
- **Round 1** = 2026-06-14 的首次模考（手动在纸上完成，未生成 round 文件）
- **Round 2** 起为 `choice-q-create` + `choice-q-drill` 自动生成的练习轮次
- 实际轮次记录见对应 target 目录（如 `targets/ai-lab/progress/choice-questions/`）
