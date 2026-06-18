# pass-llm-with-llm

> 用 LLM 备考 LLM 与算法笔试 — 面向教育与备考场景的 Claude Code Skills + MCP 执行框架

[English](README.md) | 关键词：`education`、`exam-prep`、`llm`、`algorithm`、`claude-code`、`mcp`、`ai-agents`、`spaced-repetition`、`python-oj`

## 项目亮点

- **教育优先的学习闭环**：把刷题、诊断、错题、复盘组织成可重复执行的备考流程，而不是散乱笔记。
- **Agent 友好的目录结构**：`skills/`、`targets/`、`shared/`、`progress/` 分区稳定，方便 coding agent 和 MCP 工具检索。
- **闭环式笔试准备**：错题会回流到后续注释、选择题训练、就绪度报告，以及规划中的复习调度。
- **默认本地可读**：Markdown 文件可人工阅读、可 Git 版本管理；MCP 只是增强持久化与检索，不是硬依赖。

## 这是什么

一个**执行型备考框架**，不是知识库。它通过 Claude Code 的 Skill 机制，将算法骨架生成、解题诊断、代码标注、错题回流、选择题训练、复习规划串联成自动化闭环。

默认面向 AI/算法岗位笔试，核心 Skill Pipeline 与考试无关，可适配任意笔试目标。

## 核心特性

- **Skill Pipeline**：solve-skeleton → solve-analyze → algo-annotation，从题目到标注解法的完整链路
- **错题反馈闭环**：WA/TLE 自动记录，下次刷题自动标注 `# [防错]` 标记
- **选择题引擎**：定向出题 → 交互答题 → 即时评分 → 弱点分析
- **MCP 经验沉淀**（可选）：自定义 MCP Server 实现跨会话错误模式持久化 + 用户画像
- **进度与复习追踪**：就绪度评分、知识点覆盖缺口、每日必做清单，以及规划中的间隔复习队列

## 仓库 Topics 建议

建议在 GitHub 仓库设置这些 topics，提升检索与推荐命中：

```text
education, exam-prep, llm, algorithm, python, claude-code, mcp, ai-agents,
agent-workflow, spaced-repetition, study-tools, interview-prep, oj
```

## Agent / MCP 检索入口

如果你是 agent、MCP client 或本地检索工具，优先读取：

| 需求 | 入口 |
|------|------|
| session 启动 | `START_HERE.md` |
| 项目规则与 skill 路由 | `AGENTS.md` |
| 当前交接与目标配置 | `HANDOFF.md` |
| agent 可调用技能 | `skills/` |
| 目标考试专属材料 | `targets/{target}/` |
| 共享 MCP server 与检索辅助 | `shared/exam_memory/` |
| 开发路线图 | `docs/dev-roadmap.md` |
| 复习机制实现规划 | `docs/plans/2026-06-17-review-mechanism-implementation-plan.md` |

## 快速开始

### 前置条件

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI 或 VS Code 扩展
- Python 3.10+（仅 MCP Server 需要）

### 环境支持

| 组件 | 说明 |
|------|------|
| IDE | VS Code（**推荐** — 交互答题模式需要 VS Code 扩展）或终端 |
| Claude Code | VS Code 扩展（**推荐**）或 CLI（`npm install -g @anthropic-ai/claude-code`） |
| Model Provider | 支持 Claude Code 接入的任意 provider（Claude API、第三方、本地模型） |
| Python | 3.10+（仅 exam-memory MCP Server 需要） |

本项目基于 **Claude Code VS Code 扩展**开发，使用第三方 model provider。Skill Pipeline 与底层模型无关，任意可用模型均可运行。

### 安装

```bash
git clone https://github.com/Tenstu/pass-llm-with-llm.git
cd pass-llm-with-llm
```

### 配置目标考试

编辑 `HANDOFF.md`，填写你的目标考试名称、日期和每日可投入时间。在 `targets/{target}/sources/` 下补充目标考试的历史题型分析。

### 使用

1. 在 Claude Code 中打开项目目录
2. **首次使用？** 说 "init" 或 "初始化" 启动导引流程 — 收集备考目标、考试范围、目标日期
3. 日常使用：阅读 `START_HERE.md` 了解 session 启动流程
4. 遇到算法题：`Skill(skill="solve-skeleton")`
5. 需要诊断：`Skill(skill="solve-analyze")`
6. 练习选择题：`Skill(skill="choice-q-create")` → `Skill(skill="choice-q-drill")`

### 启动顺序

```
git clone → cd pass-llm-with-llm
  │
  ├── pip install mcp               # 可选：安装 exam-memory MCP Server 依赖
  │
  ├── 编辑 .mcp.json                # 注册 exam-memory，指向 shared/exam_memory/server.py
  │
  ├── 在 Claude Code 中打开项目
  │     │
  │     ├── 首次使用 → 说 "init" → init-guide Skill 引导完成配置
  │     │
  │     └── 日常使用 → 读 START_HERE.md → Skill Pipeline
  │
  └── （可选）配置环境级 MCP：ChatMem、mempalace、onefind
        这些是外部工具，不由项目自带
        如需使用，请在 Claude Code 环境中配置
```

