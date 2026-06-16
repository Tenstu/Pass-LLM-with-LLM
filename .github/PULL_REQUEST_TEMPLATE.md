## What Changed / 改了什么

Brief description of this PR.

## Why / 为什么改

Motivation or issue being addressed.

## Scope / 影响范围

- [ ] Skill definition (`skills/`)
- [ ] MCP Server (`exam_memory/`)
- [ ] Algorithm code (`algorithms/`)
- [ ] Cheatsheet / quick notes (`llm/`)
- [ ] Documentation / README
- [ ] Progress tracking (`progress/`)
- [ ] GitHub templates / CI config

## Testing Evidence / 测试证据

Describe how you verified this change works:

- [ ] Algorithm solution tested with sample input/output
- [ ] Skill invoked successfully via `Skill(skill="...")`
- [ ] MCP tool called and returned expected result
- [ ] Manual walkthrough / dry-run completed
- [ ] N/A — docs-only or template-only change

Details:

```
(paste test output, screenshots, or notes here)
```

## Breaking Changes / 破坏性变更

- [ ] This PR introduces no breaking changes
- [ ] This PR changes an existing Skill's trigger behavior
- [ ] This PR modifies MCP tool signatures or output format
- [ ] This PR renames or moves files referenced by other components
- [ ] This PR requires re-running `exam_memory` setup

If breaking, describe migration steps:

```
(describe what users need to do after merging)
```

## Checklist

- [ ] Algorithm solution went through solve-skeleton -> algo-annotation full flow
- [ ] WA/TLE errors recorded in `algorithms/mistake_log.md`
- [ ] New Skill has complete frontmatter (name, description)
- [ ] No unnecessary third-party dependencies introduced
- [ ] No personal data from `exam_memory/` included (that directory is in `.gitignore`)
