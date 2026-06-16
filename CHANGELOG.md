# Changelog

## [1.0.0] - 2026-06-16

### Added
- 自定义 MCP Server（exam-memory）：6 个工具实现跨会话经验持久化
- 5 个核心 Skills：solve-skeleton、solve-analyze、algo-annotation、choice-q-create、choice-q-drill
- 11 道真题解答（solutions_batch.py）+ ACM/OJ 工具库（python_oj_template.py）
- 用户画像系统（user_profile.json）+ 经验文件自动编号
- ChatMem、mempalace、onefind 外部 MCP 适配文档
- GitHub 社区文件：Issue 模板、PR 模板、SECURITY.md

### Changed
- 项目重命名为 pass-llm-with-llm（原 pdd-llm-algo-exam-harness）
- README 中英双版、AGENTS.md 泛化（移除个人数据）

### Fixed
- search_web 工具标记为废弃，指向 Claude Code 内置 WebSearch
- python_oj_template.py 移除 sys.stdin.buffer 违规用法
