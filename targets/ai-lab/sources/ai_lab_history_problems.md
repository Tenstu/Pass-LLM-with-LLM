# AI Lab 历年真题与类似题型速查

> 上海 AI 实验室校招笔试 | 编程 3 题 + 单选8+不定项7 = 52分 | 120 min
> 基于历史笔试真题整理，持续补充

---

## 一、考试结构分析

| 题型 | 题数 | 每题分值 | 合计 | 考察范围 |
|------|------|----------|------|----------|
| 单选 | 8 | 3 分 | 24 分 | 数据结构、机器学习、深度学习、强化学习、概率论 |
| 不定项 | 7 | 4 分 | 28 分 | 同上，多选漏选比多选扣分少 |
| 编程 | 3 | - | - | ACM/OJ，大厂打卡题难度 |

**复习方向**：选择题靠日常积累 + 速记手册；编程靠模式识别 + 限时练习。

---

## 二、编程题历史真题（含完整模式拆解）

> 每题包含：考点 / 思路 / 陷阱 / 参考实现 / 复杂度

### 1. 发光二极管 LED 计数（模拟）

> 预先定义 0-9 每个数字对应的 LED 数量映射表，将输入数字按字符串处理，逐位累加对应 LED 数，快速计算多组数据结果。

- **考点**：模拟 + 哈希映射
- **难度**：简单
- **思路**：预计算 0-9 的 LED 段数 → 逐字符查表 → 累加
- **陷阱**：多组输入用 `for line in sys.stdin`，注意空行终止；用 dict 比 if-elif 链更清晰
- **复杂度**：O(总数字位数)，空间 O(1)

```python
import sys

def solve():
    led = {c: v for c, v in zip("0123456789", [6,2,5,5,4,5,6,3,7,6])}
    out = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            break
        out.append(str(sum(led[c] for c in line)))
    sys.stdout.write("\n".join(out))

if __name__ == "__main__":
    solve()
```

---

### 2. 扩散字符串变换（模拟 + 状态标记）

> 用 list 存字符便于原地修改，boolean 标记阴阳盘状态。遍历操作序列，每步按序号取模定位目标字符：阴盘翻转大小写，阳盘保持不变。操作后切换状态。两盘规则不同是题目的核心。

- **考点**：模拟 + 状态机
- **难度**：中等
- **思路**：按操作顺序依次处理，位置 = 操作序号 % len(s)。阴盘：翻转大小写；阳盘：字符不变。每步后切换阴阳状态。全程一次线性扫描。
- **陷阱**：① 字符串不可变需转 list ② 状态切换必须在每次操作后 ③ 访问位置按操作序号（从0起）取模 ④ 两盘规则不同是核心区分点
- **复杂度**：O(m)，m 为操作数；空间 O(n)，n 为字符串长度

```python
import sys

def solve():
    s = sys.stdin.readline().strip()
    ops = sys.stdin.readline().strip()
    chars = list(s)
    state = False  # False=阴盘(翻转大小写), True=阳盘(保持不变)

    for i, op in enumerate(ops):
        pos = i % len(chars)
        c = chars[pos]
        if not state:  # 阴盘：翻转大小写
            if c.islower():
                chars[pos] = c.upper()
            else:
                chars[pos] = c.lower()
        else:  # 阳盘：字符不变
            pass
        state = not state  # 阴阳切换

    sys.stdout.write("".join(chars))

if __name__ == "__main__":
    solve()
```

---

### 3. 循环指令糖果求和（数学 + 等差数列并集）

> 跑一轮指令获得访问坐标集合 V 和净位移 Δ。k 轮后访问坐标为 {v + i·Δ | v ∈ V, 0 ≤ i < k}。按坐标对 |Δ| 取模分组，每组内用区间合并统计等差数列并集大小，O(m + |V|) 完成计算。

- **考点**：等差数列并集、模分组、区间合并
- **难度**：困难
- **思路**：跑一轮得 V 和 Δ。按 r = x mod |Δ| 将 V 分组，同组坐标构成公差 |Δ| 的等差数列。每组内按偏移排序后合并重叠区间 [min + i·|Δ|, max + (k-1)·|Δ|]，每组贡献 (max - min) / |Δ| + k 个位置。累加所有组即答案
- **陷阱**：① **不能循环 k 次**（k 可达 10⁹）② Δ = 0 时答案为 |V|（各轮无位移，完全重合）③ 同余类内多段偏移可能重叠，必须合并区间再计数
- **复杂度**：O(m)，空间 O(m)，m 为指令长度

