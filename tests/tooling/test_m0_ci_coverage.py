"""CI coverage contracts for live PostgreSQL, collector, Docker, and Console gates."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "m0-quality.yml"


def _workflow() -> dict[str, Any]:
    parsed = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(parsed, dict)
    return parsed


def _commands(job: dict[str, Any]) -> str:
    steps = job.get("steps", [])
    assert isinstance(steps, list)
    return "\n".join(str(step.get("run", "")) for step in steps if isinstance(step, dict))


def _environment(job: dict[str, Any]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for step in job.get("steps", []):
        if not isinstance(step, dict):
            continue
        values = step.get("env", {})
        if isinstance(values, dict):
            merged.update({str(key): str(value) for key, value in values.items()})
    return merged


def test_collector_job_fails_closed_and_runs_pg_regressions() -> None:
    jobs = _workflow()["jobs"]
    assert isinstance(jobs, dict)
    collector = jobs["collector-quality"]
    assert isinstance(collector, dict)
    commands = _commands(collector)
    environment = _environment(collector)
    assert "tests/postgres" in commands
    assert "tests/distributed" in commands  # M16: cross-process evidence runs in CI
    assert "tests/e2e/test_pg_crash_restart.py" in commands
    assert environment["RESEARCHOS_REQUIRE_COLLECTOR"] == "1"
    assert environment["RESEARCHOS_REQUIRE_POSTGRES"] == "1"


def test_container_job_runs_every_docker_marked_test() -> None:
    jobs = _workflow()["jobs"]
    assert isinstance(jobs, dict)
    container = jobs["container-quality"]
    assert isinstance(container, dict)
    commands = _commands(container)
    assert "-m requires_docker" in commands
    assert "tests/adapters/execution" not in commands


def _m0_runner() -> Any:
    path = ROOT / ".cursor" / "skills" / "cursor-framework-check" / "scripts" / "run_all_checks.py"
    spec = importlib.util.spec_from_file_location("m0_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_m0_profile_runs_console_lint_test_typecheck_and_build() -> None:
    checks = _m0_runner().typescript_checks()
    names = {check.name for check in checks}
    assert {
        "typescript/web-lint",
        "typescript/web-test",
        "typescript/web-typecheck",
        "typescript/web-build",
    } <= names

    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert "apps/web" in package["scripts"]["typecheck"]
