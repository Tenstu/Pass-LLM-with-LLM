# 考试经验沉淀系统 - 后期规划

> 创建日期：2026-06-15

## 当前状态

V1（MCP + Skill + 本地文件）已实现，覆盖基本的经验 CRUD 和用户画像。

## V2 目标：RAG + LangChain 智能检索版

将纯文件遍历升级为语义检索，解决关键词匹配无法召回"表述不同但含义相近"经验的问题。

### 技术栈

| 层级 | 方案 |
|------|------|
| 框架 | LangChain / LangGraph |
| 向量数据库 | ChromaDB（本地持久化，零运维） |
| Embedding | `text-embedding-3-small`（OpenAI）或 `bge-m3`（本地 HuggingFace） |
| 重排序 | `bge-reranker-base`（本地，可选） |
| MCP Server | 保留现有接口，内部实现替换为 RAG pipeline |

### 核心改造点

**1. 经验入库时自动向量化**

```
save_experience()
  → 写入 Markdown 文件（保留原有格式）
  → 提取 frontmatter + 正文
  → embedding(text) → 存入 ChromaDB collection "experiences"
  → metadata: { type, knowledge, difficulty, error_count, created }
```

**2. 经验检索改为语义检索**

```
list_experiences(type, query, limit)
  → 当 query 为空时：按 metadata 过滤 + error_count 降序（原逻辑）
  → 当 query 非空时：
      1. ChromaDB.similarity_search(query, filter={type: type}, k=limit*2)
      2. 可选：bge-reranker 重排序
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
  server.py              # MCP Server（保留）
  experiences/           # Markdown 经验文件（保留）
  user_profile.json      # 用户画像（保留）
  vectorstore/           # ChromaDB 持久化目录（新增）
  knowledge_graph.json   # 知识点关联图（新增）
  rag_pipeline.py        # LangChain RAG 管道（新增）
  config.yaml            # embedding 模型、reranker 等配置（新增）
```

### 实施路线

| 阶段 | 内容 | 依赖 |
|------|------|------|
| Phase 1 | 经验文件 → ChromaDB 向量化入库 | `chromadb`, `langchain` |
| Phase 2 | `list_experiences` 支持语义检索 | Phase 1 |
| Phase 3 | LangChain Agent 自动推断画像 | `langchain`, LLM API |
| Phase 4 | 知识图谱关联推荐 | Phase 1, 自定义图结构 |

### V3 方向（远期）

- 多模态：截图题目 OCR → 自动识别题型并检索经验
- 间隔重复调度：基于 SM-2 算法自动安排复习
- 跨设备同步：经验文件 Git 同步或 WebDAV
- 可视化仪表盘：强弱项热力图、错误趋势、复习计划