### MCP 依赖说明

本项目**自带一个 MCP Server**（`exam-memory`），**引用外部 MCP** 需单独安装：

| MCP Server | 是否自带 | 用途 | 配置方式 |
|------------|:---:|------|---------|
| `exam-memory` | 是 | 跨会话经验持久化 + 用户画像 | `pip install mcp` + 编辑 `.mcp.json` |
| ChatMem | 否 | 跨会话对话记忆 | [外部安装](https://github.com/Rimagination/ChatMem/releases) |
| mempalace | 否 | 结构化知识存储 | [外部安装](https://github.com/MemPalace/mempalace) |
| onefind | 否 | 本地知识库检索 | [外部安装](https://github.com/iawnfoanaowt/OneFind) |

所有 Skill 在 MCP 不可用时自动降级为纯本地模式。若要启用项目自带 server，在 `.mcp.json` 中注册一个 stdio 命令运行 `shared/exam_memory/server.py`。

## Skill 一览

| Skill | 功能 | MCP 依赖 |
|-------|------|:---:|
| init-guide | 首次使用导引：备考目标、日期、范围、用户画像 | 可选 |
| solve-skeleton | 算法题骨架生成（8 模板 + 6 模式） | 无 |
| solve-analyze | 解题诊断：代码对比 + 根因标签 | 可选 |
| algo-annotation | 中文注释 + `# [防错]` 标记 | 无 |
| choice-q-create | 定向选择题生成 | 可选 |
| choice-q-drill | 交互答题 + 即时评分 | 可选 |
| exam-assistant | 考试助手（经验检索 + 用户画像） | 核心 |
| review-tracker | 进度汇总 + 就绪度趋势 | 无 |

标记"可选"的 Skill 在 MCP 不可用时自动降级为纯本地模式。

### ChatMem 增强（推荐）

[ChatMem](https://github.com/Rimagination/ChatMem/releases) 提供跨会话对话记忆。非必需，但能显著提升以下 Skill 的体验：

| Skill | ChatMem 增强效果 |
|-------|-----------------|
| review-tracker | 存储历史进度报告，实现跨会话趋势对比 |
| exam-assistant | 回溯之前的答题会话和错题讨论，保持学习连续性 |
| init-guide | 记忆上次配置过程，避免重复收集已知信息 |
| solve-analyze | 跨会话关联诊断历史，识别反复出现的错误模式 |

安装 ChatMem 并在 Claude Code 全局配置中注册。

### MemPalace 增强（可选）

[MemPalace](https://github.com/MemPalace/mempalace) 提供结构化知识存储与跨 wing 知识图谱。适合长期知识管理，超越单次备考周期：

| 使用场景 | 增强效果 |
|---------|---------|
| 知识图谱 | 建模知识点前置关系（如 DP ← 背包问题，二分 ← 有序数组），实现定向复习 |
| Agent 日记 | 每次 session 记录学习观察，构建可搜索的"我学到了什么"历史 |
| 跨项目知识 | 将备考笔记与项目实战、面试准备、研究笔记关联 |

适合与 review-tracker（知识图谱查覆盖缺口）和 exam-assistant（结构化检索历史洞察）配合使用。项目内 Skill 不直接调用 MemPalace，通过 Claude Code 手动使用其工具。

### OneFind 增强（可选）

[OneFind](https://github.com/iawnfoanaowt/OneFind) 从本地知识库（Obsidian 笔记库、Zotero 文献库、本地文件夹）检索内容。适合已有外部学习笔记的用户：

| 使用场景 | 增强效果 |
|---------|---------|
| Obsidian 笔记 | 练习时搜索已有的 ML/算法笔记，关联相关概念 |
| Zotero 文献库 | 为 `shared/cheatsheets/` 或 `targets/{target}/cheatsheets/` 中的 Transformer、GNN、Diffusion 主题检索参考论文 |
| 混合检索 | 跨所有本地源执行词法 + 语义联合搜索 |

适合与 choice-q-create（从笔记中搜索出题素材）、exam-assistant（解答时检索参考资料）和 review-tracker（检查笔记是否覆盖考试知识点）配合使用。项目内 Skill 不直接调用 OneFind，通过 Claude Code 手动使用其工具。

#### OneFind + exam-memory：互补检索层

OneFind 的 **folder source** 可以索引 `shared/exam_memory/experiences/` 目录，提供语义搜索能力。但 OneFind 是**只读检索**层设计，无法替代 exam-memory 的写入链路（保存经验 → 向量化 → 原子存储）。推荐组合方案：

| 层级 | 角色 | 写入 | 读取 |
|------|------|:----:|:----:|
| `exam-memory` MCP | 经验 CRUD + 错误计数 + 用户画像 | 是（save, update） | 是（list, 按类型过滤） |
| OneFind folder source | 经验文件的语义搜索覆盖层 | 否（仅索引刷新） | 是（语义 + 关键词） |

**配置方式**：将 OneFind 的 `folder_library` 指向 `shared/exam_memory/experiences/`，然后使用 `onefind_search`（`target="folder"`）对历史经验做语义检索。通过 MCP 保存新经验后，调用 `onefind_index_refresh` 触发索引更新。

## 路线图

### V1（当前）— 稳定版

- Skill Pipeline：solve-skeleton / solve-analyze / algo-annotation
- 选择题引擎：出题 / 答题 / 评分
- exam-memory MCP V1：本地文件式经验 CRUD + 用户画像
- 进度追踪与错题反馈闭环

### V2 — RAG + 语义检索

将 `exam-memory` 从关键词匹配升级为语义检索：

| 阶段 | 特性 | 依赖 |
|------|------|------|
| 1 | 经验文件自动向量化 → numpy 存储 | `sentence-transformers`（bge-m3） |
| 2 | `list_experiences` 支持语义检索 | 阶段 1 |
| 3 | LLM 自动推断用户画像 | LLM API |
| 4 | 知识图谱关联推荐前置知识点 | 阶段 1 |

### V2.5 — 复习调度

把间隔复习纳入当前 dev 规划：

- 在 `targets/{target}/progress/reviews/` 下维护文件式 review queue
- 基于 SM-2 简化规则调度错题、薄弱知识点、选择题错误
- 可选 MCP 工具：`list_due_reviews` 与 `mark_review_result`
- 详见 [复习机制实现规划](docs/plans/2026-06-17-review-mechanism-implementation-plan.md)

### V3 — 远期方向

- **多模态**：截图题目 OCR → 自动识别题型并检索经验
- **跨设备同步**：Git 或 WebDAV 同步经验文件
- **可视化仪表盘**：强弱项热力图、错误趋势、复习计划

### 开源改进

- GitHub Issue & PR 模板（`.github/`）
- `CHANGELOG.md`

## 目录结构

```
pass-llm-with-llm/
  AGENTS.md                    # 项目规则、Component Map、Skill Pipeline
  START_HERE.md                # Session 启动引导 + Skill 调用指南
  HANDOFF.md                   # Session 交接模板
  README.md                    # 英文文档
  README_CN.md                 # 本文件（中文）

  skills/                      # Claude Code Skill 定义
    init-guide.md              # 首次使用导引（备考目标、日期、范围）
    solve-skeleton/            # 算法骨架模板
    solve-analyze/             # 解题诊断引擎
    algo-annotation.md         # 代码标注 + 防错标记
    choice-q-create.md         # 选择题生成器
    choice-q-drill.md          # 交互答题模式
    exam-assistant.md          # MCP 考试助手
    review-tracker.md          # 进度汇总

  targets/                     # 目标考试专属内容
    ai-lab/
      exam_config.md           # 考试题型、分值、时间配置
      cheatsheets/             # 目标专属 AI/ML 速记资料
      daily/                   # 目标专属每日计划
      progress/                # 选择题轮次、学习计划、考试分析、任务看板
      prompts/                 # 目标专属 prompt 模板
      sources/                 # 历史题型与目标专属参考资料
    pdd-algo/
      exam_config.md           # PDD 算法笔试配置
      python_oj_template.py    # 工具函数库
      solutions_batch.py       # 考试真题解答集
      practice/                # 按专题分类的练习题
      solutions/               # 单题题解
      mistake_log.md           # WA/TLE 错误模式记录
      topic_checklist.md       # 知识点覆盖追踪
      progress/                # 目标专属进度追踪

  shared/                      # 跨目标共享内容
    cheatsheets/               # 通用 LLM/ML/项目表达速记资料
    daily/                     # 共享每日计划（YYYY-MM-DD.md）
    exam_memory/               # 自定义 MCP server 与经验库
      server.py                # MCP 工具，经验持久化
      experiences/             # 经验文件（YAML frontmatter + Markdown）
      user_profile.json        # 用户画像（强弱项、偏好）
    progress/                  # 共享进度与 task-board 文件
    prompts/                   # 通用 prompt 模板

  algorithms/                  # 兼容占位；活跃 OJ 资产在 targets/ 下
  exam_memory/                 # 兼容占位；活跃 MCP 代码在 shared/exam_memory/
  progress/                    # 兼容占位；活跃进度在 shared/ 或 targets/ 下
  prompts/                     # Prompt 模板
```

## 适配其他考试

默认使用 `HANDOFF.md` 中配置的目标考试，核心机制可复用：

1. 在 `targets/{target}/sources/` 下放入目标考试的题型分析
2. 更新 `targets/{target}/exam_config.md` 中的题数、分值和时间
3. 将目标专属资料放入 `targets/{target}/cheatsheets/`，可复用资料放入 `shared/cheatsheets/`
4. 修改 `AGENTS.md` 中的 Exam Format 表格

## Contributing

见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License

[MIT](LICENSE)
