"""Phase 执行循环：按 DAG 拓扑序运行任务，每个任务经独立 Evaluation gate。

与 service.py 分离：编排入口（compile/freeze/cancel/resume）与执行语义
（task loop + gate + handoff）职责分离；副作用经注入的 Port 与回调，
保持 application 层不直接实例化 adapter。
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

from packages.application.memory.gate import MemoryGateDeps
from packages.application.observability.scope import operation
from packages.application.observability.signals import (
    CorrelationRef,
    OperationOutcome,
    OperationScope,
)
from packages.application.ports.agent_runtime import AgentRuntime
from packages.application.ports.approval_store import ApprovalSpec
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.ports.telemetry_sink import TelemetrySink
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
    # cycle 20：语义 digest 与定价引用同源处理——不随执行结果回填，HTTP 边界就会
    # 静默丢字段，而 resume 的漂移校验（assert_semantics_frozen）恰恰只认它。
    manifest_semantic_digest: str | None = None
    # M15 定价冻结引用(BLOCKER-6):service 在 Manifest freeze 后把这两个
    # 字段回填执行结果，API 再持久化到 ResearchRun；不能只存 manifest digest
    # 否则 run 行会在 HTTP 边界静默丢失冻结价格引用。
    pricing_version: str | None = None
    pricing_digest: str | None = None
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
    telemetry: TelemetrySink | None = None
    # WP-H：human gate 注册面。approvals 与 human_gated 同源注入（service 仅在
    # store 存在时给出非空 gate 集）；on_pause 把未执行 specs 交回 service 暂存。
    approvals: Any | None = None
    human_gated: frozenset[str] = frozenset()
    on_pause: Callable[[tuple[SessionSpec, ...]], None] | None = None
    # PLAN-048：协作式暂停信号（读 canonical run state）。为真时在组边界停止，
    # 不执行该组任何任务；剩余 specs 经 on_pause 交回 service 暂存供 resume 续跑。
    pause_requested: Callable[[], bool] | None = None

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
    """按 phase DAG 拓扑序执行任务；human gate 前注册审批并进入 WAITING。"""
    outcomes: list[TaskOutcome] = []
    handoffs: dict[str, object] = {}
    specs = ctx.pending or ctx.resolve_sessions()
    groups = list(_phase_groups(specs))
    for index, group in enumerate(groups):
        paused = _pause_for_human_gate(deps, ctx, group, groups[index:], outcomes)
        if paused is not None:
            return paused
        held = _pause_if_requested(deps, ctx, groups[index:], outcomes)
        if held is not None:
            return held
        failure = _execute_phase_group(
            deps,
            ctx,
            group,
            _GroupRun(outcomes=outcomes, handoffs=handoffs, tail=groups[index + 1 :]),
        )
        if failure is not None:
            return failure
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


def _pause_if_requested(
    deps: PhaseRunnerDeps,
    ctx: PhaseContext,
    remaining: "list[tuple[SessionSpec, ...]]",
    outcomes: "list[TaskOutcome]",
) -> RunOutcome | None:
    """协作式暂停（PLAN-20260914-048）：组边界观测到暂停信号 → **零任务执行**
    返回 PAUSED，剩余 specs（含当前组）经 on_pause 交回 service 暂存。

    只读 canonical run state（service 注入谓词），不自己造暂停事实；
    已持租约的任务不受影响（不在本函数职责内撤销）。
    """
    if deps.pause_requested is None or not deps.pause_requested():
        return None
    if deps.on_pause is not None:
        deps.on_pause(tuple(spec for group in remaining for spec in group))
    return RunOutcome(
        run_id=ctx.run_id,
        state=ResearchRunState.State.PAUSED,
        message="paused at phase boundary (cooperative pause)",
        tasks=tuple(outcomes),
        manifest_digest=ctx.frozen_manifest_digest,
        system_failure=False,
    )


def _pause_for_human_gate(
    deps: PhaseRunnerDeps,
    ctx: PhaseContext,
    group: "tuple[SessionSpec, ...]",
    remaining: "list[tuple[SessionSpec, ...]]",
    outcomes: "list[TaskOutcome]",
) -> RunOutcome | None:
    """声明的 human gate：注册 ApprovalRecord + APPROVAL_REQUESTED 事件 +
    WAITING_FOR_APPROVAL outcome（剩余 specs 经 on_pause 交回 service 暂存）。
    没有 approvals store 时 service 不会给出 human_gated 集（fail-closed）。"""
    phase_id = group[0][2].phase_id
    if not phase_id or phase_id not in deps.human_gated or deps.approvals is None:
        return None
    approval = deps.approvals.register(
        ApprovalSpec(
            run_id=ctx.run_id,
            action=f"human-gate:{phase_id}",
            risk="HUMAN_GATE",
            context=phase_id,
            policy_source="protocol-gate",
            # requested_event_id 关联本应指向 approval.requested 事件，但发布在
            # register 之后且 publish 不回传 id；留空（审批记录本身即真相源）。
            requested_event_id="",
        )
    )
    deps.emit(
        EventType.APPROVAL_REQUESTED,
        {"run_id": ctx.run_id, "phase_id": phase_id, "approval_id": approval.id},
        ctx.run_id,
        ctx.trace_id,
        None,
    )
    if deps.on_pause is not None:
        deps.on_pause(tuple(spec for chunk in remaining for spec in chunk))
    return RunOutcome(
        run_id=ctx.run_id,
        state=ResearchRunState.State.WAITING_FOR_APPROVAL,
        message=f"awaiting human approval for phase {phase_id} (approval {approval.id})",
        tasks=tuple(outcomes),
        manifest_digest=ctx.frozen_manifest_digest,
    )


def _phase_groups(
    specs: tuple[SessionSpec, ...],
) -> "Iterator[tuple[SessionSpec, ...]]":
    """按连续相同 phase_id 分组(resolve_sessions 按 DAG 序产出,同 phase 连续)。"""
    index = 0
    while index < len(specs):
        phase_id = specs[index][2].phase_id
        end = index
        while end < len(specs) and specs[end][2].phase_id == phase_id:
            end += 1
        yield specs[index:end]
        index = end


@dataclass(slots=True)
class _GroupRun:
    """一个 phase 组的执行现场：累积结果 + 本组之后的剩余组（参数对象）。

    `_execute_phase_group` / `_park_for_retry` 需要同时拿到"已经成功的任务""本组
    之后的 specs""handoff 累积"，逐个当参数传会撞上 5 参数上限——收敛成一个现场对象。
    """

    outcomes: list[TaskOutcome]
    handoffs: dict[str, object]
    tail: list[tuple[SessionSpec, ...]]


def _execute_phase_group(
    deps: PhaseRunnerDeps,
    ctx: PhaseContext,
    group: tuple[SessionSpec, ...],
    run: _GroupRun,
) -> RunOutcome | None:
    """执行一个 phase 分组(外包 PHASE span);返回失败 RunOutcome 或 None。

    M15 债务清偿:phase_id 为空(resume 重建路径)时不发 PHASE correlation,
    TASK 落回 RUN 父。
    """
    phase_id = group[0][2].phase_id
    phase_correlation = CorrelationRef(
        run_id=ctx.run_id,
        phase_run_id=phase_id if phase_id else None,
        trace_id=ctx.trace_id or None,
    )
    with operation(
        deps.telemetry,
        scope=OperationScope.PHASE,
        name="phase",
        correlation=phase_correlation,
    ) as phase_op:
        for position, (task, contract, spec_context) in enumerate(group):
            task_correlation = CorrelationRef(
                run_id=ctx.run_id,
                task_id=task.id.value,
                phase_run_id=phase_id if phase_id else None,
                trace_id=ctx.trace_id or None,
            )
            with operation(
                deps.telemetry,
                scope=OperationScope.TASK,
                name="task",
                correlation=task_correlation,
            ):
                step = _execute_one_task(
                    deps,
                    TaskContext(task=task, contract=contract, spec_context=spec_context, ctx=ctx),
                )
            if step.retry_deferred:
                return _park_for_retry(deps, ctx, group, position, run)
            if step.failure is not None:
                phase_op.set_outcome(OperationOutcome.FAILED, "task_failed")
                return step.failure  # type: ignore[no-any-return]
            run.handoffs[task.id.value] = step.handoff
            run.outcomes.append(TaskOutcome(task=task, outcome="SUCCEEDED", verdict=step.verdict))
    return None


def _park_for_retry(
    deps: PhaseRunnerDeps,
    ctx: PhaseContext,
    group: tuple[SessionSpec, ...],
    position: int,
    run: _GroupRun,
) -> RunOutcome:
    """把"重排还没到期"的 run 停在 PAUSED，而不是判失败（PLAN-20260915-081）。

    失败的那个任务与它后面的所有 specs 一起交回 service 暂存供 resume 续跑。
    为什么不能判失败：run 的 FAILED 是**终态**（`FAILED --RESUME-->` 不在迁移表里），
    一旦落 FAILED，durable 侧那条 `RETRY_SCHEDULED`（带 `retry_at`）就再没有派发方
    会来取——声明了退避的重排会变成孤儿（RECHECK-20260915-080 W-1）。
    """
    if deps.on_pause is not None:
        deps.on_pause(tuple(group[position:]) + tuple(spec for chunk in run.tail for spec in chunk))
    return RunOutcome(
        run_id=ctx.run_id,
        state=ResearchRunState.State.PAUSED,
        message=(
            f"task {group[position][0].id.value} retry scheduled; run parked until the retry is due"
        ),
        tasks=tuple(run.outcomes),
        manifest_digest=ctx.frozen_manifest_digest,
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
            # budget 必须接进来:失败/重试路径的 attempt 记账在
            # `record_attempt_usage` 里以 `budget is None` 提前返回,原先这里
            # 漏传导致生产 run 的失败尝试**从不落账**——"失败消耗不丢失"无从成立
            # (M15 复审 BLOCKER-5 的第二半)。
            ExecutionDeps(deps.workflow, deps.runtime, budget=deps.budget),
            task,
            tctx.contract,
            tctx.spec_context,
            trace_id=tctx.ctx.trace_id,
        )
    if not execution.succeeded:
        if execution.retry_deferred:
            # 不是终局失败：durable 侧已经排了下一次尝试（带 deadline），由派发方
            # 再来取。这里不 fail run——FAILED 是终态，会把那条重排变成孤儿。
            return PhaseStep(retry_deferred=True)
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
