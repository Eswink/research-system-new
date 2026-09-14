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
from packages.application.run_orchestration.phase_runner import (
    PhaseContext,
    PhaseRunnerDeps,
    RunOutcome,
    TaskOutcome,
    execute_phases,
)
from packages.application.run_orchestration.session_resolution import resolve_sessions
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.application.run_orchestration.usage_recording import record_cancelled_usage
from packages.domain.enums import GateType
from packages.domain.events import EventType
from packages.domain.manifest import RunManifest
from packages.domain.protocols import ProtocolDefinition
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
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
            id=command.run_id, project_id=command.project_id, protocol_id=command.protocol_id
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
        if str(context.run.manifest_digest or "") != command.frozen_manifest_digest:
            raise ManifestFreezeError("resume manifest digest does not match frozen snapshot")
        if context.run.state != ResearchRunState.State.PAUSED:
            raise ValueError(f"cannot resume run in state {context.run.state}")
        assert_semantics_frozen(
            context,
            pricing_version=context.run.pricing_version,
            pricing_digest=context.run.pricing_digest,
        )
        resumed = context.run.transition(ResearchRunState.Transition.RESUME)
        context = replace(context, run=resumed)
        return self._execute_with_context(context, None, pending=pending)

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
        outcome = execute_phases(
            PhaseRunnerDeps(
                workflow=self._deps.workflow,
                runtime=self._deps.runtime,
                artifacts=self._deps.artifacts,
                budget=self._deps.budget,
                ledger=self._deps.ledger,
                publish=self._publish_phase_event,
                fail_run=self._fail_run,
                telemetry=self._deps.telemetry,
                approvals=self._deps.approvals,
                human_gated=self._pending_human_gates(context),
                on_pause=paused.append,
            ),
            PhaseContext(
                command=command,
                resolve_sessions=lambda: self._resolve_sessions(context),
                frozen_manifest_digest=context.frozen_manifest_digest,
                trace_id=context.trace_id,
                run_id=context.run.id.value,
                pending=pending,
            ),
        )
        if outcome.state == ResearchRunState.State.WAITING_FOR_APPROVAL and paused:
            self._waiting[context.run.id.value] = (context, paused[0])
        return outcome

    def _pending_human_gates(self, context: RunContext) -> frozenset[str]:
        """声明的 HUMAN_GATE phase − 本 run 已裁决审批（无 store 则不暂停）。"""
        approvals = self._deps.approvals
        if approvals is None:
            return frozenset()
        declared = {
            gate.phase_id for gate in context.plan.gates if gate.gate is GateType.HUMAN_GATE
        }
        decided = {
            approval.context
            for approval in approvals.list_for_run(context.run.id.value)
            if approval.status != "PENDING"
        }
        return frozenset(declared - decided)

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
        self._publish(
            EventType.RUN_FAILED,
            {"run_id": run_id, "message": message},
            run_id=run_id,
            trace_id="",
        )
        return RunOutcome(
            run_id=run_id,
            state=ResearchRunState.State.FAILED,
            message=message,
            system_failure=system_failure,
        )

    def _release_if_terminal(self, run_id: str, state: str) -> None:
        if state in ResearchRunState.terminal():
            release_reservation(self._reservation_refs, self._deps.budget, run_id)

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
