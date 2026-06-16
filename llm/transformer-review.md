# Transformer 前向流程复习笔记

> 算法笔试速查 | 只要求能讲清前向流程

---

## 一、Self-Attention 机制（缩放点积注意力）

### 1. 公式

**线性投影：**

$$Q = XW_Q, \quad K = XW_K, \quad V = XW_V$$

**注意力计算：**

$$\text{Attention}(Q,K,V) = \text{softmax}\!\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

### 2. 符号说明

| 符号 | 含义 | 维度 |
|------|------|------|
| $X$ | 输入序列，每个 token 的嵌入向量 | $(n, d_{\text{model}})$ |
| $W_Q, W_K, W_V$ | 可学习的投影矩阵 | $(d_{\text{model}}, d_k)$ |
| $Q, K, V$ | Query、Key、Value 矩阵 | $(n, d_k)$ |
| $QK^T$ | 注意力得分矩阵 | $(n, n)$ |
| $\sqrt{d_k}$ | 缩放因子，$d_k$ 为 Key 的维度 | 标量 |

其中 $n$ 是序列长度，$d_{\text{model}}$ 是模型隐藏维度，$d_k$ 是 Key 的维度。

### 3. 为什么除以 $\sqrt{d_k}$

当 $d_k$ 较大时，$QK^T$ 的元素方差约为 $d_k$，量级随之增大。未经缩放的点积进入 softmax 后，输出趋近 one-hot（某个位置接近 1，其余接近 0），梯度极小，训练难以收敛。除以 $\sqrt{d_k}$ 将方差重新归一化到约 1，使 softmax 处于梯度敏感区间。

### 4. 数值示例（$n=3, d_k=2, d_{\text{model}}=4$）

取 $d_k=2$ 以便手算，$X$ 为 $3\times4$，投影后得到：

$$Q = \begin{pmatrix} 1 & 0 \\ 0 & 1 \\ 1 & 1 \end{pmatrix}, \quad K = \begin{pmatrix} 1 & 0 \\ 0 & 1 \\ 1 & 1 \end{pmatrix}, \quad V = \begin{pmatrix} 1 & 2 \\ 3 & 4 \\ 5 & 6 \end{pmatrix}$$

**Step 1：** 计算 $QK^T$：

$$QK^T = \begin{pmatrix} 1 & 0 & 1 \\ 0 & 1 & 1 \\ 1 & 1 & 2 \end{pmatrix}$$

**Step 2：** 缩放，$\sqrt{d_k}=\sqrt{2}\approx1.414$：

$$\frac{QK^T}{\sqrt{2}} \approx \begin{pmatrix} 0.707 & 0 & 0.707 \\ 0 & 0.707 & 0.707 \\ 0.707 & 0.707 & 1.414 \end{pmatrix}$$

**Step 3：** 对每行做 softmax（以第 1 行为例）：

$e^{0.707}\approx2.028,\; e^{0}=1,\; e^{0.707}\approx2.028$，总和 $\approx5.056$

$\text{softmax} \approx (0.401,\; 0.198,\; 0.401)$

**Step 4：** 加权求和第 1 行输出：

$0.401\times(1,2) + 0.198\times(3,4) + 0.401\times(5,6) = (3.40,\; 4.40)$

对第 2、3 行重复同理，最终得到输出矩阵 $3\times2$。

**核心要点：** Self-Attention 通过 $QK^T$ 度量序列中任意两个位置的相关性，经 softmax 归一化为权重后对 $V$ 加权求和，实现全局信息聚合。

---

## 二、Multi-Head Attention

### 1. 核心公式

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \dots, \text{head}_h)\, W^O$$

其中每个头独立计算：

$$\text{head}_i = \text{Attention}(XW_Q^i,\; XW_K^i,\; XW_V^i)$$

参数矩阵维度：$W_Q^i, W_K^i \in \mathbb{R}^{d_{\text{model}} \times d_k}$，$W_V^i \in \mathbb{R}^{d_{\text{model}} \times d_v}$，$W^O \in \mathbb{R}^{hd_v \times d_{\text{model}}}$。

### 2. 为什么要多头

单头 Attention 只在一种表示子空间中计算相似度，容易被主导模式淹没。多头机制将 $d_{\text{model}}$ 维空间拆成 $h$ 个低维子空间，每个头独立学习一组 $W_Q, W_K, W_V$，从而并行捕获不同类型的语义关系——例如一个头关注句法依存，另一个头关注指代消解，第三个头关注局部 n-gram 搭配。

### 3. 维度关系

$$d_k = d_v = \frac{d_{\text{model}}}{h}$$

$h$ 个头拼接后总维度仍为 $d_{\text{model}}$，与残差连接维度一致。例如 $d_{\text{model}}=512, h=8$，则每个头工作在 $d_k=64$ 维子空间中。

