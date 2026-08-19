"""Phase 执行循环：按 DAG 拓扑序运行任务，每个任务经独立 Evaluation gate。

与 service.py 分离：编排入口（compile/freeze/cancel/resume）与执行语义
（task loop + gate + handoff）职责分离；副作用经注入的 Port 与回调，
保持 application 层不直接实例化 adapter。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from packages.application.memory.gate import MemoryGateDeps
from packages.application.ports.agent_runtime import AgentRuntime
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.ports.workflow_engine import WorkflowEngine
from packages.application.run_orchestration.commands import StartRunCommand
from packages.application.run_orchestration.task_executor import (
    ExecutionDeps,
    SessionSpecContext,
    TaskExecutionResult,
    execute_task,
)
from packages.application.run_orchestration.task_phase_helpers import (
    PhaseStep,
    register_and_gate,
    register_and_gate_experiment,
)
from packages.domain.events import EventType
from packages.domain.run_state import ResearchRunState
from packages.domain.tasks import ResearchTask, TaskContract

SessionSpec = tuple[ResearchTask, TaskContract, SessionSpecContext]


@dataclass(frozen=True, slots=True)
class TaskOutcome:
    task: ResearchTask
    outcome: str
    verdict: str | None = None
    message: str = ""


@dataclass(frozen=True, slots=True)
class RunOutcome:
    run_id: str
    state: str
    message: str = ""
    tasks: tuple[TaskOutcome, ...] = ()
    manifest_digest: str | None = None
    handoff_digests: tuple[str, ...] = ()
    system_failure: bool = False


@dataclass(frozen=True, slots=True)
class PhaseRunnerDeps:
    """执行循环的 Port 组合与发布/失败回调（由 service 注入）。"""

    workflow: WorkflowEngine
    runtime: AgentRuntime
    artifacts: ArtifactStore
    budget: BudgetLedger | None = None
    ledger: EvidenceLedger | None = None
    experiment_task: (
        Callable[[ResearchTask, TaskContract, SessionSpecContext, str], TaskExecutionResult] | None
    ) = None
    memory_gate: MemoryGateDeps | None = None
    publish: Callable[[EventType, dict[str, object], str, str, str | None], None] | None = None
    fail_run: Callable[[str, str, bool], RunOutcome] | None = None

    def emit(
        self,
        event_type: EventType,
        payload: dict[str, object],
        run_id: str,
        trace_id: str,
        task_id: str | None,
    ) -> None:
        if self.publish is not None:
            self.publish(event_type, payload, run_id, trace_id, task_id)

    def fail(self, run_id: str, message: str, system_failure: bool) -> RunOutcome:
        if self.fail_run is not None:
            return self.fail_run(run_id, message, system_failure)
        return RunOutcome(
            run_id=run_id,
            state=ResearchRunState.State.FAILED,
            message=message,
            system_failure=system_failure,
        )


@dataclass(frozen=True, slots=True)
class PhaseContext:
    """执行循环的输入面（参数对象，避免参数爆发）。"""

    command: StartRunCommand | None
    resolve_sessions: Callable[[], tuple[SessionSpec, ...]]
    frozen_manifest_digest: str
    trace_id: str
    run_id: str
    pending: tuple[SessionSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class TaskContext:
    """单任务上下文（参数对象，避免参数爆发）。"""

    task: ResearchTask
    contract: TaskContract
    spec_context: SessionSpecContext
    ctx: PhaseContext


def execute_phases(deps: PhaseRunnerDeps, ctx: PhaseContext) -> RunOutcome:
    """按 phase DAG 拓扑序执行任务；每个任务经独立 Evaluation gate。"""
    outcomes: list[TaskOutcome] = []
    handoffs: dict[str, object] = {}
    specs = ctx.pending or ctx.resolve_sessions()
    for task, contract, spec_context in specs:
        step = _execute_one_task(
            deps, TaskContext(task=task, contract=contract, spec_context=spec_context, ctx=ctx)
        )
        if step.failure is not None:
            return step.failure  # type: ignore[no-any-return]
        handoffs[task.id.value] = step.handoff
        outcomes.append(TaskOutcome(task=task, outcome="SUCCEEDED", verdict=step.verdict))
    deps.emit(EventType.RUN_COMPLETED, {"run_id": ctx.run_id}, ctx.run_id, ctx.trace_id, None)
    return RunOutcome(
        run_id=ctx.run_id,
        state=ResearchRunState.State.SUCCEEDED,
        message="run completed",
        tasks=tuple(outcomes),
        manifest_digest=ctx.frozen_manifest_digest,
        handoff_digests=tuple(sorted(handoffs)),
        system_failure=False,
    )


def _execute_one_task(deps: PhaseRunnerDeps, tctx: TaskContext) -> PhaseStep:
    """单个任务：执行 → 注册 → gate → handoff；失败返回收敛 RunOutcome。"""
    task = tctx.task
    deps.emit(
        EventType.TASK_CREATED,
        {"task_id": task.id.value},
        task.run_id.value,
        tctx.ctx.trace_id,
        task.id.value,
    )
    if deps.experiment_task is not None and tctx.contract.id == "experiment_execution":
        execution = deps.experiment_task(
            task,
            tctx.contract,
            tctx.spec_context,
            tctx.ctx.trace_id,
        )
    else:
        execution = execute_task(
            ExecutionDeps(deps.workflow, deps.runtime),
            task,
            tctx.contract,
            tctx.spec_context,
            trace_id=tctx.ctx.trace_id,
        )
    if not execution.succeeded:
        return PhaseStep(
            failure=deps.fail(
                tctx.ctx.run_id,
                f"task {task.id.value} failed: {execution.message}",
                execution.failure_category is not None,
            )
        )
    if execution.experiment_outcome is not None:
        return register_and_gate_experiment(deps, tctx, execution)
    assert execution.session_result is not None
    return register_and_gate(deps, tctx, execution.session_result)
