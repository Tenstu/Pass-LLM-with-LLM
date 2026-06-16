# Mistake Log（按主题分类）

> **Harness 反馈回路的核心**：这个文件是 `algo-annotation` skill 的 `# [防错]` 标记数据源。
> 每道 WA/TLE 题必须在这里录入一条规则，annotation 会自动读取并标注到代码上。
> 考前只读这个文件。每行 = 一道题的防错规则，一行一规则。
> 详细解题过程见对应 `daily/YYYY-MM-DD.md` 的 Problem Log。
> 日期格式：MM-DD。

## Mastery 级别参考

| 值 | 含义 | 触发条件 | Redo Date |
|----|------|---------|-----------|
| WA | 答错 | 选错或漏选 | +1 天 |
| lucky_pass | 盲区（猜对） | correct + confidence = 完全不懂 | 当天 |
| partial | 半懂（猜对） | correct + confidence = 猜的有道理 | +1 天 |
| confirmed | 已掌握 | correct + confidence = 确定会 | 不设 |
| skip | 跳过 | 用户跳过此题 | +1 天 |

---

## Root Cause 汇总（考前重点看高频标签）

| Tag | 出现次数 | 说明 |
|-----|---------|------|
| pattern | 7 | 看到题型不知道怎么下笔（行列式、贝叶斯、KV cache公式、GQA、RAG流程、CNN感受野、偏差-方差） |
| proof | 15 | 概念记混或性质记错（对称矩阵、独立变量、CFG、GAT、过平滑、正交vs正定、GAT多头、QLoRA、位置编码、缩放因子、梯度消失、KV Cache/Flash、LoRA参数、Softmax全选、独立vs不相关） |
| python | 1 | 数值/常识记错（正态分布范围） |

---

## 考前 Day 1 冲刺只看这 15 条（按高频排序）

### 线性代数（4 条）
1. 对称矩阵可逆 → 逆也是对称的
2. A² 特征值 = λᵢ²，排序不变——最小是 λₙ² 不是 λ₁²
3. 正交矩阵特征值模为1可含复数（旋转 e^{iθ}）；正定矩阵特征值才全正实数
4. SVD 奇异值个数 = min(m,n)，不是 max(m,n)；Σ 维度 m×n 但非零奇异值只有 min(m,n) 个

### 概率统计（2 条）
5. 贝叶斯公式分子分母都算，三步走
6. 独立 ⇒ 不相关，但不相关 ⇏ 独立。E 可加不需要独立，Var 可加需要独立。

### 深度学习 / DL 基础（3 条）
7. Softmax：四选项全对（A溢出 B减max C平移不变 D CE梯度ŷ-y）
8. 3×3 卷积 n 层感受野 = 2n+1（3层 = 7×7），不是 n²
9. ReLU 缓解但不能"完全避免"梯度消失——Dead ReLU（x≤0梯度=0）

### Transformer / LLM 架构（3 条）
10. 位置编码只在输入层加一次，不是每层
11. 缩放因子 √d_k 三选项全对（方差归一化 + 防one-hot + 数学依据）
12. LoRA 参数 = d×r + r×k；QLoRA = 降显存不是提效果

### 推理优化（2 条）
13. KV cache 公式 = 2(K+V) × 层数 × 头数 × 头维度 × 序列长度 × 字节数
14. FlashAttention 不改 KV Cache 大小，只改 IO 模式（tiling）

### GNN / 应用（1 条）
15. 过平滑 ≠ 过拟合；GAT 多头中间 concat，输出 mean

---

## 掌握进度速查

> 由 choice-q-drill 每次答题后更新。更新频率：每次 drill session 结束。

