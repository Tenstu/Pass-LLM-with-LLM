# LLM Core Cheatsheet

## Transformer

- Input tokens become embeddings plus positional information.
- Self-attention builds Q, K, V from hidden states.
- Attention score is roughly `softmax(QK^T / sqrt(d)) V`.
- Causal LM uses a mask so each token can only attend to previous tokens.
- Multi-head attention lets different heads focus on different relations.
- FFN provides nonlinear transformation after attention.
- Residual connections and LayerNorm stabilize training.
- RoPE encodes relative position through rotation, useful for extrapolating context length with proper scaling.

Quick answer: Transformer replaces recurrence with attention, so each token can directly aggregate context and training can be parallelized.

## LLaMA3 Architecture Details（选择题高频）

- **RoPE（Rotary Position Embedding）**：将位置信息编码为旋转矩阵，支持相对位置外推，不需要学习位置嵌入。
- **GQA（Grouped Query Attention）**：多个 Query head 共享一组 Key/Value head，平衡 MHA 的表达力和 MQA 的效率。
- **SwiGLU 激活函数**：替代 ReLU 的 FFN 激活，`SwiGLU(x) = Swish(xW1) ⊙ (xW2)`，效果通常优于 ReLU/GELU。
- **RMSNorm**：替代 LayerNorm，去掉均值中心化只做缩放，计算更快且训练更稳定。
- **无偏置（No Bias）**：线性层和 LayerNorm 均不使用偏置项，减少参数和计算。
- **超大上下文窗口**：LLaMA3 支持 128K context，通过 RoPE 频率缩放实现。

Quick answer: LLaMA3 相比 LLaMA2 的主要改进是 GQA 减少 KV cache 显存、SwiGLU 提升 FFN 表达力、RMSNorm 加速训练、RoPE 支持更长上下文。

## SFT

- Supervised fine-tuning trains the model on instruction-response examples.
- Loss is usually next-token cross entropy on target responses.
- Key issues: data quality, format consistency, response masking, packing, overfitting, evaluation leakage.
- In interview: emphasize that SFT teaches behavior/style, not new deep factual knowledge reliably.

## LoRA And QLoRA

- LoRA freezes base weights and learns a low-rank update `Delta W = B A`.
- Common target modules: attention projection layers such as `q_proj`, `k_proj`, `v_proj`, `o_proj`, and sometimes MLP projections.
- Important knobs: rank `r`, alpha, dropout, target modules, learning rate.
- QLoRA quantizes the base model, commonly to 4-bit, and trains LoRA adapters to reduce memory.
- QLoRA tradeoff: much lower VRAM, possible speed/accuracy tradeoffs and more dependency friction.

Quick answer: LoRA is parameter-efficient fine-tuning; QLoRA adds low-bit base-model quantization so small GPUs can fine-tune larger models.

## RLHF And DPO

- RLHF pipeline: collect preference data, train reward model, optimize policy with PPO or similar methods.
- Advantages: aligns outputs with human preference beyond SFT imitation.
- Risks: reward hacking, instability, expensive human feedback.
- DPO directly optimizes preference pairs without training a separate reward model in the same way.
- DPO is simpler and often easier to reproduce, but still depends heavily on preference data quality.

Quick answer: SFT teaches the model to follow examples; RLHF/DPO push the model toward preferred behavior.

## RAG

- Pipeline: query rewrite, retrieve, rerank, generate, cite, verify.
- Key choices: chunk size, embedding model, index, top-k, reranker, prompt format.
- Failure types: retrieval miss, irrelevant context, context conflict, generation hallucination.
- Evaluation: recall of gold evidence, answer correctness, citation faithfulness, latency.

## Agent

- Components: planner, tool caller, memory, executor, verifier.
- Strength: decomposes multi-step tasks and uses external tools.
- Failure modes: wrong plan, tool misuse, stale memory, infinite loops, hallucinated tool results.
- Guardrails: tool schema, step budget, validation, logging, human confirmation for risky actions.

## KV Cache And Inference

- During decode, the model repeatedly generates one token at a time.
- KV cache stores previous tokens' key/value tensors, avoiding recomputation of the full prefix.
- Prefill processes the prompt; decode generates new tokens.
- Bottlenecks: memory bandwidth, batch scheduling, long-context memory, latency.
- Optimizations: continuous batching, PagedAttention, quantization, tensor parallelism, speculative decoding.
- vLLM is known for efficient serving with PagedAttention and high-throughput batching.

