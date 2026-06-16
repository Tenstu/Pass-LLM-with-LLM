# Security Policy / 安全策略

## Supported Versions / 支持版本

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability / 报告漏洞

This is an exam-prep project, not a production service. However, if you discover a security issue (e.g., credential leak, unsafe code execution, or data exposure in `exam_memory/`), please report it responsibly.

**Do NOT open a public issue for security vulnerabilities.**

Instead, email the maintainer directly or use [GitHub's private vulnerability reporting](https://github.com/Tenstu/pdd-llm-algo-exam-harness/security/advisories/new).

### What to include / 报告内容

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response timeline / 响应时间

- Acknowledgment within 72 hours
- Fix or mitigation within 7 days for confirmed issues

## Scope / 范围

Areas of concern:
- `exam_memory/` — stores personal study data; must not leak to public repos
- MCP server — runs locally with filesystem access
- Skills — executed as LLM prompts; must not inject unsafe instructions
- API keys or credentials in config files

## Out of Scope / 不在范围内

- Algorithm solution correctness (not a security issue)
- Third-party model provider availability
- Rate limiting on external APIs
