"""tests/conftest.py — pytest fixtures and config."""

import os
import sys
from pathlib import Path

import pytest

# Ensure shared/ is on sys.path for direct test runs
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

# Force pytest tmp_path to use a writable directory (Windows workaround)
if os.name == "nt":
    _proj_temp = Path(__file__).resolve().parent.parent / ".tmp"
    _proj_temp.mkdir(exist_ok=True)
    os.environ.setdefault("TMPDIR", str(_proj_temp))
    os.environ.setdefault("TEMP", str(_proj_temp))
    os.environ.setdefault("TMP", str(_proj_temp))


@pytest.fixture
def tmp_bank(tmp_path):
    """Temporary QuestionBank backed by an isolated temp dir."""
    from exam_memory.question_bank import QuestionBank
    return QuestionBank(bank_dir=tmp_path)
