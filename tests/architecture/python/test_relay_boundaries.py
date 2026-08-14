"""application 与 relay 边界测试。

- application 层只依赖 domain（layers），不得 import adapters；
- relay adapter 只走协议 HTTP，不 import 厂商 SDK（openai/litellm/anthropic）。
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _run_linter(config_name: str) -> subprocess.CompletedProcess[str]:
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


def test_application_depends_on_domain_only() -> None:
    result = _run_linter(".importlinter.application")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 broken" in result.stdout


def test_application_does_not_import_adapters() -> None:
    # application-layers 契约已禁止向下依赖；此处再显式确认无 adapters import
    result = _run_linter(".importlinter.application")
    assert "broken contracts: 0" in result.stdout or "0 broken" in result.stdout


def test_relay_adapter_has_no_vendor_sdk_dependency() -> None:
    result = _run_linter(".importlinter.relay")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 broken" in result.stdout


def test_fakes_have_no_provider_or_relay_dependency() -> None:
    result = _run_linter(".importlinter.fakes")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 broken" in result.stdout


def test_sqlite_adapters_have_no_vendor_or_fake_dependency() -> None:
    result = _run_linter(".importlinter.sqlite")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 broken" in result.stdout
