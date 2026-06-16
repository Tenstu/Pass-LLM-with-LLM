# 环境支持与 Model Provider 说明

> 本文档记录项目的开发环境配置，以及不同 model provider 的使用说明。

## 开发环境

本项目的 Skill 定义、MCP Server 和工作流基于以下环境开发和测试：

| 组件 | 版本 / 信息 |
|------|------------|
| IDE | VS Code 1.123.0 |
| Claude Code 扩展 | `anthropic.claude-code`（VS Code 插件） |
| Claude Code CLI | 2.1.150 |
| VS Code Commit Hash | `6a44c352bd24569c417e530095901b649960f9f8` |
| 操作系统 | Windows 11 Pro for Workstations |

> 以上为开发时的环境快照。项目不绑定特定版本，向下兼容。

## Model Provider

### 开发时使用的 Provider

本项目在开发过程中使用了以下 model provider（通过 Claude Code 的 model 配置接入）：

| Provider | 模型 | 说明 |
|----------|------|------|
| Xiaomi (小米) | **mimo-v2.5-pro** | 推理增强模型，用于 Skill 调试和算法题解答 |
| StepFun (阶跃星辰) | **step-3.7-flash** | 轻量快速推理模型，用于日常 Skill 调用和选择题生成 |

> 以上模型 ID 为开发时使用的标识。实际使用时请参考各 provider 官方文档确认最新模型名称和 API 端点。

### 用户适配

项目 **不绑定任何特定 model provider**。核心 Skill Pipeline（solve-skeleton、algo-annotation 等）是纯文本指令驱动，与底层模型无关。

**适配方式**：

1. **Claude API 直连**（默认）：使用 Anthropic 官方 API，无需额外配置。
2. **第三方 provider**（如 MiMo、StepFun）：在 Claude Code 的 model 配置中设置自定义 endpoint。
3. **本地模型**（如 Ollama）：配置 Claude Code 指向本地服务。

**注意事项**：

- `exam-memory` MCP Server 是项目自带的 Python 服务，与 model provider 无关。
- Skill 的质量（骨架选择准确性、诊断精确度等）受底层模型能力影响。
- 推荐使用推理能力较强的模型处理 `solve-analyze` 和 `choice-q-create`。
- `solve-skeleton` 和 `algo-annotation` 对模型要求较低，轻量模型即可胜任。

### Claude Code 配置示例

在 Claude Code 中切换 model provider 的方法：

```bash
# 查看当前 model 配置
claude config get model

# 设置自定义 model（示例）
claude config set model "provider/model-id"
```

具体 provider 的配置方式请参考：
- [Claude Code 官方文档](https://docs.anthropic.com/en/docs/claude-code)
- 各 provider 的 API 文档

## IDE 集成

### VS Code 扩展（强烈推荐）

- 安装扩展：在 VS Code 扩展市场搜索 `anthropic.claude-code`
- 扩展提供：内联 Skill 调用、MCP Server 管理、终端集成
- 配置文件 `.mcp.json` 需放在项目根目录
- **交互答题**（choice-q-drill）依赖 `AskUserQuestion` 工具，仅在 VS Code 扩展中可用

> **推荐使用 VS Code 扩展**。CLI 和 Web 模式下，交互式选择题答题（choice-q-drill）和部分需要用户即时反馈的 Skill 可能无法正常运行。

### CLI 模式

- 安装：`npm install -g @anthropic-ai/claude-code`
- 在项目目录下运行 `claude` 进入交互模式
- 支持大部分 Skill 调用和 MCP 工具
- **限制**：`AskUserQuestion` 工具不可用，choice-q-drill 等交互式 Skill 降级为文本模式

### Web 模式（claude.ai/code）

- 直接在浏览器中使用，无需本地安装
- MCP Server 需本地运行，Web 模式下不可用
- 核心 Skill Pipeline（无 MCP 依赖的 Skill）完全可用
