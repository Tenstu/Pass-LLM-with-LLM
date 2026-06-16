# Transformer 完整前向传播流程笔记

## 1. 输入嵌入层

**源序列**：token IDs $x \in \mathbb{R}^{B \times L_{src}}$，经 embedding lookup 后乘以 $\sqrt{d_{model}}$，加上正弦位置编码：

$$X = \text{Embed}(x) \cdot \sqrt{d_{model}} + PE \in \mathbb{R}^{B \times L_{src} \times d_{model}}$$

**目标序列**：训练时将 target 右移一位（去掉末尾 token，起始填 `<bos>`），同样做 embedding + PE：

$$Y = \text{Embed}(y_{shifted}) \cdot \sqrt{d_{model}} + PE \in \mathbb{R}^{B \times L_{tgt} \times d_{model}}$$

---

## 2. Encoder（×N 层）

每层包含两个子层，均使用 **残差连接 + LayerNorm**（Post-LN）：

### (a) Multi-Head Self-Attention

$$Q = XW^Q,\quad K = XW^K,\quad V = XW^V \quad \in \mathbb{R}^{B \times L_{src} \times d_k}$$

$$\text{head}_i = \text{softmax}\!\left(\frac{Q_i K_i^T}{\sqrt{d_k}}\right) V_i$$

$$\text{MHSA}(X) = \text{Concat}(\text{head}_1,\dots,\text{head}_h) W^O \in \mathbb{R}^{B \times L_{src} \times d_{model}}$$

输出经残差 + LN：$X' = \text{LN}(X + \text{MHSA}(X))$

### (b) Feed-Forward Network

$$\text{FFN}(X') = \text{ReLU}(X' W_1 + b_1) W_2 + b_2$$

其中 $W_1 \in \mathbb{R}^{d_{model} \times d_{ff}}$，$W_2 \in \mathbb{R}^{d_{ff} \times d_{model}}$，通常 $d_{ff}=4 \cdot d_{model}$。

输出：$E = \text{LN}(X' + \text{FFN}(X')) \in \mathbb{R}^{B \times L_{src} \times d_{model}}$

---

## 3. Decoder（×N 层）

每层三个子层，均带残差 + LN：

### (a) Masked Multi-Head Self-Attention

与 Encoder 相同，但 softmax 前对 attention matrix 加**上三角 mask**（$\text{mask}_{ij}=-\infty$ 当 $j>i$），保证位置 $i$ 只能 attend 到 $\leq i$ 的位置。输出：$Y' = \text{LN}(Y + \text{MaskedMHSA}(Y))$

### (b) Cross-Attention

$Q = Y' W^Q$（来自 Decoder），$K = E W^K$，$V = E W^V$（来自 Encoder 输出）。维度不变，输出：$Y'' = \text{LN}(Y' + \text{CrossAttn}(Y', E))$

### (c) Feed-Forward Network

同 Encoder FFN。输出：$D = \text{LN}(Y'' + \text{FFN}(Y'')) \in \mathbb{R}^{B \times L_{tgt} \times d_{model}}$

---

## 4. 输出层

$$\text{logits} = D \cdot W_{out} + b_{out} \in \mathbb{R}^{B \times L_{tgt} \times V_{vocab}}$$

$$P = \text{softmax}(\text{logits},\ \text{dim}=-1)$$

> $W_{out} \in \mathbb{R}^{d_{model} \times V_{vocab}}$，常与输入 embedding 共享权重（weight tying）。

---

## 5. PyTorch 伪代码

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

## 维度速查表

| 位置 | 维度 | 说明 |
|------|------|------|
| Embedding 输出 | $(B, L, d_{model})$ | 乘 $\sqrt{d_{model}}$ 缩放 |
| Attention $Q,K,V$ | $(B, h, L, d_k)$ | $d_k = d_{model}/h$ |
| FFN 中间层 | $(B, L, d_{ff})$ | $d_{ff}=4d_{model}$ |
| 输出 logits | $(B, L_{tgt}, V_{vocab})$ | softmax 得概率分布 |
