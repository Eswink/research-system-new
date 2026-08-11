"""真实产品代码（packages/domain）依赖纯度边界测试。

验证 Domain 内核不 import 任何 Web/ORM/LLM/runtime/provider 或第三方库
（jsonschema/yaml/fastapi/sqlalchemy/temporalio/openhands 等），
遵循 `adapters → application → domain` 编译期依赖方向。
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def run_domain_linter() -> subprocess.CompletedProcess[str]:
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
        [executable, "--config", str(ROOT / ".importlinter.domain"), "--no-cache"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_domain_kernel_has_no_forbidden_dependencies() -> None:
    result = run_domain_linter()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 broken" in result.stdout


def test_domain_kernel_is_importable() -> None:
    # 冒烟：domain 包可完整导入且不触发任何第三方依赖
    from packages.domain import canonical_json_bytes
    from packages.domain.manifest import RunManifest

    assert canonical_json_bytes is not None
    assert RunManifest is not None
