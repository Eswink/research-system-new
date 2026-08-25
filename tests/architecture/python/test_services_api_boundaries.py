"""M13 架构门禁：Control Plane API 依赖边界（.importlinter.api）。

证明（M13 DoD 14）：
- services/api → packages/application → packages/domain 单向；
- adapters 只能由 composition root（services.api.composition）注入；
- DTO 层不 import domain/application（前端类型边界）。
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def run_import_linter(config_name: str) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("lint-imports")
    if executable is None:
        raise RuntimeError("lint-imports executable is unavailable in the frozen uv environment")
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    return subprocess.run(
        [executable, "--config", str(ROOT / config_name), "--no-cache"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_control_plane_api_has_no_adapter_leak_outside_composition() -> None:
    result = run_import_linter(".importlinter.api")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "BROKEN" not in result.stdout


def test_control_plane_dto_does_not_import_domain() -> None:
    result = run_import_linter(".importlinter.api")
    assert "2 kept, 0 broken" in result.stdout