| 知识点 | Mastery | 错误次数 | 盲区次数 | 最近状态 |
|--------|---------|---------|---------|---------|
| 行列式乘法 | confirmed | 1 | 0 | WA→confirmed (06-15) |
| 对称矩阵逆 | confirmed | 1 | 0 | WA→confirmed (06-15) |
| SVD奇异值 | struggling | 1 | 1 | WA→struggling (06-15) |
| 贝叶斯公式 | confirmed | 1 | 0 | WA→confirmed (06-14) |
| 独立vs不相关 | struggling | 1 | 1 | WA→struggling (06-15) |
| 位置编码 | struggling | 1 | 0 | WA→struggling (06-15) |
| 缩放因子√d_k | confirmed | 1 | 0 | WA→confirmed (06-15) |
| CNN感受野 | struggling | 1 | 0 | WA→struggling (06-15) |
| 梯度消失 | confirmed | 1 | 0 | WA→confirmed (06-15) |
| KV Cache公式 | confirmed | 1 | 0 | WA→confirmed (06-15) |
| GQA/MQA | confirmed | 1 | 0 | WA→confirmed (06-15) |
| QLoRA目的 | confirmed | 1 | 0 | WA→confirmed (06-15) |
| GNN过平滑 | confirmed | 1 | 0 | WA→confirmed (06-15) |
| GAT多头 | confirmed | 1 | 0 | WA→confirmed (06-15) |
| RAG流程 | confirmed | 1 | 0 | WA→confirmed (06-15) |
| Softmax数值稳定 | confirmed | 1 | 0 | WA→confirmed (06-14) |
| CFG条件生成 | confirmed | 1 | 0 | WA→confirmed (06-14) |
| 偏差-方差 | blind_spot | 1 | 0 | WA→blind_spot (06-15) |
| SGD优化 | blind_spot | 1 | 1 | WA→blind_spot (06-15) |
| 矩阵条件数 | blind_spot | 1 | 0 | WA→blind_spot (06-15) |
| SwiGLU激活 | blind_spot | 1 | 0 | WA→blind_spot (06-15) |
| 量化策略 | blind_spot | 1 | 0 | WA→blind_spot (06-15) |
| 正交vs正定 | struggling | 1 | 1 | WA→struggling (06-15) |

---

## 线性代数 / 矩阵

| Date | Problem | Topic | Result | Mastery | Root Cause | Fix Rule | Redo Date |
|---|---|---|---|---|---|---|---|
| 06-14 | Q1 det(A²) | 行列式乘法 | WA | WA | pattern | det(AB) = det(A)det(B)，所以 det(A²) = det(A)² | 06-15 |
| 06-14 | Q2 对称矩阵逆 | 逆矩阵对称性 | WA | WA | proof | A 对称可逆 → A⁻¹ = (A⁻¹)ᵀ = (Aᵀ)⁻¹ = A⁻¹，逆也对称 | 06-15 |
| 06-15 | Q1 A²特征值排序 | 特征值排序 | WA | WA | pattern | A²特征值=λᵢ²，排序不变——最小是λₙ²不是λ₁² | 06-16 |
| 06-15 | Q9 正交vs正定 | 正交矩阵特征值 | WA | WA | proof | 正交矩阵特征值模为1但可含复数(如旋转e^{iθ})；正定矩阵特征值才全正实数 | 06-16 |
| 06-15 | Q2 SVD奇异值个数 | SVD 奇异值 | WA | WA | pattern | 奇异值个数=min(m,n)，不是max(m,n)；Σ维度m×n但非零奇异值只有min(m,n)个 | 06-16 |

### 防错规则：看到"对称矩阵"→ 自动想 (Aᵀ)ᵀ = A 和 (A⁻¹)ᵀ = A⁻¹ 两条。
### 防错规则：SVD 中 Σ 的维度是 m×n，但非零奇异值只有 min(m,n) 个。不要混淆矩阵维度和奇异值个数。

---

## 概率统计

