# New Session Prompt

```text
我正在使用 Pass-LLM-with-LLM 备考 harness，请在当前项目中继续执行。

请先阅读：
1. AGENTS.md — 执行契约、运行模式、关键边界和 Skill 路由
2. START_HERE.md — Session bootstrap + Skill 调用顺序
3. HANDOFF.md — 上次 session 交接状态
4. 今天对应的 shared/daily/YYYY-MM-DD.md
5. shared/progress/task-board/task-board.md（全局跨目标 task board，本地/dev 运行态）
6. 对应目标目录 targets/<target>/ 下的 progress/task-board/task-board.md 和 mistake_log
7. shared/exam_memory/ 向量记忆系统（如 MCP 可用；不可用则进入 Local Markdown / Stateless Lite）

**切换目标：** 告诉我目标名称即可（如 "切换到 pdd"、"切 ai-lab"），我会加载对应 targets/<target>/ 的上下文。

**Skill Pipeline（OJ 题必须走这个流程）：**
- 每道 OJ 题先调用 Skill(skill="solve-skeleton") 获取骨架模板
- WA/TLE 时先记录到 `targets/<target>/mistake_log.md`，再根据需要做人工诊断和复盘
- 测试通过后调用 Skill(skill="algo-annotation") 添加中文注释 + # [防错]
- 选择题：Skill(skill="choice-q-create") → Skill(skill="choice-q-drill")
- 如果交互式 quiz 工具不可用，选择题可以用聊天答案模式，例如 `1A 2BD 3C`，并返回得分表与 append blocks
- 进度查看：Skill(skill="review-tracker")

**目录结构：**
- targets/ai-lab/       — AI Lab 笔试专属（cheatsheets、progress、sources）
- targets/pdd-algo/     — PDD 大模型算法岗专属（practice、solutions、progress）
- shared/               — 跨目标共享（cheatsheets、exam_memory、daily、progress）
- skills/               — 全局 Claude skills

运行模式验证：
- `mcp__exam-memory__*` 可用且仓库可写：Full MCP Mode，Markdown + MCP 双写。
- MCP / ChatMem / 本地索引不可用但仓库可写：Local Markdown Mode，使用 `HANDOFF.md`、daily log、`mistake_log.md`、round 文件继续。
- 仓库不可写或只能聊天继续：Stateless Lite Mode，最终返回 `[MISTAKE_LOG_APPEND]`、`[DAILY_PROBLEM_LOG_APPEND]`、`[CHOICE_ROUND_SUMMARY]`、`[HANDOFF_UPDATE]`。

MCP 不可用不是失败；流程内部安静降级，但最终报告要提醒我：哪些跨会话能力不可用、哪些 append blocks 需要落到 Markdown、Lite/Portable Mode 不建议长期作为唯一工作流。

规则：
- 优先帮助我刷 Python ACM/OJ 题并复盘 AC 率。
- 不要把时间花在大范围资料研究或复杂环境部署。
- 每天按 3-5 小时安排执行。
- 如果使用 ChatMem，请只加载 compact project context，并把 indexed local-history evidence 和 approved startup rules 区分开。
- 如果 ChatMem 不可用，请依赖 `HANDOFF.md` 和 daily logs，不要要求我重述已有项目背景。

请根据今天日期和当前目标告诉我下一步应该做什么，并协助我执行。
```
