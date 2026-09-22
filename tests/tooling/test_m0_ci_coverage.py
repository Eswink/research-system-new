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


# ------------------------------------------- tokenizer 预热 =「每轮一次受控外部下载」（EC-05）

#: 需要预热的步骤：跑 Python 门的那些命令形态（作业级判定，见 `_python_gate_steps`）。
_PYTHON_GATE_MARKERS = ("-m pytest", "run_all_checks.py", "adapters.cli.eval_gate")
#: 预热命令的最小受判形态：装包已 frozen，且真的把词表拉下来。
_PREWARM_MARKERS = ("import litellm", "--frozen")
#: 「措辞与事实同源」的那**一句**（逐字，两处都必须有；不是把整段散文纳入判据）。
#: 实测口径（2026-09-22）：环境准备阶段那一次请求是 litellm 的 model cost map，
#: 冷 `TIKTOKEN_CACHE_DIR` 下**未**观察到词表下载 ⇒ 句子用「**至多**有一次」，不写「恰一次」。
_CANONICAL_SENTENCE = "CI 每轮至多有一次受控外部下载"


def _step_runs(job: dict[str, Any]) -> list[str]:
    steps = job.get("steps", [])
    assert isinstance(steps, list)
    return [str(step.get("run", "")) for step in steps if isinstance(step, dict)]


def test_every_job_that_runs_the_python_gate_prewarms_the_tokenizer_first() -> None:
    """**结构**判据：跑 Python 门的作业必须在跑门**之前**预热 tokenizer。

    为什么需要它（EC-05 的缺口）：冷装环境下首次 `import litellm` 会真的下载
    `cl100k_base`；workflow 用一个预热门把这次下载挪到**判据进程之外**。删掉任一个预热门，
    在**热缓存**的本机上默认门仍然全绿，只有 CI 的干净安装才会炸——所以这条位置关系必须受判。

    判据读的是**步骤顺序**，不是注释散文：把作业的步骤按序切分，凡含 `_PYTHON_GATE_MARKERS`
    的步骤即「跑门」，其**之前**必须有一个同时含 `_PREWARM_MARKERS` 的步骤。
    """
    jobs = _workflow()["jobs"]
    assert isinstance(jobs, dict)
    gate_jobs = 0
    for name, job in jobs.items():
        assert isinstance(job, dict)
        runs = _step_runs(job)
        prewarm_at = [i for i, run in enumerate(runs) if all(m in run for m in _PREWARM_MARKERS)]
        gate_at = [
            i for i, run in enumerate(runs) if any(marker in run for marker in _PYTHON_GATE_MARKERS)
        ]
        if not gate_at:
            continue
        gate_jobs += 1
        assert prewarm_at, f"{name} runs the Python gate without prewarming the tokenizer cache"
        assert min(prewarm_at) < min(gate_at), (
            f"{name} prewarms the tokenizer cache only after the gate already ran"
        )
    # 反证：这个判据不是空转——今天的 workflow 确实有多个跑门作业。
    assert gate_jobs >= 4, f"only {gate_jobs} gate-running job(s) found; the scan is probably wrong"


def test_the_one_controlled_download_sentence_is_verbatim_in_both_homes() -> None:
    """EC-05「措辞与事实同源」：同一句话在**判据自己的家**与**架构文档**里逐字在场。

    只锁这一句，不把整段散文纳入判据：它陈述的是「判据进程内离线」之外仍然存在的那一次
    受控外部下载，改掉任何一处都会被这里抓住。
    """
    guard = (ROOT / "tests" / "egress_guard.py").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "architecture" / "AGENT_RUNTIME.md").read_text(encoding="utf-8")
    assert _CANONICAL_SENTENCE in guard, "egress guard no longer states the controlled download"
    assert _CANONICAL_SENTENCE in architecture, "architecture doc lost the same sentence"
