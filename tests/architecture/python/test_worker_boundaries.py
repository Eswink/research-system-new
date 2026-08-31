"""M16 architecture gates: worker plane boundary (.importlinter.worker).

- `.importlinter.worker` must run and stay KEPT (vendor SDK ban);
- Domain/Application must never import the worker plane (adapters.worker /
  services.worker) or worker DTOs;
- the worker plane itself must never import business-truth adapters
  (adapters.postgres / adapters.sqlite / adapters.otel / adapters.openhands);
- the migration set still contains exactly one queue table and one lease table
  (M16 does not add a second queue/lease, ADR-0027).
"""

from __future__ import annotations

import ast
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

_WORKER_PLANE_PREFIXES = ("adapters/worker/", "services/worker/")
_FORBIDDEN_FOR_WORKERS = (
    "adapters.postgres",
    "adapters.sqlite",
    "adapters.otel",
    "adapters.openhands",
)
_DOMAIN_APP_ROOTS = ("packages/domain/", "packages/application/")


def _python_files(rel_roots: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for rel in rel_roots:
        root = ROOT / rel
        if root.is_dir():
            files.extend(root.rglob("*.py"))
    return files


def _imports_of(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    return names


def test_worker_linter_config_is_kept() -> None:
    executable = shutil.which("lint-imports")
    if executable is None:  # pragma: no cover - environment guard
        raise RuntimeError("lint-imports executable is unavailable")
    result = subprocess.run(
        [executable, "--config", str(ROOT / ".importlinter.worker"), "--no-cache"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={"PYTHONPATH": str(ROOT), "PYTHONUTF8": "1", "PATH": ""} | __import__("os").environ,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_worker_plane_never_imports_business_truth() -> None:
    offenders: list[str] = []
    for path in _python_files(_WORKER_PLANE_PREFIXES):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for imported in _imports_of(tree):
            if imported.startswith(_FORBIDDEN_FOR_WORKERS):
                offenders.append(f"{path.relative_to(ROOT)} -> {imported}")
    assert not offenders, f"worker plane imports business truth: {offenders}"


def test_domain_and_application_never_import_worker_plane() -> None:
    offenders: list[str] = []
    for path in _python_files(_DOMAIN_APP_ROOTS):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for imported in _imports_of(tree):
            if imported.startswith(("adapters.worker", "services.worker")):
                offenders.append(f"{path.relative_to(ROOT)} -> {imported}")
    assert not offenders, f"domain/application import worker plane: {offenders}"


def test_migration_set_has_single_queue_and_lease() -> None:
    migrations = (ROOT / "adapters/postgres/migrations").glob("*.sql")
    queue_tables = 0
    lease_tables = 0
    for path in sorted(migrations):
        text = path.read_text(encoding="utf-8")
        queue_tables += text.count("CREATE TABLE IF NOT EXISTS tasks")
        lease_tables += text.count("CREATE TABLE IF NOT EXISTS leases")
    assert queue_tables == 1, f"expected exactly one tasks table, found {queue_tables}"
    assert lease_tables == 1, f"expected exactly one leases table, found {lease_tables}"