| Date | Problem | Topic | Result | Mastery | Root Cause | Fix Rule | Redo Date |
|---|---|---|---|---|---|---|---|
| 06-14 | Q4 贝叶斯 | 贝叶斯公式 | WA | WA | pattern | P(A\|B) = P(B\|A)P(A) / P(B)，必须同时算分子分母，不能只看分子 | 06-15 |
| 06-14 | Q5 正态分布 | 正态分布 | WA | WA | python | 68-95-99.7 法则：P(\|X\|>1)≈0.32, P(\|X\|>2)≈0.045, P(X>2)≈0.0228 | 06-15 |
| 06-14 | Q13 独立随机变量 | 独立与期望/方差 | WA | WA | proof | 独立 ⇒ E[XY]=E[X]E[Y], Var(X+Y)=Var(X)+Var(Y)；但 E[X+Y]=E[X]+E[Y] 不需要独立 | 06-15 |
| 06-15 | Q7 独立与不相关 | 独立 vs 不相关 | WA | WA | proof | 独立⇒E[XY]=E[X]E[Y]且Var(X+Y)=Var(X)+Var(Y)；但不相关⇏独立（E[XY]=E[X]E[Y]仅说明线性无关） | 06-16 |

### 防错规则：贝叶斯题三步走——(1)写贝叶斯公式 (2)算分子 (3)算分母 P(B)（用全概率）。
### 防错规则：独立 ⇒ 不相关，但不相关 ⇏ 独立。E 可加不需要独立，Var 可加需要独立。

---

## Transformer / 注意力机制

| Date | Problem | Topic | Result | Mastery | Root Cause | Fix Rule | Redo Date |
|---|---|---|---|---|---|---|---|
| 06-15 | Q5 位置编码 | 位置编码/RoPE | WA | WA | proof | 位置编码只在输入层添加一次，不是每层；RoPE通过旋转Q/K编码相对位置 | 06-16 |
| 06-15 | Q6 缩放因子 | 注意力缩放因子 | WA | WA | proof | √d_k使点积方差归一化（var∝d_k），防止softmax退化；A/B/C三选项全对选D | 06-16 |

### 防错规则：位置编码 vs 逐层归一化——位置编码只加一次，LayerNorm 才是每层都有。RoPE 通过旋转 Q/K 实现，不需要单独的编码向量。
### 防错规则：缩放因子 √d_k——方差与 d_k 成正比，除后归一化；A(方差归一化) B(防one-hot) C(数学依据) 三选项全对。

---

## 机器学习 / 模型评估

| Date | Problem | Topic | Result | Mastery | Root Cause | Fix Rule | Redo Date |
|---|---|---|---|---|---|---|---|
| 06-15 | Q13 偏差方差权衡 | 偏差-方差权衡 | WA | WA | pattern | 高偏差→欠拟合，高方差→过拟合；增加数据减方差不减偏差 | 06-16 |

### 防错规则：增加训练数据减少方差，不减偏差。减少偏差需要更强的模型或更好的特征。正则化→增偏差减方差。

---

## 深度学习 / ML

| Date | Problem | Topic | Result | Mastery | Root Cause | Fix Rule | Redo Date |
|---|---|---|---|---|---|---|---|
| 06-14 | Q7 Softmax | 数值稳定性 | WA | WA | proof | 数值稳定实现：先减最大值再 exp；平移不变性 softmax(z+c) 对常量 c 成立 | 06-15 |
| 06-15 | Q14 Softmax全选项 | Softmax 数值稳定/性质 | WA | WA | proof | Softmax四选项全对：溢出风险(A)、减max实现(B)、平移不变性(C)、CE梯度ŷ-y(D) | 06-16 |
| 06-15 | Q3 CNN感受野 | CNN 感受野 | WA | WA | pattern | 3×3卷积堆叠n层感受野=2n+1（递推RF=RF_prev+(k-1)，3层=7×7） | 06-16 |
| 06-15 | Q8 梯度消失 | 梯度消失/爆炸 | WA | WA | proof | ReLU不能"完全避免"梯度消失（Dead ReLU问题）；残差连接和梯度裁剪是有效手段 | 06-16 |

### 防错规则：Softmax 题先看"数值稳定"→ 减 max 是必考点。
### 防错规则：Softmax 选项逐一验证——A(溢出) B(减max) C(平移不变) D(CE梯度) 全部正确时选全选。
### 防错规则：感受野递推 RF = RF_prev + (k-1)，3×3 每层 +2，3层 = 7×7，不是 9×9。
### 防错规则：ReLU 缓解但不能"完全避免"梯度消失——Dead ReLU（x≤0梯度=0）和深层负值累积仍是问题。

