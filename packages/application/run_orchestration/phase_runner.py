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
from packages.application.model_relay.observation import RunSessionObservation, observe_session
from packages.application.observability.scope import operation
from packages.application.observability.signals import (
    CorrelationRef,
    OperationOutcome,
    OperationScope,
)
from packages.application.ports.agent_runtime import AgentRuntime
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.application.ports.workflow_engine import WorkflowEngine
from packages.application.run_orchestration.commands import StartRunCommand
from packages.application.run_orchestration.outcomes import RunOutcome, TaskOutcome, handoff_digests
from packages.application.run_orchestration.phase_capabilities import execute_run_chain_capabilities
from packages.application.run_orchestration.phase_pause import (
    pause_for_human_gate,
    pause_if_requested,
)
from packages.application.run_orchestration.prior_knowledge import with_prior_knowledge
from packages.application.run_orchestration.report_task import register_and_gate_report
from packages.application.run_orchestration.retrieval_context import with_retrieval_context
from packages.application.run_orchestration.round_loop_runner import execute_rounds
from packages.application.run_orchestration.run_completion_payload import (
    run_completion_payload,
)
from packages.application.run_orchestration.session_carry import (
    SessionCarryInputs,
)
from packages.application.run_orchestration.session_carry import (
    build_session_carry as session_carry,
)
from packages.application.run_orchestration.task_dispatch import dispatch_task_execution
from packages.application.run_orchestration.task_executor import (
    SessionSpecContext,
    TaskExecutionResult,
)
from packages.application.run_orchestration.task_phase_helpers import (
    PhaseStep,
    failure_or_deferred,
    failure_step,
    register_and_gate,
    register_and_gate_experiment,
    tolerated_outcome,
)
from packages.domain.events import EventType
from packages.domain.failure_policy import OnTaskFailure
from packages.domain.run_state import ResearchRunState
from packages.domain.tasks import ResearchTask, TaskContract

SessionSpec = tuple[ResearchTask, TaskContract, SessionSpecContext]


