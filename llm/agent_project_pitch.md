# Agent Project Pitch

## Positioning

The user's existing projects can be framed as applied LLM/Agent systems for academic writing productivity and quality control:

- `UCAS-Thesis-AI-Delivery-Kit`
- `ChineseResearchLaTeX`

Use this framing carefully: verify exact repo features before interviews, and avoid claiming training or deployment work that was not actually done.

## 90-Second Pitch

```text
我做过一套面向 UCAS 学位论文写作的 AI 辅助交付工具，核心不是简单生成文本，而是把论文写作拆成多轮交互、规则检查、工具调用和质量控制流程。项目里我关注的是如何把用户的写作目标转成可执行步骤，例如章节结构检查、格式规范提醒、引用和材料整理、以及最终修改建议。

这个项目和大模型算法岗相关的点在于：第一，它涉及 Agent 式任务分解和多轮上下文管理；第二，它需要让模型输出可验证、可追踪的建议，而不是自由发挥；第三，它天然适合接 RAG、规则校验器和人工反馈闭环。后续如果扩展到更广泛的 AI 应用场景，类似能力可以用于智能问答、知识库管理和自动化内容处理。
```

## Algorithm-Role Emphasis

强调这些能力：

- 将复杂任务拆成可执行 pipeline。
- 设计 prompt、工具调用和检查清单。
- 关注输出质量、可验证性和失败模式。
- 能把学术写作场景的能力迁移到智能问答、知识库管理和自动化内容处理等更广泛的 AI 应用方向。
- 有 Python 脚本和自动化经验，正在补齐 OJ 和模型微调实操。

避免这些说法：

- 不要说自己做了大规模训练，除非确实做过。
- 不要把项目说成完整商业级 Agent 平台。
- 不要只讲“帮我写论文”，要讲任务分解、工具使用、质量控制。

## Possible Interview Questions

### Q1: 你的项目里 Agent 具体体现在哪里？

答题要点：任务拆解、多轮上下文、工具调用、检查器、最终汇总。强调不是让模型一次性生成，而是通过步骤约束质量。

### Q2: 如果要把它升级成更强的大模型项目，你会做什么？

答题要点：构造指令数据，做小规模 LoRA/SFT，接入 RAG，加入自动评测集，记录人工反馈，评估幻觉率和任务完成率。

### Q3: 如何将项目能力应用到 AI for Science 场景？

答题要点：将论文写作辅助能力迁移到科研数据处理、文献综述自动化、实验报告生成、科学知识问答等 AI for Science 方向。强调 RAG 检索学术论文、Agent 式实验步骤规划、质量控制确保科学准确性。

