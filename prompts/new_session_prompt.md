# New Session Prompt

```text
我正在准备上海 AI 实验室"基座模型算法（地球空间方向）- AI For Science 中心"线上笔试，2026-06-16，120 分钟。请在当前项目中继续执行备考 harness。

请先阅读：
1. AGENTS.md — 项目规则、Skill Pipeline、Component Map
2. START_HERE.md — Session bootstrap + Skill 调用顺序
3. HANDOFF.md — 上次 session 交接状态
4. 今天对应的 daily/YYYY-MM-DD.md
5. progress/task-board/task-board.md
6. algorithms/mistake_log.md 和 algorithms/mock_exam_log.md
7. sources/ai_lab_history_problems.md（历史真题分类 + 复习方向）

**Skill Pipeline（OJ 题必须走这个流程）：**
- 每道 OJ 题先调用 Skill(skill="solve-skeleton") 获取骨架模板
- WA/TLE 时调用 Skill(skill="solve-analyze") 诊断对比 + 根因标签 + 自动写 mistake_log
- 测试通过后调用 Skill(skill="algo-annotation") 添加中文注释 + # [防错]
- 选择题：Skill(skill="choice-q-create") → Skill(skill="choice-q-drill")
- 进度查看：Skill(skill="review-tracker")

考试结构：
- 选择题：单选 8 题（每题 3 分）+ 不定项 7 题（每题 4 分），共 52 分
- 编程：3 道 ACM/OJ 题
- 多选题策略：漏选比多选扣分少，不确定不选

MCP 验证：确认 mcp__exam-memory__* 工具是否可用。不可用则所有 skill 自动降级为纯本地模式。

规则：
- 优先帮助我刷 Python ACM/OJ 题并复盘 AC 率。
- 不要把时间花在大范围资料研究或复杂环境部署。
- 每天按 3-5 小时安排执行。
- 算法占 70%（含数学选择题专项），大模型核心八股占 20%，项目表达占 10%。
- 如果使用 ChatMem，请只加载 compact project context，并把 indexed local-history evidence 和 approved startup rules 区分开。

请根据今天日期告诉我下一步应该做什么，并协助我执行。
```