```python
import sys

def solve():
    n, m, k = map(int, sys.stdin.readline().split())
    ops = sys.stdin.readline().strip()

    # 跑一轮，记录访问坐标和净位移
    pos = 0
    visited = {0}
    for op in ops:
        pos += 1 if op == 'R' else -1
        visited.add(pos)
    delta = pos  # 一轮结束后的净位移

    # Δ = 0：每轮路径完全重合，只需一轮的独立位置数
    if delta == 0:
        print(len(visited))
        return

    d = abs(delta)

    # 按坐标对 |Δ| 取模分组：同余坐标的位移序列互不交叉
    groups = {}
    for v in visited:
        r = v % d
        groups.setdefault(r, []).append(v)

    ans = 0
    for r, offsets in groups.items():
        offsets.sort()
        # 每组内每轮贡献一个等差数列区间
        # [offset_i + 0*Δ, offset_i + (k-1)*Δ]，公差为 d
        # 按 offset 排序后合并重叠区间
        lo = offsets[0]
        hi = offsets[0]
        for v in offsets[1:]:
            # 两段区间 [lo, lo+(k-1)d] 与 [v, v+(k-1)d] 重叠当且仅当 v <= hi + (k-1)*d
            if v <= hi + (k - 1) * d:
                hi = max(hi, v)
            else:
                ans += (hi - lo) // d + k
                lo = hi = v
        ans += (hi - lo) // d + k

    print(ans)

if __name__ == "__main__":
    solve()
```

> **数学关键**：k 轮后坐标集合 = ⋃_{v∈V} {v + i·Δ | 0 ≤ i < k}。当 Δ ≠ 0 时，按 x mod |Δ| 分组，每组内各等差数列互不交叉。合并重叠区间后，每段长度 L 贡献 L/|Δ| + k 个位置（公差为 |Δ| 的等差数列并集大小）。三角形数思想体现在区间长度与 k 的线性组合中，避免逐轮枚举。
---

### 4. 榨汁机（模拟 + 计数器）

> 按下标扫水果，维护机内体积；超容量就交给贪吃鬼并启动榨汁清空。机内为空时不要空转计数，遍历完要补一次启动。

- **考点**：模拟 + 计数器
- **难度**：简单
- **思路**：线性扫描，维护当前体积 cur。cur + aᵢ > S → 启动计数+1，cur = aᵢ；否则 cur += aᵢ
- **陷阱**：① 机内为空时不要空转计数 ② 遍历完要补一次启动计数 ③ 体积恰好等于容量时不算溢出（用 > 不用 ≥）
- **复杂度**：O(n)，空间 O(1)

```python
import sys

def solve():
    n, S = map(int, sys.stdin.readline().split())
    a = list(map(int, sys.stdin.readline().split()))

    cur = 0
    count = 0

    for v in a:
        if cur + v > S:
            count += 1
            cur = v
        else:
            cur += v

    if cur > 0:
        count += 1

    print(count)

if __name__ == "__main__":
    solve()
```

---

### 5. 栈中熔合（栈 + GCD）

> 用栈维护序列，每次压入后看栈顶两元素是否超阈值 S，是则弹掉 top 并把下方替换成 gcd(top, 下方)。

- **考点**：栈模拟 + 数学（GCD）
- **难度**：中等
- **思路**：维护栈，每次压入后循环检查栈顶两元素：gcd < S → 弹 top 两元素，压 gcd。gcd 替换后值更小，下一轮自动续检
- **陷阱**：① gcd 后新值 ≤ 原值，不需要回退指针 ② 用 `math.gcd` ③ 压入 gcd 后可能触发新的合并，需 while 循环
- **复杂度**：O(n log V)，V = max(aᵢ)

```python
import sys, math

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    n = int(data[0])
    S = int(data[1])
    a = list(map(int, data[2:2+n]))

    stack = []
    for x in a:
        stack.append(x)
        while len(stack) >= 2:
            g = math.gcd(stack[-1], stack[-2])
            if g < S:
                stack.pop()
                stack.pop()
                stack.append(g)
            else:
                break

    print(len(stack))

if __name__ == "__main__":
    solve()
```

---

### 6. 排列 mex 计数（mex + 滑动窗口）