@dataclass(frozen=True, slots=True)
class PhaseRunnerDeps:
    """执行循环的 Port 组合与发布/失败回调（由 service 注入）。"""

    workflow: WorkflowEngine
    runtime: AgentRuntime
    artifacts: ArtifactStore
    budget: BudgetLedger | None = None
    ledger: EvidenceLedger | None = None
    # GOAL-20261008-035 EC-01：验收门求值结论的落库面（None ⇒ 读面读不到；生产根总是接上）。
    review_findings: Any | None = None
    # GOAL-20261008-038 EC-04：跨轮消费的前序结论读取器（`(run_id) -> (结论, run_id)`）。
    prior_conclusion: Any | None = None
    experiment_task: (
        Callable[[ResearchTask, TaskContract, SessionSpecContext, str], TaskExecutionResult] | None
    ) = None
    #: GOAL-20261014-077 EC-02：**报告汇编**阶段的执行缝（与 `experiment_task` 同型同层）。
    #: None（缺省）= 没接。此时契约里**声明了** `report` 的任务以**点名拒绝**收敛
    #: （fail-closed，不静默回退到会话 —— 否则「声明了汇编」与「真的汇编了」会分叉）。
    report_task: (
        Callable[[ResearchTask, TaskContract, SessionSpecContext, str], TaskExecutionResult] | None
    ) = None
    #: GOAL-20261014-078 EC-01：检索内容 → 会话上下文的装配器（每任务求值；
    #: 理由与实现见 `retrieval_context.py`）。None ⇒ 不带检索上下文（逐字节不变）。
    retrieval_context: Callable[[str], Any] | None = None
    #: GOAL-20261018-082 EC-01：前序知识 → 提示词的装配器（与检索同一求值点；None ⇒ 无该段）。
    prior_knowledge: Callable[[str], Any] | None = None
    output_schema_validator: Any | None = None
    memory_gate: MemoryGateDeps | None = None
    publish: Callable[[EventType, dict[str, object], str, str, str | None], None] | None = None
    fail_run: Callable[[str, str, bool], RunOutcome] | None = None
    # GOAL-004 cycle 3（EC-03）：被容忍的失败收敛到 DEGRADED 的发布回调（service 注入；
    # 未注入时 `degrade` 仍返回正确的 RunOutcome，只是不发 `run.degraded`）。
    degrade_run: Callable[[PhaseContext, tuple[TaskOutcome, ...], str], RunOutcome] | None = None
    telemetry: TelemetrySink | None = None
    # GOAL-011 EC-01：运行链能力步装配面（CapabilityDeps；None ⇒ 该步不启用）。
    capabilities: Any | None = None
    # WP-H：human gate 注册面。approvals 与 human_gated 同源注入（service 仅在
    # store 存在时给出非空 gate 集）；on_pause 把未执行 specs 交回 service 暂存。
    approvals: Any | None = None
    human_gated: frozenset[str] = frozenset()
    on_pause: Callable[[tuple[SessionSpec, ...]], None] | None = None
    # PLAN-048：协作式暂停信号（读 canonical run state）；剩余 specs 经 on_pause 暂存。
    pause_requested: Callable[[], bool] | None = None
    # GOAL-010 EC-04：会话期观测交回方（只在**真有观测**时调用——不发空事实）。
    on_observation: Callable[[RunSessionObservation], None] | None = None
    # GOAL-20261008-034 EC-01：**多轮循环**的驱动面（service 注入；None ⇒ 单遍语义
    # 逐字节不变）：`next_round()` / `resolve(round_index)`（懒展开，该轮的 specs）/ `record(...)`。
    round_driver: Any | None = None
    #: 单遍执行的**原始** specs 解析器（无循环时用它；有循环时由驱动按轮调用）。
    resolve_round: Callable[[int], tuple["SessionSpec", ...]] | None = None

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

    def degrade(
        self,
        ctx: PhaseContext,
        tolerated: tuple[TaskOutcome, ...],
        handoffs: dict[str, object],
    ) -> RunOutcome:
        """跑完全部剩余工作、但有被容忍的失败 ⇒ 收敛 `DEGRADED`（EC-03）。

        DEGRADED 是**非终态**："工作做完了，但有几条任务失败且契约声明容忍"——不冒充
        `SUCCEEDED`，也不把整条 run 判成 `FAILED`（那正是 `CONTINUE` 要避免的）。
        """
        message = (
            f"run completed with {len(tolerated)} tolerated failure(s) "
            f"under failure_policy on_task_failure={OnTaskFailure.CONTINUE}"
        )
        if self.degrade_run is not None:
            return self.degrade_run(ctx, tolerated, message)
        return RunOutcome(
            run_id=ctx.run_id,
            state=ResearchRunState.State.DEGRADED,
            message=message,
            tasks=(*tolerated,),
            manifest_digest=ctx.frozen_manifest_digest,
            handoff_digests=handoff_digests(handoffs),
            system_failure=False,
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
    """按 phase DAG 拓扑序执行任务；human gate 前注册审批并进入 WAITING。

    **多轮循环**：注入 `round_driver` 时按轮重复执行（循环控制在
    `round_loop_runner.execute_rounds`，本模块只暴露**单遍执行**这一原语）；
    无注入路径逐字节不变。
    """
    if deps.round_driver is not None and deps.resolve_round is not None:
        outcome: RunOutcome = execute_rounds(deps, ctx)
        return outcome
    return _execute_one_pass(deps, ctx, ctx.pending or ctx.resolve_sessions())


def _execute_one_pass(
    deps: PhaseRunnerDeps,
    ctx: PhaseContext,
    specs: tuple["SessionSpec", ...],
) -> RunOutcome:
    """**单遍**执行（循环体的原样搬迁；既有调用方语义与载荷逐字节不变）。"""
    outcomes: list[TaskOutcome] = []
    handoffs: dict[str, object] = {}
    groups = list(_phase_groups(specs))
    for index, group in enumerate(groups):
        paused = pause_for_human_gate(deps, ctx, group, groups[index:], outcomes)
        if paused is not None:
            return paused
        held = pause_if_requested(deps, ctx, groups[index:], outcomes)
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
    tolerating = tuple(outcome for outcome in outcomes if outcome.failure_policy is not None)
    if tolerating:
        return deps.degrade(ctx, tolerating, handoffs)
    # 载荷由**唯一构造点**给出（GOAL-20261009-042 EC-03 抽出：跳过与标注两条通道
    # 只此一份字段清单；此处与 `round_loop_runner` 不再各写一份）。缺省不带键
    # ⇒ 既有 payload 逐字节不变。
    payload = run_completion_payload(ctx.run_id, outcomes)
    deps.emit(EventType.RUN_COMPLETED, payload, ctx.run_id, ctx.trace_id, None)
    return RunOutcome(
        run_id=ctx.run_id,
        state=ResearchRunState.State.SUCCEEDED,
        chain_outputs=tuple(item for outcome in outcomes for item in outcome.chain_outputs),
        message="run completed",
        tasks=tuple(outcomes),
        manifest_digest=ctx.frozen_manifest_digest,
        handoff_digests=handoff_digests(handoffs),
        system_failure=False,
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
        frame = _GroupFrame(deps=deps, ctx=ctx, phase_id=phase_id, phase_op=phase_op)
        for position in range(len(group)):
            outcome = _run_group_task(frame, group, position, run)
            if outcome is not None:
                return outcome
    return None


@dataclass(frozen=True, slots=True)
class _GroupFrame:
    """组内执行现场（避免参数爆发）：依赖、上下文、phase 身份与 span。"""

    deps: PhaseRunnerDeps
    ctx: PhaseContext
    phase_id: str
    phase_op: Any


def _dispatch_task_execution(deps: PhaseRunnerDeps, tctx: TaskContext) -> TaskExecutionResult:
    """「谁执行这件工作」的派发（实现见 `task_dispatch.py`；本行只委派）。

    单列的理由与 GOAL-011 EC-03 拆 `experiment_task` 同源：本模块卡在 **450 行硬上限**上 ——
    GOAL-20261014-078 的检索上下文接缝同样因此**不在这里写实现**（见
    `retrieval_context.with_retrieval_context`）。
    """
    return dispatch_task_execution(deps, tctx)


def _task_correlation(ctx: PhaseContext, task: ResearchTask, phase_id: str) -> CorrelationRef:
    """本任务的观测 correlation（单列以守住函数长度门）。"""
    return CorrelationRef(
        run_id=ctx.run_id,
        task_id=task.id.value,
        phase_run_id=phase_id if phase_id else None,
        trace_id=ctx.trace_id or None,
    )


def _run_group_task(
    frame: _GroupFrame,
    group: tuple[SessionSpec, ...],
    position: int,
    run: _GroupRun,
) -> RunOutcome | None:
    """组内一个任务：跑 TASK span → 按步骤结果决定"继续 / 停车 / 失败"。

    返回值非 None = 该组到此为止（停车或失败）；None = 继续下一个任务。
    """
    deps, ctx, phase_id = frame.deps, frame.ctx, frame.phase_id
    task, contract, spec_context = group[position]
    # GOAL-20261014-078 EC-01：此刻已取回的检索内容 → 本任务的会话上下文（求值点说明
    # 见 `retrieval_context.with_retrieval_context`）。
    spec_context = with_retrieval_context(deps, task, spec_context)
    # GOAL-20261018-082 EC-01：前序知识 → 同一 spec 的第二个槽位（与检索同一求值点）。
    spec_context = with_prior_knowledge(deps, task, spec_context)
    with operation(
        deps.telemetry,
        scope=OperationScope.TASK,
        name="task",
        correlation=_task_correlation(ctx, task, phase_id),
    ):
        step = _execute_one_task(
            deps,
            TaskContext(task=task, contract=contract, spec_context=spec_context, ctx=ctx),
        )
    if step.retry_deferred:
        return _park_for_retry(deps, ctx, group, position, run)
    if step.tolerated_failure is not None:
        # 契约声明了容忍（`on_task_failure: CONTINUE`）：失败记账后继续跑，
        # run 最后收敛 DEGRADED（见 execute_phases），不在这里假装成功。
        run.outcomes.append(tolerated_outcome(task, step.tolerated_failure))
        return None
    if step.failure is not None:
        frame.phase_op.set_outcome(OperationOutcome.FAILED, "task_failed")
        return step.failure  # type: ignore[no-any-return]
    run.handoffs[task.id.value] = step.handoff
    run.outcomes.append(
        TaskOutcome(
            task=task,
            outcome="SUCCEEDED",
            verdict=step.verdict,
            skipped=step.skipped,
            chain_outputs=step.chain_outputs,
            annotations=step.annotations,
        )
    )
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
    capability = execute_run_chain_capabilities(deps.capabilities, task, tctx.spec_context)
    if capability.failure_message is not None:
        return failure_step(deps, tctx, capability.failure_message, capability.system_failure)
    execution = _dispatch_task_execution(deps, tctx)
    observe_session(deps.on_observation, tctx.spec_context.endpoint, execution.session_result)
    if not execution.succeeded:
        return failure_or_deferred(deps, tctx, execution)
    if execution.experiment_outcome is not None:
        return register_and_gate_experiment(deps, tctx, execution)
    if execution.report_outcome is not None:
        return register_and_gate_report(deps, tctx, execution)
    assert execution.session_result is not None
    carry = session_carry(
        SessionCarryInputs(
            workflow=deps.workflow,
            artifacts=deps.artifacts,
            ledger=deps.ledger,
            task=tctx.task,
            declared=tctx.spec_context.cross_phase_inputs,
            capability=capability,
        )
    )
    if isinstance(carry, str):
        return failure_step(deps, tctx, carry, True)
    return register_and_gate(deps, tctx, execution.session_result, carry)
