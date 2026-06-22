#!/usr/bin/env python3
"""Scan staged files against main-extraction denylist.

Usage:
    python scripts/check_main_extraction.py
    python scripts/check_main_extraction.py --staged-files path1 path2
    python scripts/check_main_extraction.py --require-branch main

Exit code: 0 = no leaks, 1 = denylist paths or wrong branch found.
"""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

_DENYLIST = [
    "docs/",
    ".mcp.json",
    ".env",
    ".env.*",
    ".claude/",
    ".codex/",
    ".serena/",
    ".chatmem/",
    ".mempalace/",
    "shared/exam_memory/user_profile.json",
    "shared/exam_memory/experiences/",
    "shared/exam_memory/vectorstore/",
    "shared/exam_memory/bank/difficulty_stats.json",
    "shared/exam_memory/bank/",
    "shared/daily/",
    "shared/progress/",
    "targets/*/progress/",
    "targets/*/solutions/",
    "targets/*/mistake_log.md",
    "targets/*/mock_exam_log.md",
    "targets/*/cheatsheets/",
    "targets/*/sources/",
    "HANDOFF.md",
    "prompts/review-fix-session-prompt.md",
    "skills/branch-ops/",
    "skills/harness-dev-flow/",
    "skills/dev-review-flow/",
    "tests/test_chunking.py",
    "tests/test_fts_store.py",
    "tests/test_hybrid_search.py",
    "tests/test_security.py",
    "tests/test_server.py",
    "tests/test_vector_store.py",
]


def _is_allowed_root_public_example(path: str) -> bool:
    return _path_parts(path) in ([".mcp.example.json"], [".env.example"])


def _is_allowed_exam_bank_public_file(path: str) -> bool:
    return _path_parts(path) == ["shared", "exam_memory", "bank", "README.md"]


def _is_allowed_shared_progress_public_file(path: str) -> bool:
    parts = _path_parts(path)
    if len(parts) < 3 or parts[:2] != ["shared", "progress"]:
        return False
    filename = parts[-1]
    return (
        parts == ["shared", "progress", "README.md"]
        or filename == ".gitkeep"
        or filename.endswith(".example.md")
        or filename.endswith(".template.md")
    )


def _git_staged() -> list[str]:
    # Deletions remove dev-only files from main and are safe for cleanup commits.
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"],
        capture_output=True, text=True, check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _git_current_branch() -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def _path_parts(path: str) -> list[str]:
    normalized = path.replace("\\", "/").strip("/")
    return [part for part in normalized.split("/") if part and part != "."]


def _parts_match(path_parts: list[str], pattern_parts: list[str]) -> bool:
    if len(path_parts) != len(pattern_parts):
        return False
    return all(
        fnmatch.fnmatchcase(path_part, pattern_part)
        for path_part, pattern_part in zip(path_parts, pattern_parts)
    )


def _matches_denylist(path: str) -> str | None:
    if (
        _is_allowed_root_public_example(path)
        or _is_allowed_exam_bank_public_file(path)
        or _is_allowed_shared_progress_public_file(path)
    ):
        return None
    path_parts = _path_parts(path)
    for entry in _DENYLIST:
        pattern_parts = _path_parts(entry.rstrip("/"))
        if entry.endswith("/"):
            if len(path_parts) >= len(pattern_parts) and _parts_match(
                path_parts[:len(pattern_parts)], pattern_parts
            ):
                return entry
        elif _parts_match(path_parts, pattern_parts):
            return entry
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Check staged files for main-extraction denylist violations")
    ap.add_argument("--staged-files", nargs="*", default=None,
                    help="Explicit file list (default: read from git)")
    ap.add_argument("--require-branch", default=None,
                    help="Fail unless the current git branch matches this name")
    args = ap.parse_args()
    if args.require_branch is not None:
        current_branch = _git_current_branch()
        if current_branch != args.require_branch:
            print(
                f"WRONG BRANCH - expected {args.require_branch}, got {current_branch}",
                file=sys.stderr,
            )
            return 1
    files = args.staged_files if args.staged_files is not None else _git_staged()
    if not files:
        print("check_main_extraction: no staged files - nothing to check")
        return 0
    leaks: list[tuple[str, str]] = []
    for f in files:
        match = _matches_denylist(f)
        if match:
            leaks.append((f, match))
    if leaks:
        print("DENYLIST LEAK - do not publish to main:", file=sys.stderr)
        for path, rule in leaks:
            print(f"  {path}  ->  hits {rule}", file=sys.stderr)
        return 1
    print(f"check_main_extraction: {len(files)} staged files - no denylist violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