> 长度 k 窗口的 mex ≥ v 等价于窗口包含 {0..v-1}，设 L_v 为最短覆盖窗口长度，则 f 的跳变点恰对应不同的 L 值。

- **考点**：mex 性质 + 最小覆盖窗口去重
- **难度**：困难
- **思路**：mex ≥ v ⇔ 窗口含 [0, v-1]。对每个 v，用双指针找最短覆盖 [0,v-1] 的窗口长度 L_v。答案 = (n-1) − 去重后的 {L_2..L_n} 的个数
- **陷阱**：① 理解 mex ≥ v 的等价条件 ② L_v 去重（不同 v 可能对应同一最短窗口）③ v=1 时 [0,0] 是单元素
- **复杂度**：O(n)

```python
import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    p = data[1:]  # 排列，p[i] in [0, n-1]

    pos = [0] * n
    for i, val in enumerate(p):
        pos[val] = i

    # L_v = max(pos[0..v-1]) - min(pos[0..v-1]) + 1
    # Track min and max incrementally as v grows
    unique_L = set()
    min_pos = n          # running minimum position among values [0, v-1]
    max_pos = -1         # running maximum position among values [0, v-1]

    for v in range(2, n + 1):
        pv = pos[v - 1]           # position of newly required value v-1
        if pv < min_pos:
            min_pos = pv
        if pv > max_pos:
            max_pos = pv
        L = max_pos - min_pos + 1  # shortest window length for this v
        unique_L.add(L)

    ans = (n - 1) - len(unique_L)
    sys.stdout.write(str(ans))

if __name__ == "__main__":
    solve()
```

> **核心 insight**：mex ≥ v 当且仅当 [0, v-1] 都在窗口内。v 递增时左指针不回退，总复杂度 O(n)。

---

### 7. 井字棋（博弈模拟）

> 每步前先看有人赢没，赢了还下就-1；落子位置有子也-1；下完检查当前玩家是否三连。最后没人赢输出2，先手赢0，后手赢1。

- **考点**：模拟 + 博弈状态检查
- **难度**：中等
- **思路**：逐步模拟每一步。每步：先检查上一步是否已有人赢（赢了还下→-1），再检查落子合法性（位置冲突→-1），下完后检查当前玩家是否三连。终局：先手赢=0，后手赢=1，没人赢=2
- **陷阱**：① **赢了之后继续下** → 直接 -1 ② 落子位置已有子 → -1 ③ 三连检查：3 行 + 3 列 + 2 对角线 ④ 第一步也要检查"赢了没"（上一步是否赢）
- **复杂度**：O(m)，m = 操作步数

```python
import sys

def check_win(board, player):
    for r in range(3):
        if all(board[r][c] == player for c in range(3)):
            return True
    for c in range(3):
        if all(board[r][c] == player for r in range(3)):
            return True
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2-i] == player for i in range(3)):
        return True
    return False

def solve():
    ops = sys.stdin.readline().strip()
    board = [['.' for _ in range(3)] for _ in range(3)]
    players = ['X', 'O']

    for step, op in enumerate(ops):
        player = players[step % 2]
        r, c = int(op[0]) - 1, int(op[1]) - 1

        if step > 0 and check_win(board, players[(step-1) % 2]):
            print(-1)
            return
        if board[r][c] != '.':
            print(-1)
            return
        board[r][c] = player

    if check_win(board, 'X'):
        print(0)
    elif check_win(board, 'O'):
        print(1)
    else:
        print(2)

if __name__ == "__main__":
    solve()
```

---

### 8. 能力观赏排序（贪心 + 前缀和）

> 能力从大到小排序，每轮人数减半向上取整，累加前缀和就是最大观赏值。

- **考点**：排序、贪心、前缀和、模拟
- **思路**：能力降序排列。每轮取 ceil(剩余/2) 个人，累加他们的能力值之和
- **陷阱**：① 排序方向必须是**降序**（观赏值最大）② 向上取整用 `(n+1)//2` ③ 预计算前缀和，每轮 O(1) 求和
- **复杂度**：O(n log n)

```python
import sys

def solve():
    n = int(sys.stdin.readline())
    a = list(map(int, sys.stdin.readline().split()))
    a.sort(reverse=True)
    pre = [0]
    for x in a:
        pre.append(pre[-1] + x)

    ans = 0
    idx = 0
    cur_n = n
    while cur_n > 0:
        ans += pre[idx + cur_n] - pre[idx]
        idx += cur_n
        cur_n = (cur_n + 1) // 2

    print(ans)

if __name__ == "__main__":
    solve()
```