### 4. 输出投影 $W^O$ 的作用

Concat 将 $h$ 个头的输出简单拼接，各子空间特征相互独立。$W^O$ 将拼接结果投影回 $d_{\text{model}}$ 维，使不同头学到的信息发生交互融合，同时适配残差连接和后续层的输入维度。

---

## 三、Position Encoding（位置编码）

### 1. 为什么需要位置编码

Self-Attention 对输入序列具有**置换不变性**（permutation invariant）：打乱 token 顺序，输出不变。必须显式注入位置信息，否则模型无法区分 "猫吃鱼" 和 "鱼吃猫"。

### 2. 正弦/余弦编码公式

$$PE_{(pos, 2i)} = \sin\!\left(\frac{pos}{10000^{2i/d_{model}}}\right), \quad PE_{(pos, 2i+1)} = \cos\!\left(\frac{pos}{10000^{2i/d_{model}}}\right)$$

其中 $pos$ 为 token 位置，$i$ 为维度索引。不同维度对应不同频率的正弦波，从低频到高频逐步编码。

### 3. 为什么选正弦余弦

核心优势：**相对位置可通过线性变换获得**。对任意固定偏移 $k$，存在与 $pos$ 无关的矩阵 $M_k$，使得：

$$PE_{(pos+k)} = M_k \cdot PE_{(pos)}$$

这是因为 $\sin(a+b)$ 和 $\cos(a+b)$ 可展开为 $\sin a, \cos a$ 的线性组合。模型因此能泛化至训练时未见过的序列长度。

### 4. RoPE（旋转位置编码）

**一句话核心**：将位置 $m$ 编码为旋转矩阵 $R_m$，分别作用在 $Q$ 和 $K$ 上，使 $q_m^\top k_n$ 的点积天然只依赖于相对位置 $m-n$：

$$\langle R_m q,\; R_n k \rangle = f(q, k, m-n)$$

二维情形下，$R_m = \begin{pmatrix}\cos m\theta & -\sin m\theta \\ \sin m\theta & \cos m\theta\end{pmatrix}$，高维时按二维子空间分组旋转。

### 5. 可学习 vs 固定位置编码

**固定编码**（如正弦编码）不增加参数、天然支持外推；**可学习编码**（如 BERT）参数化每个位置的向量，表达能力更强但受限于训练长度，外推能力差。RoPE 属于固定编码但兼具外推性。

---

## 四、Transformer Block

### Encoder Block

两个子层，每层带 **残差连接 + LayerNorm**：

$$\text{output} = \text{LayerNorm}(x + \text{SubLayer}(x))$$

> **Pre-Norm vs Post-Norm**：Post-Norm 在子层输出后做 LayerNorm（原始论文，需 warm-up）；Pre-Norm 在子层输入前做 LayerNorm（收敛更稳定，现为主流）。

**FFN** 逐位置独立计算，先升维再降维（通常扩大 4 倍）：

$$\text{FFN}(x) = \max(0,\, xW_1 + b_1)\,W_2 + b_2$$

其中 $x \in \mathbb{R}^{d}$，$W_1 \in \mathbb{R}^{d \times 4d}$，$W_2 \in \mathbb{R}^{4d \times d}$。激活函数原始用 ReLU，后续变体常用 GELU / SwiGLU。

### Decoder Block

三个子层：

1. **Masked Self-Attention**：对当前位置之后施加 causal mask（上三角置为 $-\infty$），保证自回归性质：

$$\text{Attention}(Q,K,V) = \text{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}} + M\right)V, \quad M_{ij} = \begin{cases} 0 & i \ge j \\ -\infty & i < j \end{cases}$$

2. **Cross-Attention**：**Q** 来自 Decoder 上一层输出，**K、V** 来自 Encoder 最终输出，让 Decoder 能"查询"源序列信息。

3. **FFN**：与 Encoder 相同。

推理时通过 **KV Cache** 缓存历史 K/V，避免重复计算。

---

## 五、完整前向流程（Encoder-Decoder 架构）

### 符号约定

| 符号 | 含义 |
|------|------|
| $d_{\text{model}}$ | 模型隐藏维度（如 512） |
| $d_k = d_{\text{model}}/h$ | 每个头的维度 |
| $d_{\text{ff}} = 4 \cdot d_{\text{model}}$ | FFN 中间维度 |
| $V_{\text{vocab}}$ | 词表大小 |
| $B, L_{src}, L_{tgt}$ | batch size、源/目标序列长度 |

### Step 1：输入嵌入

**源序列**：token IDs 经 embedding lookup 后乘以 $\sqrt{d_{model}}$，加上正弦位置编码：

