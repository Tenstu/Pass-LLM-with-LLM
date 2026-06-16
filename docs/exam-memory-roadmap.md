# 考试经验沉淀系统 - 后期规划

> 创建日期：2026-06-15

## 当前状态

V1（MCP + Skill + 本地文件）已实现，覆盖基本的经验 CRUD 和用户画像。

## V2 目标：RAG + 语义检索版

将纯文件遍历升级为语义检索，解决关键词匹配无法召回"表述不同但含义相近"经验的问题。

### 技术栈（2026-06-16 可行性验证后修订）

**分层依赖设计**：核心功能零额外依赖，LangChain 为可选增强层。

| 层级 | 方案 | 安装 | 状态 |
|------|------|------|------|
| Embedding | `BAAI/bge-m3`（本地 HF，已缓存） | `pip install ".[embed]"` | Phase 1 |
| 向量存储 | numpy `.npy` + metadata JSON | `[embed]` 内含 | Phase 1 |
| LangChain 增强 | `langchain-core` Retriever 标准接口 | `pip install ".[langchain]"` | Phase 2+ |
| RAG 链 | LangChain LCEL（Retrieve → Format → Generate） | `[langchain]` | Phase 3 |
| 画像推断 Agent | LangChain + LLM API | `[langchain]` + API key | Phase 3 |
| MCP Server | 保留现有接口，内部双路径 | 核心 | Phase 1 |

**安装矩阵**：

```bash
pip install .              # V1 纯本地（无向量化）
pip install ".[embed]"     # V2 Phase 1+2（语义检索，无需 LangChain）
pip install ".[full]"      # V2 全部（含 LangChain 增强）
```

> **为什么不用 ChromaDB**：ChromaDB 1.5.1 依赖 pydantic v1，与 Python 3.14 不兼容。numpy 方案零额外依赖，对 <1000 条经验的规模性能等价。
>
> **为什么不用 GPU**：RTX 5060（CC 12.0）需要 PyTorch sm_120，当前 torch 2.12.0+cu126 仅支持到 sm_90。CPU 推理已足够快（bge-m3 编码 3 条经验 0.24s，查询 38ms）。
>
> **LangChain 兼容**：Phase 1 不依赖 LangChain；Phase 2+ 通过 `rag_pipeline.py` 提供 LangChain Retriever 包装。`server.py` 运行时检测 `HAS_LANGCHAIN` 标志，自动选择最优路径。
>
> **OneFind 互补**：OneFind 的 folder source 可索引 `experiences/` 提供只读语义检索，详见 `docs/mcp-setup-guide.md` §2.4。但 OneFind 是只读设计，无法替代写入链路。

### 核心改造点

**1. 经验入库时自动向量化**

```
save_experience()
  → 写入 Markdown 文件（保留原有格式）
  → 提取 frontmatter + 正文
  → bge-m3(text) → np.save() 存入 vectorstore/embeddings.npy
  → metadata JSON: { type, knowledge, difficulty, error_count, created, file_name }
```

**2. 经验检索改为语义检索**

```
list_experiences(type, query, limit)
  → 当 query 为空时：按 metadata 过滤 + error_count 降序（原逻辑）
  → 当 query 非空时：
      1. bge-m3(query) → cosine_similarity(query_emb, all_embs)
      2. 按 type 过滤 + 相似度排序
      3. 返回 top limit 条
```

**3. 用户画像自动推断（LangChain Agent）**

```python
# 用 LLM 分析对话，提取画像变更
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

profile_prompt = ChatPromptTemplate.from_messages([
    ("system", "分析以下对话，提取用户的强项、弱项和偏好变更。输出 JSON diff。"),
    ("human", "{conversation}")
])
# 对话结束后调用，结果传入 update_user_profile()
```

**4. 知识图谱层（可选增强）**

将经验之间的"前置知识"关系建模为图：

```
动态规划 ← 前置 — 背包问题
双指针   ← 应用 — 三数之和
```

当用户在 A 知识点反复出错时，自动推荐关联的前置知识点复习。

### 目录结构演进

```
exam_memory/
  server.py              # MCP Server（保留，双路径：有/无 LangChain）
  experiences/           # Markdown 经验文件（保留）
  user_profile.json      # 用户画像（保留）
  vectorstore/           # 向量索引目录（新增）
    embeddings.npy       # numpy 向量矩阵 (N x 1024)
    metadata.json        # 每条经验的元数据（与 embeddings 行对齐）
  embedding.py           # 核心层：bge-m3 封装（新增，无 LangChain 依赖）
  vector_store.py        # 核心层：NumpyVectorStore（新增，无 LangChain 依赖）
  rag_pipeline.py        # 增强层：LangChain Retriever 包装（新增，langchain 可选）
  rebuild_index.py       # CLI：扫描 experiences/ 全量重建向量索引（新增）
```

**核心层 vs 增强层**：
- `embedding.py` + `vector_store.py`：永远可用，零额外依赖
- `rag_pipeline.py`：运行时检测 `HAS_LANGCHAIN`，无 LangChain 时整个模块被跳过
- `server.py`：`try: from .rag_pipeline ... except ImportError: from .vector_store`

### 实施路线

| 阶段 | 内容 | 依赖 | LangChain | 状态 |
|------|------|------|:---------:|------|
| Phase 1 | `embedding.py` + `vector_store.py`：向量化入库 | `[embed]` | 不需要 | 待执行 |
| Phase 2 | `server.py` 支持 `list_experiences(query=...)` 语义检索 | Phase 1 | 不需要（有则增强） | 待执行 |
| Phase 2+ | `rag_pipeline.py`：LangChain Retriever 标准接口 | `[langchain]` | 可选增强 | 待执行 |
| Phase 3 | LLM 自动推断画像（LangChain Agent + structured output） | `[langchain]` + LLM API | **必需** | 未开始 |
| Phase 4 | 知识图谱关联推荐 | Phase 1 | 可选 | 未开始 |

### V3 方向（远期）

- 多模态：截图题目 OCR → 自动识别题型并检索经验
- 间隔重复调度：基于 SM-2 算法自动安排复习
- 跨设备同步：经验文件 Git 同步或 WebDAV
- 可视化仪表盘：强弱项热力图、错误趋势、复习计划
