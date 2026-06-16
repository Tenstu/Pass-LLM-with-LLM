# Progress 目录分类整理规划

> 目标：为 progress/ 建立清晰的分类结构，避免文档混杂。按主题分目录存放，README 作为入口索引。

## 当前状态

progress/ 目前为扁平结构，共 6 份文档。随着备考推进，刷题记录、复盘记录、题库引用等会持续增长，需要提前规划分类。

## 目标结构

```
progress/
├── README.md                        # 入口索引（本规划完成后创建）
├── choice-questions/                # 选择题刷题记录
│   ├── round1.md
│   ├── round2.md
│   └── ...
├── study-planning/                  # 学习计划与准备度
│   ├── daily-plan-review-summary.md
│   └── readiness-score.md
├── exam-analysis/                   # 考试分析
│   └── exam-style-analysis.md
├── task-board/                      # 跨域任务追踪
│   └── task_board.md
└── mistake-log/                     # 错题记录（预留）
    └── ...
```

## 分类说明

| 目录 | 当前文档 | 说明 |
|------|----------|------|
| choice-questions/ | round2.md, round3.md | 按轮次记录的刷题进度 |
| study-planning/ | daily_plan_review_summary.md, readiness_score.md | 学习计划、每日复盘、准备度评估 |
| exam-analysis/ | exam_style_analysis.md | 出题风格分析、考试策略总结 |
| task-board/ | task_board.md | 跨域通用任务追踪 |
| mistake-log/ | (待填充) | 解题错因记录，solve-analyze 技能完成后启用 |

## 迁移条件

- 选择题轮次超过 3 轮，或新增刷题类型记录时
- 出现首个 mistake-log 条目时
- progress/ 文档总数超过 10 份时

迁移步骤：按上表目标结构创建子目录，移动文件，创建 README.md 入口。
