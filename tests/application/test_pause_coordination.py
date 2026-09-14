"""协作式暂停（PLAN-20260914-048）应用层用例。

覆盖两件事，都是"暂停必须真被观测/真被协调"的可证伪断言：

1. `execute_phases` 在组边界读到 `pause_requested()` 时**零任务执行**返回 PAUSED，
   并把剩余 specs（含当前组）交回 `on_pause`；
2. service 侧暂停谓词只读 canonical run state，且没有暂停上下文时
   `resume_paused` 抛 InvalidInputError（不伪造续跑）。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from adapters.fakes import FakeAgentRuntime, FakeArtifactStore, FakeWorkflowEngine
from adapters.fakes.event_publisher import FakeEventPublisher
from packages.application.ports.errors import InvalidInputError
from packages.application.run_orchestration.phase_runner import (
    PhaseContext,
    PhaseRunnerDeps,
    execute_phases,
)
from packages.application.run_orchestration.service import (
    OrchestrationDependencies,
    RunOrchestrationService,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.core import ID
from packages.domain.enums import (
    ActivationPolicy,
    ModelBindingMode,
    RoleCategory,
)
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.run import ResearchRun
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
        assigned_agent_id=agent,
        idempotency_key=f"{phase_id}:{agent}",
    )
    return (task, task_contract(), _spec_context(phase_id, agent))


def _ctx(specs: tuple[tuple[Any, Any, Any], ...]) -> PhaseContext:
    return PhaseContext(
        command=None,
        resolve_sessions=lambda: specs,
        frozen_manifest_digest="manifest-digest",
        trace_id="trace-1",
        run_id=_RUN_ID,
    )


def _counting_runner(executed: list[str]) -> Any:
    """替身执行器：记录被真正执行的任务（不触网、不写 store）。"""
    from packages.application.run_orchestration.task_phase_helpers import PhaseStep

    def run(deps: Any, tctx: Any) -> Any:
        executed.append(tctx.task.id.value)
        return PhaseStep(handoff={"summary": "ok"}, verdict="PASS")

    return run


def test_pause_requested_skips_every_group_and_hands_specs_back(monkeypatch: Any) -> None:
    """暂停信号在第一次边界即为真：一个任务都不执行，剩余 specs 全部交回。"""
    from packages.application.run_orchestration import phase_runner as pr

    executed: list[str] = []
    monkeypatch.setattr(pr, "_execute_one_task", _counting_runner(executed))
    handed: list[tuple[Any, ...]] = []
    specs = (_spec("phase-a", "agent-1"), _spec("phase-b", "agent-2"))
    deps = PhaseRunnerDeps(
        workflow=FakeWorkflowEngine(),
        runtime=FakeAgentRuntime(),
        artifacts=FakeArtifactStore(),
        on_pause=handed.append,
        pause_requested=lambda: True,
    )

    outcome = execute_phases(deps, _ctx(specs))

    assert executed == []
    assert outcome.state == ResearchRunState.State.PAUSED
    assert outcome.manifest_digest == "manifest-digest"
    assert len(handed) == 1
    handed_ids = tuple(spec[0].id.value for spec in handed[0])
    assert handed_ids == tuple(spec[0].id.value for spec in specs)


def test_pause_is_observed_at_the_next_boundary(monkeypatch: Any) -> None:
    """信号在第一组之后翻转：该组已执行，后续组一个任务都不执行。"""
    from packages.application.run_orchestration import phase_runner as pr

    executed: list[str] = []
    monkeypatch.setattr(pr, "_execute_one_task", _counting_runner(executed))
    flips = {"count": 0}

    def observed() -> bool:
        flips["count"] += 1
        return flips["count"] > 1

    handed: list[tuple[Any, ...]] = []
    first = _spec("phase-a", "agent-1")
    second = _spec("phase-b", "agent-2")
    deps = PhaseRunnerDeps(
        workflow=FakeWorkflowEngine(),
        runtime=FakeAgentRuntime(),
        artifacts=FakeArtifactStore(),
        on_pause=handed.append,
        pause_requested=observed,
    )

    outcome = execute_phases(deps, _ctx((first, second)))

    assert executed == [first[0].id.value]
    assert outcome.state == ResearchRunState.State.PAUSED
    assert tuple(spec[0].id.value for spec in handed[0]) == (second[0].id.value,)


def test_without_pause_signal_the_run_completes(monkeypatch: Any) -> None:
    """对照组：谓词恒假时正常跑完（防止"总是暂停"的错误实现）。"""
    from packages.application.run_orchestration import phase_runner as pr

    executed: list[str] = []
    monkeypatch.setattr(pr, "_execute_one_task", _counting_runner(executed))
    specs = (_spec("phase-a", "agent-1"), _spec("phase-b", "agent-2"))
    deps = PhaseRunnerDeps(
        workflow=FakeWorkflowEngine(),
        runtime=FakeAgentRuntime(),
        artifacts=FakeArtifactStore(),
        on_pause=lambda _specs: None,
        pause_requested=lambda: False,
    )

    outcome = execute_phases(deps, _ctx(specs))

    assert len(executed) == 2
    assert outcome.state == ResearchRunState.State.SUCCEEDED


def _service() -> tuple[RunOrchestrationService, FakeWorkflowEngine]:
    workflow = FakeWorkflowEngine()
    service = RunOrchestrationService(
        OrchestrationDependencies(
            runtime=FakeAgentRuntime(),
            workflow=workflow,
            artifacts=FakeArtifactStore(),
            events=FakeEventPublisher(),
        )
    )
    return service, workflow


def test_pause_predicate_reads_canonical_run_state_only() -> None:
    """谓词来源是 canonical run state：未知 run 不是暂停（不靠进程内标志推断）。"""
    service, workflow = _service()

    assert service.pause_requested(_RUN_ID) is False
    workflow.set_run_state(_RUN_ID, ResearchRunState.State.RUNNING)
    assert service.pause_requested(_RUN_ID) is False
    workflow.set_run_state(_RUN_ID, ResearchRunState.State.PAUSED)
    assert service.pause_requested(_RUN_ID) is True


def test_resume_without_paused_context_is_an_error_not_a_fake_resume() -> None:
    """没有暂停上下文时 resume_paused 必须报错（调用方据此降级为"只解除暂停"）。"""
    service, _ = _service()
    run = ResearchRun(id=ID(_RUN_ID), project_id="p", protocol_id="proto")

    assert service.has_paused_context(_RUN_ID) is False
    try:
        service.resume_paused(_RUN_ID, run)
    except InvalidInputError:
        return
    raise AssertionError("resume_paused must reject a missing paused context")