Quick answer: KV cache speeds autoregressive decoding by reusing historical attention keys and values.

## Evaluation

- Offline metrics: accuracy, F1, BLEU/ROUGE for limited tasks, retrieval recall, latency, cost.
- Human evaluation: helpfulness, correctness, harmlessness, style, task success.
- LLM-as-judge: scalable but needs calibration and bias checks.
- Online evaluation: A/B test, business metrics, complaint rate, conversion, retention.
- Safety checks: hallucination, prompt injection, privacy, toxic content, refusal quality.

## GNN Quick Reference（详见 llm/gnn_diffusion_cheatsheet.md）

- **图表示**：邻接矩阵 A、度矩阵 D、拉普拉斯矩阵 L = D - A。
- **GCN**：聚合邻居特征后线性变换，`H' = σ(D̃^(-1/2) Ã D̃^(-1/2) H W)`。
- **GAT**：用注意力权重加权聚合邻居，权重可学习，比 GCN 更灵活。
- **消息传递**：message（构造消息）→ aggregate（聚合邻居消息）→ update（更新节点表示）。
- **任务粒度**：节点级（分类/回归）、边级（链接预测）、图级（分子性质预测）。
- **AI for Science 应用**：分子性质预测、蛋白质结构、交通流量、气象网格建模。

## Diffusion Model Quick Reference（详见 llm/gnn_diffusion_cheatsheet.md）

- **核心思想**：前向逐步加噪 → 反向学习去噪。
- **前向过程**：`q(x_t | x_{t-1}) = N(x_t; √(1-β_t) x_{t-1}, β_t I)`，逐步加高斯噪声。
- **反向过程**：学习 `p(x_{t-1} | x_t)`，从纯噪声恢复数据。
- **DDPM 训练**：网络预测噪声 ε，损失为 `||ε - ε_θ(x_t, t)||²`。
- **vs GAN**：训练更稳定，生成多样性好，但推理慢（需多步去噪）。
- **条件生成**：Classifier-Free Guidance 混合条件/无条件预测，控制生成方向。
- **Latent Diffusion**：在潜空间做扩散，大幅降低计算量，Stable Diffusion 的基础。
- **AI for Science 应用**：气象预测（GenCast）、分子生成、材料设计、科学模拟。

## Math Foundations Quick Reference（详见 llm/math_fundamentals.md）

- **线性代数**：矩阵乘法维度、特征值分解 A = PΛP⁻¹、SVD = UΣV^T、PCA 取最大特征值方向。
- **概率**：贝叶斯 P(A|B) = P(B|A)P(A)/P(B)、常见分布性质、MLE 最大似然 vs MAP 最大后验。
- **微积分**：链式法则（反向传播基础）、梯度 ∇f 方向为最快上升、凸函数局部最优=全局最优。
- **DL 数学**：softmax 归一化、交叉熵 = -Σ y log ŷ、dW = X^T dZ、BatchNorm 训练用 batch 统计量。

## Last-Day Oral Drill

1. Explain Transformer in 2 minutes.
2. Explain why LoRA saves memory.
3. Compare SFT, RLHF, and DPO.
4. Explain RAG failure modes.
5. Explain KV cache and prefill/decode.
6. **Map your Agent project to an AI for Science scenario (e.g. scientific literature review, experimental data analysis).**
7. **Explain LLaMA3 vs LLaMA2 improvements (GQA/RoPE/SwiGLU/RMSNorm).**
8. **Explain GNN message passing in 2 minutes.**
9. **Explain diffusion model forward/reverse process.**
10. **Recall 5 math formulas for choice questions (Bayes, SVD, chain rule, softmax, cross entropy).**

## AI Lab Context Quick Reference（详见 llm/ai_lab_context.md）

- **InternLM（书生大语言模型）**：上海 AI 实验室主力 LLM，开源，支持长上下文。
- **InternVL（书生视觉语言模型）**：多模态模型，图文理解能力。
- **OpenCompass**：开源大模型评测体系/平台。
- **AI for Science**：用 AI 方法解决科学问题（气象、分子、材料、地球空间）。
- **AGI 方向**：实验室以通用人工智能为长期目标，强调多模态、长上下文、工具使用。