$$X = \text{Embed}(x) \cdot \sqrt{d_{model}} + PE \in \mathbb{R}^{B \times L_{src} \times d_{model}}$$

**目标序列**：训练时将 target 右移一位（起始填 `<bos>`），同样做 embedding + PE：

$$Y = \text{Embed}(y_{shifted}) \cdot \sqrt{d_{model}} + PE \in \mathbb{R}^{B \times L_{tgt} \times d_{model}}$$

### Step 2：Encoder（×N 层）

每层两个子层，均带残差 + LN：

**(a) Multi-Head Self-Attention**（Q/K/V 同源）

$$\text{MHSA}(X) = \text{Concat}(\text{head}_1,\dots,\text{head}_h) W^O, \quad X' = \text{LN}(X + \text{MHSA}(X))$$

**(b) FFN**

$$E = \text{LN}(X' + \text{FFN}(X')), \quad E \in \mathbb{R}^{B \times L_{src} \times d_{model}}$$

### Step 3：Decoder（×N 层）

每层三个子层，均带残差 + LN：

**(a) Masked Self-Attention**：causal mask 保证位置 $i$ 只能 attend 到 $\leq i$ 的位置

$$Y' = \text{LN}(Y + \text{MaskedMHSA}(Y))$$

**(b) Cross-Attention**：$Q = Y'W^Q$（来自 Decoder），$K = EW^K, V = EW^V$（来自 Encoder 输出）

$$Y'' = \text{LN}(Y' + \text{CrossAttn}(Y', E))$$

**(c) FFN**

$$D = \text{LN}(Y'' + \text{FFN}(Y'')), \quad D \in \mathbb{R}^{B \times L_{tgt} \times d_{model}}$$

### Step 4：输出层

$$\text{logits} = D \cdot W_{out} + b_{out} \in \mathbb{R}^{B \times L_{tgt} \times V_{vocab}}$$

$$P = \text{softmax}(\text{logits},\ \text{dim}=-1)$$

> $W_{out}$ 常与输入 embedding 共享权重（weight tying）。

### 维度速查表

| 位置 | 维度 | 说明 |
|------|------|------|
| Embedding 输出 | $(B, L, d_{model})$ | 乘 $\sqrt{d_{model}}$ 缩放 |
| Attention $Q,K,V$ | $(B, h, L, d_k)$ | $d_k = d_{model}/h$ |
| FFN 中间层 | $(B, L, d_{ff})$ | $d_{ff}=4d_{model}$ |
| 输出 logits | $(B, L_{tgt}, V_{vocab})$ | softmax 得概率分布 |

---

## 六、PyTorch 伪代码

```python
import torch, torch.nn as nn, math

class Transformer(nn.Module):
    def __init__(self, vocab_size, d_model=512, nhead=8,
                 num_layers=6, d_ff=2048, max_len=512):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, d_model)
        self.pos_enc = nn.Embedding(max_len, d_model)  # 可替换为正弦编码
        encoder_layer = nn.TransformerEncoderLayer(d_model, nhead, d_ff)
        decoder_layer = nn.TransformerDecoderLayer(d_model, nhead, d_ff)
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers)
        self.decoder = nn.TransformerDecoder(decoder_layer, num_layers)
        self.fc_out = nn.Linear(d_model, vocab_size)

    def forward(self, src, tgt_shifted):
        # 1. 嵌入
        src_emb = self.embed(src) * math.sqrt(self.fc_out.in_features)
        tgt_emb = self.embed(tgt_shifted) * math.sqrt(self.fc_out.in_features)
        src_emb += self.pos_enc(torch.arange(src.size(1)))
        tgt_emb += self.pos_enc(torch.arange(tgt_shifted.size(1)))
        # 2. Encoder
        memory = self.encoder(src_emb.transpose(0, 1))
        # 3. Decoder（含 causal mask）
        tgt_mask = nn.Transformer.generate_square_subsequent_mask(tgt_shifted.size(1))
        dec_out = self.decoder(tgt_emb.transpose(0, 1), memory, tgt_mask)
        # 4. 输出层
        logits = self.fc_out(dec_out.transpose(0, 1))  # (B, L_tgt, V)
        return torch.softmax(logits, dim=-1)
```

---

## 速记口诀

- **Self-Attention**：Q·K 算相似度 → 缩放 → softmax 得权重 → 加权求 V
- **Multi-Head**：拆成 h 个头各自算 → 拼接 → W^O 融合
- **Position Encoding**：Attention 本身不含位置信息，必须显式注入
- **Encoder**：自注意 + FFN，残差 + Norm 不可少，FFN 升四倍再降回
- **Decoder**：掩码自注意 + 交叉注意 + FFN
- **前向流程**：Embed(+scale+PE) → N×Encoder → N×Decoder → Linear → Softmax