---

### 9. 质因子分解计数（数论）

> a 不能整除 x 直接 0。分解 x 质因子，a 里该因子次数已满则 b 可选 0~t 共 t+1 种，未满则 b 只能补满（1 种），乘起来就是答案。

- **考点**：数论 + 质因数分解
- **难度**：中等
- **思路**：对 x 做质因数分解。对 x 的每个质因子 p：检查 a 中 p 的次数 v_p(a)。若 v_p(a) > b·v_p(x) 则无解。b 的下界为 ceil(v_p(a)/v_p(x))。答案 = max(0, m - min_b + 1)
- **陷阱**：① a 含 x 没有的质因子 → 直接 0 ② 用试除法分解（x ≤ 10¹²，试除到 √x 即可）③ 注意 b 从 1 还是 0 开始
- **复杂度**：O(√x)，空间 O(log x)

```python
import sys, math

def factorize(n):
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors

def solve():
    a, m, x = map(int, sys.stdin.readline().split())
    fx = factorize(x)
    fa = factorize(a)

    for p in fa:
        if p not in fx:
            print(0)
            return

    min_b = 1
    for p in fx:
        need = fa.get(p, 0)
        have = fx[p]
        b_min = (need + have - 1) // have
        min_b = max(min_b, b_min)

    print(max(0, m - min_b + 1))

if __name__ == "__main__":
    solve()
```

---

### 10. 括号匹配（字符串 + 栈）

> 看描述像博弈论，实际就是括号匹配，用计数栈解决。

- **考点**：字符串 + 栈
- **难度**：基础
- **思路**：标准括号匹配。左括号入栈，右括号检查栈顶是否匹配。遍历完栈空=合法
- **陷阱**：① 栈空时遇到右括号 ② 遍历结束后栈不为空 ③ 多种括号类型需要匹配对
- **复杂度**：O(n)，空间 O(n)

```python
import sys

def solve():
    s = sys.stdin.readline().strip()
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}

    for c in s:
        if c in '([{':
            stack.append(c)
        elif c in ')]}':
            if not stack or stack[-1] != pairs[c]:
                print("invalid")
                return
            stack.pop()

    print("valid" if not stack else "invalid")

if __name__ == "__main__":
    solve()
```

---

### 11. 字符串按下标修改（字符串操作）

> 给定操作序列（位置 + 字符），按顺序修改字符串对应位置字符。

- **考点**：字符串 + 模拟
- **难度**：基础
- **思路**：字符串转 list（可变），按操作直接赋值 `s[pos] = new_char`
- **陷阱**：① Python 字符串不可变，必须转 list ② 下标 0-based vs 1-based ③ 多次修改同一位置
- **复杂度**：O(m)，空间 O(n)

```python
import sys

def solve():
    s = list(sys.stdin.readline().strip())
    m = int(sys.stdin.readline())
    for _ in range(m):
        parts = sys.stdin.readline().split()
        pos = int(parts[0]) - 1
        s[pos] = parts[1]
    print("".join(s))

if __name__ == "__main__":
    solve()
```

---

## 四、选择题高频考点

### 数据结构
- 栈/队列操作序列判断
- 树遍历（前中后序、层序）性质
- 排序算法复杂度与稳定性
- 哈希表冲突解决

### 机器学习
- 过拟合/欠拟合识别与对策
- 偏差-方差权衡
- 交叉验证原理
- 常见损失函数性质

### 深度学习
- Transformer 注意力机制细节（Q/K/V、缩放因子）
- CNN 感受野计算
- 梯度消失/爆炸原因与对策
- BatchNorm 训练 vs 推理差异（训练用 batch 统计量，推理用全局移动平均）
- BatchNorm 每通道 γ、β 共 2C 个可学习参数
- Softmax 数值稳定：先减最大值再 exp；平移不变性 softmax(z+c)=softmax(z)
- Softmax+CE 联合求导 = ŷ - y
- 参数量计算：Linear(n→m) = nm+m；Conv(C_out,C_in,k) = C_out×C_in×k²+C_out

### 强化学习
- MDP 定义（状态/动作/奖励/转移）
- Q-learning vs SARSA
- 策略梯度 vs 值函数方法
- Exploration vs Exploitation

