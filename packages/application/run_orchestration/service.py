"""RunOrchestrationService：Compile → Preflight → Freeze → Execute → Complete。

把 M2（compile/preflight/freeze）、M4（team resolution）、M6（AgentRuntime）、
M5（WorkflowEngine/ArtifactStore/EventPublisher）与领域产物链串成端到端
ResearchRun 执行。Preflight 不可绕过（ManifestFreezeError 阻断）；RunManifest
在执行前冻结，resume/retry 基于冻结 snapshot；OpenHands Conversation 状态
不替代 ResearchRun 状态（AGENTS.md §6）。执行循环见 phase_runner；
resume 语义守卫与预算释放见 convergence；team resolution 辅助见
session_resolution。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from packages.application.observability.scope import operation
from packages.application.observability.signals import (
    CorrelationRef,
    OperationOutcome,
    OperationScope,
)
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.resource_catalog import (
    CatalogSnapshot,
    PreflightContext,
    ProjectSettings,
)
from packages.application.preflight.preflight import (
    ManifestFreezeError,
    PricingFreeze,
    compile_and_preflight,
    freeze_manifest,
)
from packages.application.run_orchestration.commands import (
    CancelRunCommand,
    ResumeRunCommand,
    StartRunCommand,
)
from packages.application.run_orchestration.context import RunContext
from packages.application.run_orchestration.convergence import (
    assert_semantics_frozen,
    release_reservation,
)
from packages.application.run_orchestration.dependencies import OrchestrationDependencies
from packages.application.run_orchestration.eventing import (
    EventSink,
    EventTarget,
    frozen_payload,
    publish_event,
)
from packages.application.run_orchestration.human_gates import pending_human_gates
from packages.application.run_orchestration.outcomes import RunOutcome, TaskOutcome
from packages.application.run_orchestration.phase_runner import (
    PhaseContext,
    PhaseRunnerDeps,
    execute_phases,
)
from packages.application.run_orchestration.run_terminals import (
    compensate_failed_resume,
    publish_degraded_run,
    publish_failed_run,
)
from packages.application.run_orchestration.session_resolution import resolve_sessions
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.application.run_orchestration.usage_recording import record_cancelled_usage
from packages.domain.core import ID
from packages.domain.events import EventType
from packages.domain.manifest import RunManifest
from packages.domain.protocols import ProtocolDefinition
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import ResearchTask, TaskContract

SessionSpec = tuple[ResearchTask, TaskContract, SessionSpecContext]


def _preflight_failure_message(report: Any) -> str:
    """PA-1 F5: carry failing check codes so an unprovisioned control plane
    is actionable (which check failed) instead of a bare "preflight failed".
    Honest FAILED semantics unchanged."""
    codes = ", ".join(sorted({finding.code for finding in report.findings}))
    return f"preflight failed: {codes}" if codes else "preflight failed"


class RunOrchestrationService:
    """端到端 ResearchRun 编排 Use Case。"""

    def __init__(self, deps: OrchestrationDependencies) -> None:
        self._deps = deps
        self._event_sink = EventSink(deps.events, deps.default_actor)
        # run_id → reservation_ref：进程内记账（M7 同步边界内 run 收敛时释放预算）。
        self._reservation_refs: dict[str, str] = {}
        # WP-H：human gate 暂停暂存（run_id → 上下文与剩余 specs）。in-process 面：
        # 重启后丢失，decide 端点据此诚实 503，绝不伪装恢复了执行。
        self._waiting: dict[str, tuple[RunContext, tuple[SessionSpec, ...]]] = {}
        # PLAN-048：协作式暂停暂存（run_id → 上下文与剩余 specs）。同样是进程内
        # 面：没有它时 resume 只解除暂停（派发恢复），不伪造"继续执行"。
        self._paused: dict[str, tuple[RunContext, tuple[SessionSpec, ...]]] = {}

    def start_run(
        self,
        protocol: ProtocolDefinition,
        catalog: CatalogSnapshot,
        project: ProjectSettings,
        preflight_context: PreflightContext,
        command: StartRunCommand,
    ) -> RunOutcome:
        """执行整条链路；任何阶段失败都收敛到确定的 Run 终态。"""
        with operation(
            self._deps.telemetry,
            scope=OperationScope.RUN,
            name="run",
            correlation=CorrelationRef(
                project_id=command.project_id,
                run_id=command.run_id.value,
                trace_id=command.trace_id,
            ),
        ) as op:
            outcome = self._start_run_impl(protocol, catalog, project, preflight_context, command)
            if outcome.state == ResearchRunState.State.FAILED:
                op.set_outcome(OperationOutcome.FAILED, "run_failed")
            return outcome

    def _start_run_impl(
        self,
        protocol: ProtocolDefinition,
        catalog: CatalogSnapshot,
        project: ProjectSettings,
        preflight_context: PreflightContext,
        command: StartRunCommand,
    ) -> RunOutcome:
        # 懒触发 lease 恢复：上次进程崩溃遗留的过期 lease 先收敛再调度新 run。
        self._deps.workflow.recover_expired_leases()
        run = ResearchRun(
            id=command.run_id,
            project_id=command.project_id,
            protocol_id=command.protocol_id,
            protocol_source=command.protocol_source,
            protocol_body=command.protocol_body,
        )
        run = run.transition(ResearchRunState.Transition.START_COMPILE)
        plan, report = compile_and_preflight(protocol, catalog, project, preflight_context)
        if plan is None or report.status.value == "FAIL":
            return self._fail_run(run.id.value, _preflight_failure_message(report), False)
        run = run.transition(ResearchRunState.Transition.COMPILE_OK)
        run = run.transition(ResearchRunState.Transition.PREFLIGHT_OK)
        manifest = freeze_manifest(
            run.id.value,
            plan,
            report,
            preflight_context,
            pricing_freeze=PricingFreeze(table=self._deps.pricing, store=self._deps.pricing_store),
        )
        run = self._started_run(run, manifest)
        if manifest.budget_reservation_ref is not None:
            self._reservation_refs[run.id.value] = manifest.budget_reservation_ref
        self._publish(
            EventType.MANIFEST_FROZEN,
            frozen_payload(run, manifest),
            run_id=run.id.value,
            trace_id=command.trace_id,
        )
        context = RunContext(
            protocol=protocol,
            plan=plan,
            report=report,
            run=run,
            catalog=catalog,
            project=project,
            preflight=preflight_context,
            trace_id=command.trace_id,
        )
        return self._execute_with_context(context, command)

    def _started_run(self, run: ResearchRun, manifest: RunManifest) -> ResearchRun:
        """回填冻结引用并进入 START（逐字段保留定价引用，见 ResearchRun）。"""
        return run.with_manifest(
            manifest.digest(),
            manifest.semantic_digest(),
            pricing_version=manifest.pricing_version,
            pricing_digest=manifest.pricing_digest,
        ).transition(ResearchRunState.Transition.START)

    def cancel_run(self, command: CancelRunCommand) -> None:
        """协作式取消并按 canonical task 归属记录不可计量用量。"""
        run_id = command.run_id.value
        self._deps.workflow.cancel_run(run_id)
        record_cancelled_usage(
            self._deps.budget,
            run_id,
            self._deps.workflow.cancelled_task_ids(run_id),
        )
        release_reservation(self._reservation_refs, self._deps.budget, run_id)

    def resume_run(
        self,
        context: RunContext,
        command: ResumeRunCommand,
        pending: tuple[SessionSpec, ...],
    ) -> RunOutcome:
        """恢复：以冻结 manifest 语义继续剩余任务（mismatch 拒绝）。"""
        self._assert_resumable(context, command)
        if context.run.state != ResearchRunState.State.PAUSED:
            raise ValueError(f"cannot resume run in state {context.run.state}")
        resumed = context.run.transition(ResearchRunState.Transition.RESUME)
        context = replace(context, run=resumed)
        return self._execute_with_context(context, None, pending=pending)

    def resume_rebuilt(self, context: RunContext, command: ResumeRunCommand) -> RunOutcome:
        """重启后的续跑：上下文由调用方按 durable 事实重建（GOAL-003 cycle 20）。

        与 `resume_run` 的差别只有一处：canonical 状态迁移**已由控制面完成**并落库
        （先迁 `PAUSED → RUNNING` 再续跑——协作式暂停谓词读的就是 canonical 状态，
        顺序反了续跑会被自己的暂停谓词挡住，cycle 19 的教训）。剩余工作由本服务按
        canonical 任务重算：specs 每次解析都会生成新的 task id，只有 idempotency key
        是稳定身份，所以"已成功的任务不重跑"只能按 key 对齐。

        冻结语义校验与 `resume_run` 完全同一套（digest + 语义 digest），不做任何放宽。
        """
        self._assert_resumable(context, command)
        if context.run.state != ResearchRunState.State.RUNNING:
            raise ValueError(f"cannot continue a rebuilt resume in state {context.run.state}")
        return self._execute_with_context(context, None, pending=self._remaining_specs(context))

    def _assert_resumable(self, context: RunContext, command: ResumeRunCommand) -> None:
        """resume 前置断言：冻结 digest 一致 + 语义未漂移（两个入口共用）。"""
        if str(context.run.manifest_digest or "") != command.frozen_manifest_digest:
            raise ManifestFreezeError("resume manifest digest does not match frozen snapshot")
        assert_semantics_frozen(
            context,
            pricing_version=context.run.pricing_version,
            pricing_digest=context.run.pricing_digest,
        )

    def _remaining_specs(self, context: RunContext) -> tuple[SessionSpec, ...]:
        """重算剩余工作（按 idempotency key 对齐 canonical 任务）。

        两条规则缺一不可：

        - 已 `SUCCEEDED` 的任务**不重跑**（重建出来的 specs 是全量的，不是断点）；
        - 未成功的任务必须换成 **canonical task id**——`resolve_sessions` 每次解析都
          生成新 id，而引擎按 idempotency key 去重，拿新 id 去 acquire 只会得到
          "这个任务不存在"（替身/持久化 adapter 同判据）。
        """
        identities = {
            item.idempotency_key: item
            for item in self._deps.workflow.task_identities(context.run.id.value)
        }
        remaining: list[SessionSpec] = []
        for task, contract, spec_context in self._resolve_sessions(context):
            identity = identities.get(task.idempotency_key or "")
            if identity is None:
                remaining.append((task, contract, spec_context))
                continue
            if identity.status == ResearchTaskState.State.SUCCEEDED:
                continue
            remaining.append((replace(task, id=ID(identity.task_id)), contract, spec_context))
        return tuple(remaining)

    def _execute_with_context(
        self,
        context: RunContext,
        command: StartRunCommand | None,
        *,
        pending: tuple[SessionSpec, ...] = (),
    ) -> RunOutcome:
        outcome = self._execute(context, command, pending=pending)
        outcome = replace(
            outcome,
            pricing_version=context.run.pricing_version,
            pricing_digest=context.run.pricing_digest,
            manifest_semantic_digest=(
                str(context.run.manifest_semantic_digest)
                if context.run.manifest_semantic_digest is not None
                else None
            ),
        )
        self._release_if_terminal(context.run.id.value, outcome.state)
        return outcome

    def _execute(
        self,
        context: RunContext,
        command: StartRunCommand | None,
        *,
        pending: tuple[SessionSpec, ...] = (),
    ) -> RunOutcome:
        """委托 phase_runner 执行；service 负责事件发布、失败收敛与 human-gate 暂存。"""
        paused: list[tuple[SessionSpec, ...]] = []
        run_id = context.run.id.value
        outcome = execute_phases(
            PhaseRunnerDeps(
                workflow=self._deps.workflow,
                runtime=self._deps.runtime,
                artifacts=self._deps.artifacts,
                budget=self._deps.budget,
                ledger=self._deps.ledger,
                publish=self._publish_phase_event,
                fail_run=self._fail_run,
                degrade_run=self._degrade_run,
                telemetry=self._deps.telemetry,
                approvals=self._deps.approvals,
                human_gated=pending_human_gates(self._deps.approvals, context.plan, run_id),
                on_pause=paused.append,
                pause_requested=lambda: self.pause_requested(run_id),
            ),
            PhaseContext(
                command=command,
                resolve_sessions=lambda: self._resolve_sessions(context),
                frozen_manifest_digest=context.frozen_manifest_digest,
                trace_id=context.trace_id,
                run_id=run_id,
                pending=pending,
            ),
        )
        if outcome.state == ResearchRunState.State.WAITING_FOR_APPROVAL and paused:
            self._waiting[run_id] = (context, paused[0])
        elif outcome.state == ResearchRunState.State.PAUSED and paused:
            self._paused[run_id] = (context, paused[0])
        return outcome

    def pause_requested(self, run_id: str) -> bool:
        """协作式暂停谓词：读 canonical run state（派发/执行面唯一暂停事实）。

        未知 run（行尚未落库，如首次执行的起始阶段）→ False：暂停必须先被
        控制面持久化才会被观测到，不靠进程内标志推断。
        """
        return bool(self._deps.workflow.run_state(run_id) == ResearchRunState.State.PAUSED)

    def has_paused_context(self, run_id: str) -> bool:
        """resume 前置探测：无暂存暂停上下文（如进程重启后）不得伪装继续执行。"""
        return run_id in self._paused

    def resume_paused(self, run_id: str, run: ResearchRun) -> RunOutcome:
        """续跑协作式暂停：以控制面已迁移的 canonical run 继续剩余 specs。

        无暂停上下文 → InvalidInputError（调用方据此诚实降级为"只解除暂停"）。

        GOAL-004 cycle 7（EC-06）：执行阶段的**失败**会把上下文留在 pop 之后（不复活），
        调用方必须据 `compensate_failed_resume` 把 canonical 放回停车——不在悬空 RUNNING
        上等一个永远不会来的续跑。
        """
        stashed = self._paused.pop(run_id, None)
        if stashed is None:
            raise InvalidInputError(f"no paused execution context for run {run_id}")
        context, pending = stashed
        return self._execute_with_context(replace(context, run=run), None, pending=pending)

    def compensate_failed_resume(self, run: ResearchRun, failure: BaseException) -> ResearchRun:
        """续跑失败 ⇒ canonical 放回 `PAUSED` 并记原因（GOAL-004 cycle 7 = EC-06）。

        迁移与发事件的动作在 `run_terminals`（450 行上限）；调用方负责把返回的 run 落库。
        两条入口（API `POST /resume` 与守护线程 `_resume`）共用这一处补偿。
        """
        compensated: ResearchRun = compensate_failed_resume(self._publish, run, failure)
        return compensated

    def has_waiting_context(self, run_id: str) -> bool:
        """approve 前置探测：无暂存上下文（如进程重启后）不得伪装恢复执行。"""
        return run_id in self._waiting

    def reservation_ref(self, run_id: str) -> str | None:
        """run 的预算预留引用（budget_adjust 干预的 release 输入）。

        进程内记账：本进程启动的 run 才有；None 表示无预留或跨进程重启丢失。
        """
        return self._reservation_refs.get(run_id)

    def register_reservation_ref(self, run_id: str, ref: str) -> None:
        """budget_adjust 后登记新预留引用（后续收敛释放指向新额度）。"""
        self._reservation_refs[run_id] = ref

    def resume_after_approval(self, run_id: str) -> RunOutcome:
        """审批通过后续跑剩余 specs；再次遇 human gate 会重新暂存 WAITING。"""
        stashed = self._waiting.pop(run_id, None)
        if stashed is None:
            raise InvalidInputError(f"no waiting execution context for run {run_id}")
        context, remaining = stashed
        return self._execute_with_context(context, None, pending=remaining)

    def _resolve_sessions(self, context: RunContext) -> tuple[SessionSpec, ...]:
        """M4 team resolution：phase assignments → ResearchTask + session spec。"""
        return resolve_sessions(context, contract_for=self._contract_for)

    def _contract_for(self, context: RunContext, refs: tuple[str, ...]) -> TaskContract:
        if not refs:
            raise ValueError("phase declares no task contract")
        contract = context.catalog.task_contracts.get(refs[0])
        if contract is None:
            raise ValueError(f"task contract {refs[0]} is unavailable")
        return contract

    def _fail_run(self, run_id: str, message: str, system_failure: bool) -> RunOutcome:
        release_reservation(self._reservation_refs, self._deps.budget, run_id)
        return publish_failed_run(self._publish, run_id, message, system_failure)

    def _release_if_terminal(self, run_id: str, state: str) -> None:
        if state in ResearchRunState.terminal():
            release_reservation(self._reservation_refs, self._deps.budget, run_id)

    def _degrade_run(
        self,
        ctx: Any,
        tolerated: tuple[Any, ...],
        message: str,
    ) -> RunOutcome:
        """被容忍的失败 ⇒ `run.degraded`（GOAL-004 cycle 3 = EC-03）。

        发事件的动作在 `run_terminals`（450 行上限拆出）；这里只接线。
        """
        return publish_degraded_run(self._publish, ctx, tolerated, message)

    def _publish_phase_event(
        self,
        event_type: EventType,
        payload: dict[str, object],
        run_id: str,
        trace_id: str,
        task_id: str | None,
    ) -> None:
        self._publish(event_type, payload, run_id=run_id, trace_id=trace_id, task_id=task_id)

    def _publish(
        self,
        event_type: EventType,
        payload: dict[str, object],
        *,
        run_id: str,
        trace_id: str,
        task_id: str | None = None,
    ) -> None:
        publish_event(
            self._event_sink,
            event_type,
            payload,
            EventTarget(run_id=run_id, trace_id=trace_id, task_id=task_id),
        )


__all__ = [
    "OrchestrationDependencies",
    "RunOrchestrationService",
    "RunOutcome",
    "SessionSpec",
    "TaskOutcome",
]
