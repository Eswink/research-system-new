"""应用层：`failure_policy` 的 run 级消费者（GOAL-004 cycle 3 = EC-03）。

契约声明 `on_task_failure: CONTINUE` 时，一个任务的**终局失败**不再让 run 立刻失败：
失败被记账（`TaskOutcome.failure_policy`），**剩余工作照跑**，最后收敛 `DEGRADED`；
未声明 / 显式 `FAIL_RUN` ⇒ 与基线逐字一致（首个失败即 run FAILED、后续任务不再被尝试）。

这里不替身执行器：走真 `_execute_one_task`（`failure_step` 真读契约视图），
用"会话尝试次数"作为"剩余工作有没有跑"的可观测证据。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from adapters.fakes import FakeArtifactStore, FakeWorkflowEngine
from packages.application.ports.agent_runtime import (
    AgentSessionHandle,
    AgentSessionResult,
    AgentSessionSpec,
)
from packages.application.ports.errors import TransientPortError
from packages.application.run_orchestration.phase_runner import (
    PhaseContext,
    PhaseRunnerDeps,
    RunOutcome,
    execute_phases,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.core import ID
from packages.domain.enums import FailureCategory
from packages.domain.events import EventType
from packages.domain.run_state import ResearchRunState
from tests.contracts.fixtures import research_task, task_contract

_RUN_ID = "7d1a2b3c-4e5f-4a6b-8c9d-0e1f2a3b4c5d"


@dataclass(slots=True)
class _FailingRuntime:
    """每次会话都失败（可数）：尝试次数就是"剩余工作有没有跑"的证据。"""

    runs: int = 0

    def create_session(self, spec: AgentSessionSpec) -> AgentSessionHandle:
        return AgentSessionHandle(session_id=f"session-{spec.task_id.value}")

    def run(self, session_id: str) -> AgentSessionResult:
        self.runs += 1
        raise TransientPortError("model timed out", failure_category=FailureCategory.MODEL_TIMEOUT)

    def pause(self, session_id: str) -> None: ...
    def cancel(self, session_id: str) -> None: ...


def _spec(phase_id: str, agent: str, policy: dict[str, Any]) -> tuple[Any, Any, Any]:
    task = replace(
        research_task(),
        id=ID.generate(),
        run_id=ID(_RUN_ID),
        assigned_agent_id=agent,
        idempotency_key=f"{phase_id}:{agent}",
    )
    return (task, replace(task_contract(), failure_policy=policy), _context(phase_id))


def _context(phase_id: str) -> SessionSpecContext:
    from tests.contracts.fixtures import agent_spec, role_definition

    return SessionSpecContext(
        role=role_definition(),
        agent=agent_spec(),
        frozen_manifest_digest="manifest-digest",
        phase_id=phase_id,
    )


def _deps(runtime: _FailingRuntime, *, degraded: list[Any] | None = None) -> PhaseRunnerDeps:
    def degrade(ctx: Any, tolerated: tuple[Any, ...], message: str) -> RunOutcome:
        assert degraded is not None
        degraded.append((ctx.run_id, tolerated, message))
        return RunOutcome(
            run_id=ctx.run_id,
            state=ResearchRunState.State.DEGRADED,
            message=message,
            tasks=tolerated,
        )

    return PhaseRunnerDeps(
        workflow=FakeWorkflowEngine(),
        runtime=runtime,  # type: ignore[arg-type]
        artifacts=FakeArtifactStore(),
        degrade_run=degrade if degraded is not None else None,
    )


def _ctx(specs: tuple[tuple[Any, Any, Any], ...]) -> PhaseContext:
    return PhaseContext(
        command=None,
        resolve_sessions=lambda: specs,
        frozen_manifest_digest="manifest-digest",
        trace_id="trace-1",
        run_id=_RUN_ID,
    )


def _three_specs(policy: dict[str, Any]) -> tuple[tuple[Any, Any, Any], ...]:
    """同组两个 + 后续 phase 一个：三个都失败才能证明"两组都没被停住"。"""
    return (
        _spec("phase-a", "agent-1", policy),
        _spec("phase-a", "agent-2", policy),
        _spec("phase-b", "agent-3", policy),
    )


def test_declared_continue_tolerates_failures_and_runs_the_rest() -> None:
    runtime = _FailingRuntime()
    degraded: list[Any] = []

    outcome = execute_phases(
        _deps(runtime, degraded=degraded),
        _ctx(_three_specs({"on_task_failure": "CONTINUE"})),
    )

    assert runtime.runs == 3, "被容忍的失败不能停住同组后续任务，也不能停住后续 phase"
    assert outcome.state == ResearchRunState.State.DEGRADED
    assert outcome.system_failure is False
    assert [task.outcome for task in outcome.tasks] == ["FAILED", "FAILED", "FAILED"]
    assert {task.failure_policy for task in outcome.tasks} == {"CONTINUE"}
    assert len(degraded) == 1 and degraded[0][1] == outcome.tasks


def test_undeclared_policy_keeps_the_baseline_fail_fast() -> None:
    runtime = _FailingRuntime()

    outcome = execute_phases(_deps(runtime), _ctx(_three_specs({})))

    assert runtime.runs == 1, "缺省就是 fail-fast：第一个失败之后不再尝试任何任务"
    assert outcome.state == ResearchRunState.State.FAILED
    assert outcome.tasks == ()


def test_a_declared_fail_run_is_the_baseline_too() -> None:
    runtime = _FailingRuntime()

    outcome = execute_phases(_deps(runtime), _ctx(_three_specs({"on_task_failure": "FAIL_RUN"})))

    assert runtime.runs == 1
    assert outcome.state == ResearchRunState.State.FAILED


def test_an_unhonored_key_does_not_change_anything() -> None:
    """`on_validation_failure` 今天没有消费者 ⇒ 声明它不改变行为（诚实边界）。"""
    runtime = _FailingRuntime()

    outcome = execute_phases(
        _deps(runtime),
        _ctx(_three_specs({"on_validation_failure": "DEAD_LETTER"})),
    )

    assert runtime.runs == 1
    assert outcome.state == ResearchRunState.State.FAILED


def test_the_tolerated_path_publishes_task_failures_and_never_run_completed() -> None:
    """应用层的可见事实：每条被容忍的失败发 `task.failed`（带策略），不发 `run.completed`。

    `run.degraded` 由 service 的 `degrade_run` 回调发布（payload 的用例在 service 侧）。
    """
    published: list[tuple[EventType, dict[str, object]]] = []
    runtime = _FailingRuntime()
    deps = replace(
        _deps(runtime),
        publish=lambda event_type, payload, *_args: published.append((event_type, payload)),
    )

    outcome = execute_phases(deps, _ctx(_three_specs({"on_task_failure": "CONTINUE"})))

    assert outcome.state == ResearchRunState.State.DEGRADED
    kinds = [event_type for event_type, _ in published]
    assert kinds.count(EventType.TASK_FAILED) == 3
    assert EventType.RUN_COMPLETED not in kinds, "有被容忍的失败就不发 run.completed"
    assert {
        payload["failure_policy"] for kind, payload in published if kind is EventType.TASK_FAILED
    } == {"CONTINUE"}


def test_the_degrade_callback_receives_the_tolerated_failures_and_the_policy_message() -> None:
    degraded: list[Any] = []
    runtime = _FailingRuntime()

    execute_phases(
        _deps(runtime, degraded=degraded),
        _ctx(_three_specs({"on_task_failure": "CONTINUE"})),
    )

    assert len(degraded) == 1
    run_id, tolerated, message = degraded[0]
    assert run_id == _RUN_ID
    assert len(tolerated) == 3
    assert "on_task_failure=CONTINUE" in message, "消息必须点名是哪条策略允许的"
