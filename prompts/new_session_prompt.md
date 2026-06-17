# New Session Prompt

```text
我正在使用 Pass-LLM-with-LLM 备考 harness，请在当前项目中继续执行。

请先阅读：
1. AGENTS.md — 项目规则、Skill Pipeline、Component Map
2. START_HERE.md — Session bootstrap + Skill 调用顺序
3. HANDOFF.md — 上次 session 交接状态
4. 今天对应的 shared/daily/YYYY-MM-DD.md
5. shared/progress/task-board.md（全局跨目标 task board）
6. 对应目标目录 targets/<target>/ 下的 progress/task-board.md 和 mistake_log
7. shared/exam_memory/ 向量记忆系统（如 MCP 可用）

**切换目标：** 告诉我目标名称即可（如 "切换到 pdd"、"切 ai-lab"），我会加载对应 targets/<target>/ 的上下文。

**Skill Pipeline（OJ 题必须走这个流程）：**
- 每道 OJ 题先调用 Skill(skill="solve-skeleton") 获取骨架模板
- WA/TLE 时先记录到 `targets/<target>/mistake_log.md`，再根据需要做人工诊断和复盘
- 测试通过后调用 Skill(skill="algo-annotation") 添加中文注释 + # [防错]
- 选择题：Skill(skill="choice-q-create") → Skill(skill="choice-q-drill")
- 进度查看：Skill(skill="review-tracker")

**目录结构：**
- targets/ai-lab/       — AI Lab 笔试专属（cheatsheets、progress、sources）
- targets/pdd-algo/     — PDD 大模型算法岗专属（practice、solutions、progress）
- shared/               — 跨目标共享（cheatsheets、exam_memory、daily、progress）
- skills/               — 全局 Claude skills

MCP 验证：确认 mcp__exam-memory__* 工具是否可用。不可用则所有 skill 自动降级为纯本地模式。

规则：
- 优先帮助我刷 Python ACM/OJ 题并复盘 AC 率。
- 不要把时间花在大范围资料研究或复杂环境部署。
- 每天按 3-5 小时安排执行。
- 如果使用 ChatMem，请只加载 compact project context，并把 indexed local-history evidence 和 approved startup rules 区分开。

请根据今天日期和当前目标告诉我下一步应该做什么，并协助我执行。
```
