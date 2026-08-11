from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"


def run_import_linter(fixture_name: str) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("lint-imports")
    if executable is None:
        raise RuntimeError("lint-imports executable is unavailable in the frozen uv environment")
    env = {
        **os.environ,
        "PYTHONPATH": str(FIXTURES / fixture_name),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    return subprocess.run(
        [executable, "--config", str(ROOT / ".importlinter"), "--no-cache"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_valid_python_dependency_graph_is_allowed() -> None:
    result = run_import_linter("valid")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "2 kept, 0 broken" in result.stdout


def test_reverse_python_dependency_is_rejected() -> None:
    result = run_import_linter("invalid")
    assert result.returncode != 0, "负向 Python 架构夹具必须被 import-linter 拒绝"
    assert "Clean architecture dependency direction BROKEN" in result.stdout