### 概率论
- 贝叶斯公式 + 全概率公式三步走
- 常见分布（正态、泊松、二项）
- 期望与方差性质：E 线性性无需独立，Var 可加/乘积期望可拆需独立
- 独立 vs 不相关：独立⇒不相关，反之不成立（仅 Cov=0 是线性关系）
- MLE vs MAP：MAP = MLE + 先验；L2 正则 ↔ 高斯先验

### 线性代数
- 特征值性质：tr(A)=Σλᵢ，det(A)=Πλᵢ
- A² 特征值 = λᵢ²，排序不变（最小仍为 λₙ²）
- 正交矩阵：det=±1，特征值模为1可含复数（旋转），A⁻¹=A^T
- 正定矩阵：特征值全正实数，对称矩阵特例
- SVD：任意矩阵可用，A=UΣV^T，σᵢ=√λᵢ(A^T A)

### 推理优化
- KV Cache 显存公式：2×layers×heads×head_dim×seq_len×bytes
- GQA/MQA/MHA 对比：GQA=折中（如64Q→8KV，cache 1/8）；MQA=极端（1个KV，1/64）
- FlashAttention：不改结果只改内存访问模式（tiling分块），IO 从 O(N²) 降到 O(N²d²/M)
- 量化：INT8 几乎无损；INT4 (GPTQ/AWQ) 有损但大幅省显存
- weight-only vs weight-activation 量化区分

### 大模型微调
- LoRA：冻结原始权重，ΔW=BA，参数量=d×r+r×k（不是 d×k）
- QLoRA：核心目的是降显存（4-bit NF4 量化），不是提效果
- LoRA 通常应用于 Q/K/V/O 投影矩阵

### 对齐算法
- RLHF 是范式（SFT→奖励模型→PPO），PPO 是具体算法
- DPO 不需要单独奖励模型，将奖励隐式融入损失（本质是分类损失，非 RL）
- DPO 仍需参考模型（frozen SFT model）

### RAG / Agent
- RAG 流程：Chunk→Embedding→Retrieval(粗排/Bi-Encoder)→Rerank(精排/Cross-Encoder)→LLM生成
- ReAct = Thought→Action→Observation 交替循环；vs CoT 关键区别：ReAct 可调用外部工具
- Function Calling 需要结构化输出（函数名+JSON参数）

### GNN（详见 llm/gnn_diffusion_cheatsheet.md）
- 过平滑（over-smoothing）：层数过多→感受野过大→节点表征趋同，≠过拟合
- GCN 权重固定（度归一化），GAT 权重可学习（注意力机制）
- GAT 多头：中间层 concat，输出层 mean
- 消息传递 MPNN 包含 GCN/GAT/GraphSAGE/GIN 作为特例
- 任务粒度：节点级、边级、图级

### 扩散模型（详见 llm/gnn_diffusion_cheatsheet.md）
- DDPM 训练预测噪声 ε，损失 ‖ε-ε_θ‖²
- DDPM 采样是随机的（每步注入噪声）；DDIM(η=0) 是确定性采样
- CFG = 线性外推 ε'=ε_uncond + s·(ε_cond - ε_uncond)，不需要额外分类器
- Latent Diffusion 在潜空间做扩散，大幅降低计算量
- α̅_t = ∏(1-βₛ)，前向一步到位：q(x_t|x_0)=N(√α̅_t x₀, (1-α̅_t)I)

---

## 五、复习优先级

```
P0（必练）：
  - 模拟类题目（线性扫描 + 状态维护）— 大厂笔试最高频
  - 栈操作（括号匹配、栈中元素合并）
  - 字符串处理（逐字符、转 list 修改）

P1（重点）：
  - 数论基础（质因数分解）
  - 数学推导（等差数列求和、三角形数）
  - 贪心 + 排序 + 前缀和

P2（熟悉模板）：
  - DP（mex、LCS、背包变种）
  - BFS/DFS（网格、树）
  - 选择题高频概念（ML/DL/概率）

P3（了解）：
  - 强化学习基础概念
  - 实验室认知（InternLM/InternVL）
```

---

## 六、推荐练习节奏

1. 先过 P0 模式，每类做 2-3 道题建立肌肉记忆
2. 用 `mock_exam_prompt.md` 进行限时模拟（3 题编程 + 选择题）
3. 错题立即记录到 `algorithms/mistake_log.md`
4. 考前 2 天：只过 P0/P1 模板 + 数学选择题速记

---

*本文件基于历史真题分析，持续补充实际考试题型*
