# Minimal SFT / LoRA Project For 8G VRAM

## Purpose

This is a small hands-on proof, not the main exam-prep path. It should support interview discussion if needed. Do not let it consume algorithm practice time.

## Time Cap

- Local setup cap: 1 hour.
- If CUDA, bitsandbytes, PyTorch, or driver issues block progress, switch to Colab or keep this as a documented plan.
- During the exam week, never sacrifice a mock exam for this mini-project.

## Minimal Goal

Fine-tune a small instruction model with LoRA on 50-200 examples related to academic writing assistance or tool-using Agent prompts, then compare before/after responses.

## Suggested Model Scale

- Local RTX 5060 8G: prefer a 0.5B-1.5B instruct model.
- If using 4-bit QLoRA and dependencies work: try a 1.5B-3B model.
- If local setup is unstable: use Colab with a known notebook-style workflow.

## Dataset Sketch

Create JSONL examples like:

```json
{"instruction":"将论文写作需求拆成可执行 Agent 步骤。","input":"用户要检查 UCAS 学位论文格式、引用和章节逻辑。","output":"先解析论文结构，再检查格式规则，然后核对引用，最后生成修改建议和风险清单。"}
```

Good examples should reflect:

- Multi-turn writing assistance.
- Tool-use planning.
- Quality-control checklists.
- RAG or citation verification behavior.
- Clear refusal when evidence is insufficient.

## Minimal Workflow

1. Pick a tiny instruct model and tokenizer.
2. Format data as instruction/input/output.
3. Train LoRA adapters for 1-3 epochs.
4. Save adapters only.
5. Run 5 fixed prompts before and after training.
6. Write a short result note: what improved, what failed, what you would evaluate next.

## Hyperparameter Starting Point

| Setting | Suggested Value |
|---|---|
| LoRA rank | 8 or 16 |
| LoRA alpha | 16 or 32 |
| Dropout | 0.05 |
| Learning rate | 1e-4 to 2e-4 |
| Batch size | 1-2 |
| Gradient accumulation | 8-16 |
| Epochs | 1-3 |
| Max length | 512-1024 |

## Interview-Safe Summary

可以这样表达：

```text
我为了补足实操经验，设计过一个小规模 LoRA/SFT 实验：用论文写作 Agent 场景构造几十到两百条 instruction 数据，在小模型上只训练 LoRA adapter，对比训练前后在任务拆解、工具调用规划、质量检查输出上的变化。重点不是追求大模型效果，而是理解数据格式、显存约束、参数高效微调、评测和失败案例。
```

## What Not To Do This Week

- Do not train a large model from scratch.
- Do not spend hours debugging GPU dependencies.
- Do not build a full deployment stack.
- Do not let the mini-project replace OJ practice.