---

## 扩散模型

| Date | Problem | Topic | Result | Mastery | Root Cause | Fix Rule | Redo Date |
|---|---|---|---|---|---|---|---|
| 06-14 | Q14 DDPM/CFG | 条件生成 | WA | WA | proof | CFG 不需要额外分类器：ε' = ε_uncond + s·(ε_cond - ε_uncond) | 06-15 |

### 防错规则：看到 CFG → 想到"线性外推"，不需要分类器。

---

## GNN

| Date | Problem | Topic | Result | Mastery | Root Cause | Fix Rule | Redo Date |
|---|---|---|---|---|---|---|---|
| 06-14 | Q15 GNN 消息传递 | GAT/GNN 框架 | WA | WA | proof | GAT 注意力权重是**可学习的**（通过训练），不是固定由度决定 | 06-15 |
| 06-15 | Q3 过平滑vs过拟合 | GNN 过平滑 | WA | WA | proof | 过平滑=节点表征趋同（表达力退化），不是过拟合；增加边/层数会加剧 | 06-16 |
| 06-15 | Q13 GAT多头策略 | GAT 多头注意力 | WA | WA | proof | GAT多头：中间层用concat，输出层用mean（平均），不是全concat | 06-16 |

### 防错规则：GAT vs GCN → GCN 权重固定（度归一化），GAT 权重可学习（注意力机制）。
### 防错规则：GAT 多头：中间 concat，输出 mean。

---

## 推理优化 / 架构计算

| Date | Problem | Topic | Result | Mastery | Root Cause | Fix Rule | Redo Date |
|---|---|---|---|---|---|---|---|
| 06-15 | Q5 GQA/MQA/MHA | GQA KV cache 计算 | WA | WA | pattern | GQA=折中(如64Q→8KV，cache减到1/8)；MQA=极端(1个KV，1/64) | 06-16 |
| 06-15 | Q6 KV Cache 显存 | KV Cache 公式 | WA | WA | pattern | 公式=2×layers×heads×head_dim×seq_len×bytes；别忘乘2(K+V)和层数 | 06-16 |
| 06-15 | Q12 QLoRA 目的 | LoRA/QLoRA | WA | WA | proof | QLoRA 核心是降显存（4-bit量化），不是提效果 | 06-16 |
| 06-15 | Q10 KV Cache/Flash | KV Cache / FlashAttention | WA | WA | proof | FlashAttention改IO模式(HBM↔SRAM)，不改KV Cache大小；KV Cache减小靠GQA/MQA | 06-16 |
| 06-15 | Q11 LoRA参数效率 | LoRA 参数效率 | WA | WA | proof | LoRA参数=d×r+r×k；QLoRA=降显存不是提效果；GQA=MQA极端情况(1个KV head) | 06-16 |

### 防错规则：KV cache 公式五要素——2(K+V) × 层数 × 头数 × 头维度 × 序列长度 × 字节数。GQA 8个KV头=减到1/8，MQA 1个KV头=减到1/64。
### 防错规则：FlashAttention 不改 KV Cache 大小，只改内存访问模式（tiling 分块）。KV Cache 减小靠 GQA/MQA。
### 防错规则：LoRA 参数量 = d×r + r×k；QLoRA = 降显存（4-bit量化），不是提效果。

---

## RAG / 应用层

| Date | Problem | Topic | Result | Mastery | Root Cause | Fix Rule | Redo Date |
|---|---|---|---|---|---|---|---|
| 06-15 | Q8 RAG 流程排序 | RAG 架构 | WA | WA | pattern | 标准流程：Chunk→Embed→Retrieval(粗排)→Rerank(精排)→LLM生成 | 06-16 |

### 防错规则：Rerank(精排/Cross-Encoder) 在 Retrieval(粗排/Bi-Encoder) 之后，LLM 生成之前。
