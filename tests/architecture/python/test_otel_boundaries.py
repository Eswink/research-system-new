"""M15 OTel 边界门禁(WP4)。

- `.importlinter.otel`:OTel SDK 只允许 adapters.otel 引用;
- `.importlinter.postgres`:开始执行(此前存在但无测试运行);
- 静态扫描:packages/services 无任何 opentelemetry import;
- OTel SDK 不进入 fakes/sqlite/postgres/relay/mcp/domain/application/api。
"""

from __future__ import annotations

import ast
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


def test_otel_sdk_is_confined_to_otel_adapter() -> None:
    result = _run_linter(".importlinter.otel")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 broken" in result.stdout


def test_postgres_boundary_contract_executes_and_passes() -> None:
    """`.importlinter.postgres` 此前存在但从未被执行(M15 起纳入门禁)。"""
    result = _run_linter(".importlinter.postgres")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 broken" in result.stdout


def test_no_opentelemetry_import_outside_otel_adapter() -> None:
    """AST 级静态扫描:packages/services/adapters(otel 外)无 opentelemetry。"""
    offenders: list[str] = []
    for top in ("packages", "services", "adapters", "tools"):
        for path in (ROOT / top).rglob("*.py"):
            relative = path.relative_to(ROOT)
            if relative.as_posix().startswith("adapters/otel/"):
                continue
            offenders.extend(
                f"{relative} -> {name}"
                for name in _otel_imports(
                    ast.parse(path.read_text(encoding="utf-8", errors="replace"))
                )
            )
    assert not offenders, f"opentelemetry imports outside adapters.otel: {offenders}"


def test_otel_linter_config_covers_every_adapter_subpackage() -> None:
    """`.importlinter.otel` 的 source_modules 必须覆盖 adapters/ 全部子包。

    新增 adapter 子包而忘记登记会让 OTel 边界失去 import-linter 保护——
    此断言使缺口成为测试失败而非静默放行。
    """
    config = (ROOT / ".importlinter.otel").read_text(encoding="utf-8")
    declared = {line.strip() for line in config.splitlines() if line.startswith("    adapters.")}
    actual = {
        "adapters." + path.name
        for path in (ROOT / "adapters").iterdir()
        if path.is_dir() and not path.name.startswith("_") and path.name != "otel"
    }
    missing = actual - declared
    assert not missing, f".importlinter.otel 缺少 source_modules 登记: {sorted(missing)}"


def _otel_imports(tree: ast.AST) -> list[str]:
    """AST 中全部 opentelemetry 顶层导入名。"""
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            candidates = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            candidates = [node.module or ""]
        else:
            continue
        names.extend(name for name in candidates if name.split(".")[0] == "opentelemetry")
    return names
