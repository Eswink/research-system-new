"""Phase 执行循环：按 DAG 拓扑序运行任务，每个任务经独立 Evaluation gate。

与 service.py 分离：编排入口（compile/freeze/cancel/resume）与执行语义
（task loop + gate + handoff）职责分离；副作用经注入的 Port 与回调，
保持 application 层不直接实例化 adapter。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from packages.application.ports.agent_runtime import (
    AgentRuntime,
    AgentSessionResult,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.ports.workflow_engine import WorkflowEngine
from packages.application.run_orchestration.claim_promotion import (
    ClaimPromotionContext,
    promote_registered_claims,
)
from packages.application.run_orchestration.commands import StartRunCommand
from packages.application.run_orchestration.evaluation_gate import (
    EvaluationInputs,
    GateOutcome,
    evaluate_task_gate,
)
from packages.application.run_orchestration.handoff_builder import (
    HandoffPayload,
    build_handoff,
)
from packages.application.run_orchestration.result_handler import (
    RegistrationDeps,
    ResultRegistration,
    register_session_result,
)
from packages.application.run_orchestration.task_executor import (
    ExecutionDeps,
    SessionSpecContext,
    execute_task,
)
from packages.application.run_orchestration.usage_recording import record_task_usage
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


def execute_phases(deps: PhaseRunnerDeps, ctx: PhaseContext) -> RunOutcome:
    """按 phase DAG 拓扑序执行任务；每个任务经独立 Evaluation gate。"""
    outcomes: list[TaskOutcome] = []
    handoffs: dict[str, object] = {}
    specs = ctx.pending or ctx.resolve_sessions()
    for task, contract, spec_context in specs:
        step = _execute_one_task(
            deps, _TaskContext(task=task, contract=contract, spec_context=spec_context, ctx=ctx)
        )
        if step.failure is not None:
            return step.failure
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


@dataclass(frozen=True, slots=True)
class _TaskStep:
    handoff: object | None = None
    verdict: str | None = None
    failure: RunOutcome | None = None


@dataclass(frozen=True, slots=True)
class _TaskContext:
    """单任务上下文（参数对象，避免参数爆发）。"""

    task: ResearchTask
    contract: TaskContract
    spec_context: SessionSpecContext
    ctx: PhaseContext


def _execute_one_task(deps: PhaseRunnerDeps, tctx: _TaskContext) -> _TaskStep:
    """单个任务：执行 → 注册 → gate → handoff；失败返回收敛 RunOutcome。"""
    task = tctx.task
    deps.emit(
        EventType.TASK_CREATED,
        {"task_id": task.id.value},
        task.run_id.value,
        tctx.ctx.trace_id,
        task.id.value,
    )
    execution = execute_task(
        ExecutionDeps(deps.workflow, deps.runtime),
        task,
        tctx.contract,
        tctx.spec_context,
        trace_id=tctx.ctx.trace_id,
    )
    if not execution.succeeded:
        return _TaskStep(
            failure=deps.fail(
                tctx.ctx.run_id,
                f"task {task.id.value} failed: {execution.message}",
                execution.failure_category is not None,
            )
        )
    assert execution.session_result is not None
    return _register_and_gate(deps, tctx, execution.session_result)


def _register_and_gate(
    deps: PhaseRunnerDeps, tctx: _TaskContext, session_result: AgentSessionResult
) -> _TaskStep:
    """会话结果注册（Artifact/Evidence）+ AcceptanceCriteria gate。"""
    task = tctx.task
    registered = _register_or_fail(deps, tctx, session_result)
    if isinstance(registered, str):
        return _TaskStep(
            failure=deps.fail(
                tctx.ctx.run_id,
                f"task {task.id.value} produced malformed result: {registered}",
                True,
            )
        )
    registration = registered
    gate = _evaluate_gate(deps, tctx, registration, session_result)
    if gate is None:
        return _TaskStep(
            failure=deps.fail(
                tctx.ctx.run_id, f"task {task.id.value} rejected by acceptance gate", False
            )
        )
    if deps.ledger is not None:
        promote_registered_claims(
            ClaimPromotionContext(
                ledger=deps.ledger,
                reviewer=f"gate:{tctx.spec_context.agent.id}",
                run_id=tctx.ctx.run_id,
                trace_id=tctx.ctx.trace_id,
                task_id=tctx.task.id.value,
                emit=deps.emit,
            ),
            registration,
            gate,
        )
    _record_usage(deps, task)
    return _TaskStep(
        handoff=build_handoff(
            HandoffPayload(
                task=task,
                producer=f"agent:{tctx.spec_context.agent.id}",
                summary=f"phase output for {task.contract_id}",
                artifact_refs=registration.artifact_refs(),
                evidence_refs=registration.evidence_refs(),
                claim_refs=registration.claim_refs(),
                decision_refs=(gate.decision.id,),
            )
        ),
        verdict=gate.verdict,
    )


def _register_or_fail(
    deps: PhaseRunnerDeps, tctx: _TaskContext, session_result: AgentSessionResult
) -> ResultRegistration | str:
    """会话结果注册；malformed 返回错误消息（由调用方收敛为系统失败）。"""
    try:
        return register_session_result(
            RegistrationDeps(
                store=deps.artifacts,
                agent_id=tctx.spec_context.agent.id,
                ledger=deps.ledger,
            ),
            tctx.task,
            tctx.contract,
            session_result.structured_output,
        )
    except InvalidInputError as error:
        return str(error)


def _evaluate_gate(
    deps: PhaseRunnerDeps,
    tctx: _TaskContext,
    registration: ResultRegistration,
    session_result: AgentSessionResult,
) -> GateOutcome | None:
    """AcceptanceCriteria 求值；未通过返回 None。"""
    gate = evaluate_task_gate(
        tctx.task,
        tctx.contract,
        EvaluationInputs(
            structured_output=session_result.structured_output,
            artifacts=_artifact_view(registration),
            evidence_source_count=registration.evidence_source_count,
        ),
        reviewer=f"gate:{tctx.spec_context.agent.id}",
    )
    return gate if gate.passed else None


def _artifact_view(registration: ResultRegistration) -> dict[str, object]:
    """Artifact 视图：按 id 与短名（`{task}:{name}` 的 name 段）双索引。"""
    view: dict[str, object] = {}
    for artifact in registration.artifacts:
        view[artifact.id] = artifact
        view[artifact.id.split(":")[-1]] = artifact
    return view


def _record_usage(deps: PhaseRunnerDeps, task: ResearchTask) -> None:
    """task 完成后的确定性用量记录（entry_id 幂等，见 usage_recording）。"""
    record_task_usage(deps.budget, task)
