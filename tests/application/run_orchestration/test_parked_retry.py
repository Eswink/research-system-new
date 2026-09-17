"""应用层：声明了退避的重排把 run 停在 PAUSED（PLAN-20260915-081）。

覆盖三件事，都是可证伪断言：

1. `execute_phases` 遇到"交回派发方的重排"时返回 PAUSED，并把**失败的任务 + 它后面的
   所有 specs** 交回 `on_pause`（含失败任务本身，否则 resume 会跳过要重试的那一个）；
2. 非重排的失败仍然照旧 fail run（对照，防止"什么都停车"）；
3. 执行器在 deadline 之前再被调用一次：**不执行**、返回 `retry_deferred`（重新停车），
   而不是把这次调用判成 task FAILED（否则一次早到的 resume 会把 run 弄死）。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any

from adapters.fakes import FakeArtifactStore, FakeWorkflowEngine
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.agent_runtime import (
    AgentSessionHandle,
    AgentSessionResult,
    AgentSessionSpec,
)
from packages.application.ports.errors import TransientPortError
from packages.application.run_orchestration.phase_runner import (
    PhaseContext,
    PhaseRunnerDeps,
    execute_phases,
)
from packages.application.run_orchestration.task_executor import (
    ExecutionDeps,
    SessionSpecContext,
    execute_task,
)
from packages.application.run_orchestration.task_phase_helpers import PhaseStep
from packages.domain.core import ID
from packages.domain.enums import FailureCategory
from packages.domain.run_state import ResearchRunState
from packages.domain.tasks import RetryPolicy
from tests.contracts.fixtures import research_task, task_contract

_RUN_ID = "5b6c7d8e-9f0a-4b1c-8d2e-3f4a5b6c7d8e"
START = datetime(2026, 9, 18, 9, 0, 0, tzinfo=timezone.utc)


@dataclass(slots=True)
class _Clock:
    value: datetime = START

    def __call__(self) -> datetime:
        return self.value


@dataclass(slots=True)
class _FailingRuntime:
    runs: int = 0

    def create_session(self, spec: AgentSessionSpec) -> AgentSessionHandle:
        return AgentSessionHandle(session_id=f"session-{spec.task_id.value}")

    def run(self, session_id: str) -> AgentSessionResult:
        self.runs += 1
        raise TransientPortError("model timed out", failure_category=FailureCategory.MODEL_TIMEOUT)

    def pause(self, session_id: str) -> None: ...
    def cancel(self, session_id: str) -> None: ...


def _spec(phase_id: str, agent: str) -> tuple[Any, Any, Any]:
    task = replace(
        research_task(),
        id=ID.generate(),
        run_id=ID(_RUN_ID),
        assigned_agent_id=agent,
        idempotency_key=f"{phase_id}:{agent}",
    )
    return (task, task_contract(), _context(phase_id))


def _context(phase_id: str) -> SessionSpecContext:
    from tests.contracts.fixtures import agent_spec, role_definition

    return SessionSpecContext(
        role=role_definition(),
        agent=agent_spec(),
        frozen_manifest_digest="manifest-digest",
        phase_id=phase_id,
    )


def _deps(*, handed: list[tuple[Any, ...]]) -> PhaseRunnerDeps:
    return PhaseRunnerDeps(
        workflow=FakeWorkflowEngine(),
        runtime=_FailingRuntime(),  # type: ignore[arg-type]
        artifacts=FakeArtifactStore(),
        on_pause=handed.append,
    )


def _ctx(specs: tuple[tuple[Any, Any, Any], ...]) -> PhaseContext:
    return PhaseContext(
        command=None,
        resolve_sessions=lambda: specs,
        frozen_manifest_digest="manifest-digest",
        trace_id="trace-1",
        run_id=_RUN_ID,
    )


def _deferring_runner(defer_ids: set[str]) -> Any:
    """替身执行器：名单里的任务返回"重排（等 deadline）"，其余成功。"""

    def run(deps: Any, tctx: Any) -> Any:
        if tctx.task.id.value in defer_ids:
            return PhaseStep(retry_deferred=True)
        return PhaseStep(handoff={"summary": "ok"}, verdict="PASS")

    return run


def test_a_deferred_retry_parks_the_run_and_hands_the_task_back(monkeypatch: Any) -> None:
    """重排 ⇒ PAUSED，交回的 specs 以**失败的那个任务**开头（否则 resume 会跳过它）。"""
    from packages.application.run_orchestration import phase_runner as pr

    first = _spec("phase-a", "agent-1")
    second = _spec("phase-b", "agent-2")
    monkeypatch.setattr(pr, "_execute_one_task", _deferring_runner({first[0].id.value}))
    handed: list[tuple[Any, ...]] = []

    outcome = execute_phases(_deps(handed=handed), _ctx((first, second)))

    assert outcome.state == ResearchRunState.State.PAUSED
    assert outcome.system_failure is False
    assert [spec[0].id.value for spec in handed[0]] == [first[0].id.value, second[0].id.value]
    assert outcome.tasks == (), "第一个任务没成功，不应计入已完成的 task outcomes"


def test_only_the_remaining_specs_are_handed_back(monkeypatch: Any) -> None:
    """组内前面的任务已经成功：交回的是"失败任务 + 其后"，已完成的 task 仍在 outcome 里。"""
    from packages.application.run_orchestration import phase_runner as pr

    first = _spec("phase-a", "agent-1")
    second = _spec("phase-a", "agent-2")
    third = _spec("phase-b", "agent-3")
    monkeypatch.setattr(pr, "_execute_one_task", _deferring_runner({second[0].id.value}))
    handed: list[tuple[Any, ...]] = []

    outcome = execute_phases(_deps(handed=handed), _ctx((first, second, third)))

    assert outcome.state == ResearchRunState.State.PAUSED
    assert [spec[0].id.value for spec in handed[0]] == [second[0].id.value, third[0].id.value]
    assert [task.task.id.value for task in outcome.tasks] == [first[0].id.value]


def test_a_plain_failure_still_fails_the_run(monkeypatch: Any) -> None:
    """对照：不是重排的失败照旧收敛成 run FAILED（防止"什么都停车"）。"""
    from packages.application.run_orchestration import phase_runner as pr

    def failing(deps: Any, tctx: Any) -> Any:
        return PhaseStep(failure=deps.fail(tctx.ctx.run_id, "boom", True))

    monkeypatch.setattr(pr, "_execute_one_task", failing)
    handed: list[tuple[Any, ...]] = []

    outcome = execute_phases(_deps(handed=handed), _ctx((_spec("phase-a", "agent-1"),)))

    assert outcome.state == ResearchRunState.State.FAILED
    assert handed == [], "普通失败不交回 specs（没有可续跑的上下文）"


def test_a_second_call_before_the_deadline_defers_instead_of_failing() -> None:
    """deadline 之前再执行一次：不跑会话、返回 retry_deferred（不是 task FAILED）。

    否则一次早到的 resume 会把 run 判失败——而 FAILED 是终态，重排就真的死了。
    """
    clock = _Clock()
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=60, now=clock)
    runtime = _FailingRuntime()
    task = replace(research_task(), run_id=ID(_RUN_ID), idempotency_key="phase-a:agent-1")
    contract = replace(
        task_contract(),
        retry_policy=RetryPolicy(
            max_attempts=3,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=3600,
        ),
    )
    deps = ExecutionDeps(engine, runtime)  # type: ignore[arg-type]

    first = execute_task(deps, task, contract, _context("phase-a"), "trace-1")
    second = execute_task(deps, task, contract, _context("phase-a"), "trace-2")

    assert first.retry_deferred is True
    assert second.retry_deferred is True, "还没到期 ⇒ 继续停车，而不是判失败"
    assert "waiting for its retry backoff" in second.message
    assert runtime.runs == 1, "deadline 之前一次都不该执行"
    engine.close()
