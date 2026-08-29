"""M15 债务清偿:PHASE 级 span 测试(分组、父子链接、失败传播)。

execute_phases 按连续相同 `spec_context.phase_id` 分组,每组外包
PHASE span(name="phase");组内 TASK span correlation 携带 phase_run_id,
经 parent_span_ref 规则自动父链接到 PHASE span。任务失败 → PHASE end
outcome=FAILED。phase_id 为空(resume 重建路径)时不发 PHASE correlation。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from adapters.fakes import FakeAgentRuntime, FakeArtifactStore, FakeWorkflowEngine
from adapters.fakes.telemetry_sink import FakeTelemetrySink
from packages.application.run_orchestration.phase_runner import (
    PhaseContext,
    PhaseRunnerDeps,
    RunOutcome,
    execute_phases,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.enums import (
    ActivationPolicy,
    ModelBindingMode,
    RoleCategory,
)
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.run_state import ResearchRunState
from tests.contracts.fixtures import research_task, task_contract

_RUN_ID = "7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d"


def _spec_context(phase_id: str, agent: str) -> SessionSpecContext:
    return SessionSpecContext(
        role=RoleDefinition(
            id="researcher",
            role_type="researcher",
            category=RoleCategory.DISCOVERY,
            activation_default=ActivationPolicy.ALWAYS,
        ),
        agent=AgentSpec(
            id=agent,
            role="researcher",
            model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
        ),
        frozen_manifest_digest="manifest-digest",
        phase_id=phase_id,
    )


def _spec(phase_id: str, agent: str) -> tuple[Any, Any, Any]:
    base = research_task()
    task = replace(
        base,
        run_id=base.run_id,
        assigned_agent_id=agent,
        idempotency_key=f"{phase_id}:{agent}",
    )
    return (task, task_contract(), _spec_context(phase_id, agent))


def _deps(telemetry: FakeTelemetrySink) -> PhaseRunnerDeps:
    return PhaseRunnerDeps(
        workflow=FakeWorkflowEngine(),
        runtime=FakeAgentRuntime(),
        artifacts=FakeArtifactStore(),
        telemetry=telemetry,
    )


def _ctx(specs: tuple[tuple[Any, Any, Any], ...]) -> PhaseContext:
    return PhaseContext(
        command=None,
        resolve_sessions=lambda: specs,
        frozen_manifest_digest="manifest-digest",
        trace_id="trace-1",
        run_id=_RUN_ID,
    )


def _ok_step() -> object:
    from packages.application.run_orchestration.task_phase_helpers import PhaseStep

    return PhaseStep(handoff={"summary": "ok"}, verdict="PASS")


def test_phase_spans_group_tasks_and_parent_link(monkeypatch: Any) -> None:
    """两阶段各包一个 PHASE span;组内 TASK 父引用指向对应 PHASE span。"""
    from packages.application.run_orchestration import phase_runner as pr

    monkeypatch.setattr(pr, "_execute_one_task", lambda deps, tctx: _ok_step())
    fake = FakeTelemetrySink()
    specs = (
        _spec("phase-a", "agent-1"),
        _spec("phase-a", "agent-2"),
        _spec("phase-b", "agent-3"),
    )
    execute_phases(_deps(fake), _ctx(specs))
    phase_begins = [b for b in fake.begins if b.scope.value == "phase"]
    task_begins = [b for b in fake.begins if b.scope.value == "task"]
    assert len(phase_begins) == 2
    assert len(task_begins) == 3  # 3 specs(phase-a×2 + phase-b×1)
    assert phase_begins[0].correlation.phase_run_id == "phase-a"
    assert phase_begins[1].correlation.phase_run_id == "phase-b"
    # 父子链接:TASK 的 parent_span_ref == 对应 PHASE 的 span_ref
    refs = {b.correlation.phase_run_id: b.span_ref.value for b in phase_begins}
    for begin in task_begins:
        assert begin.parent_span_ref is not None
        assert begin.parent_span_ref.value == refs[begin.correlation.phase_run_id]
    # TASK span correlation 携带 phase_run_id(父派生依据)
    assert {b.correlation.phase_run_id for b in task_begins} == {"phase-a", "phase-b"}
    # 成功路径:PHASE end outcome=OK
    phase_ends = [
        e for e in fake.ends if e.span_ref.value in {b.span_ref.value for b in phase_begins}
    ]
    assert all(end.outcome.value == "OK" for end in phase_ends)


def test_phase_span_marks_failed_outcome_on_task_failure(monkeypatch: Any) -> None:
    """任务失败 → 对应 PHASE span end outcome=FAILED;后续阶段不执行。"""
    from packages.application.run_orchestration import phase_runner as pr
    from packages.application.run_orchestration.task_phase_helpers import PhaseStep

    def _fail(deps: object, tctx: Any) -> object:
        return PhaseStep(
            failure=RunOutcome(
                run_id=tctx.ctx.run_id,
                state=ResearchRunState.State.FAILED,
                message="task failed",
                system_failure=False,
            )
        )

    monkeypatch.setattr(pr, "_execute_one_task", _fail)
    fake = FakeTelemetrySink()
    specs = (
        _spec("phase-a", "agent-1"),
        _spec("phase-b", "agent-2"),
    )
    outcome = execute_phases(_deps(fake), _ctx(specs))
    assert outcome.state == ResearchRunState.State.FAILED
    phase_refs = {b.span_ref.value for b in fake.begins if b.scope.value == "phase"}
    phase_ends = [e for e in fake.ends if e.span_ref.value in phase_refs]
    assert phase_ends and phase_ends[0].outcome.value == "FAILED"
    # 失败后后续阶段不执行:只有 phase-a 的 PHASE/TASK span
    assert len(phase_refs) == 1
    assert len([b for b in fake.begins if b.scope.value == "task"]) == 1


def test_empty_phase_id_falls_back_to_run_parent(monkeypatch: Any) -> None:
    """resume 重建路径(phase_id 缺省)→ TASK 无 PHASE correlation,落回 RUN 父。"""
    from packages.application.run_orchestration import phase_runner as pr

    monkeypatch.setattr(pr, "_execute_one_task", lambda deps, tctx: _ok_step())
    fake = FakeTelemetrySink()
    specs = (_spec("", "agent-1"),)
    execute_phases(_deps(fake), _ctx(specs))
    task_begins = [b for b in fake.begins if b.scope.value == "task"]
    assert len(task_begins) == 1
    assert task_begins[0].correlation.phase_run_id is None
    phase_begins = [b for b in fake.begins if b.scope.value == "phase"]
    assert len(phase_begins) == 1  # 仍包一个空 phase 分组(无 correlation phase id)
    assert phase_begins[0].correlation.phase_run_id is None
