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

import uuid
from dataclasses import dataclass, replace

from packages.application.ports.agent_runtime import AgentRuntime
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.ports.event_publisher import EventPublisher
from packages.application.ports.resource_catalog import (
    CatalogSnapshot,
    PreflightContext,
    ProjectSettings,
)
from packages.application.ports.workflow_engine import WorkflowEngine
from packages.application.preflight.preflight import (
    ManifestFreezeError,
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
from packages.application.run_orchestration.phase_runner import (
    PhaseContext,
    PhaseRunnerDeps,
    RunOutcome,
    TaskOutcome,
    execute_phases,
)
from packages.application.run_orchestration.session_resolution import (
    assigned_agents,
    flatten_tool_providers,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.core import ID, Timestamp
from packages.domain.events import EventEnvelope, EventType, digest_of_payload
from packages.domain.protocols import ProtocolDefinition
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from packages.domain.tasks import ResearchTask, TaskContract

SessionSpec = tuple[ResearchTask, TaskContract, SessionSpecContext]


@dataclass(frozen=True, slots=True)
class OrchestrationDependencies:
    """composition root：全部 Port 显式注入，不直接实例化 adapter。"""

    runtime: AgentRuntime
    workflow: WorkflowEngine
    artifacts: ArtifactStore
    events: EventPublisher
    budget: BudgetLedger | None = None
    default_actor: str = "system:orchestration"


class RunOrchestrationService:
    """端到端 ResearchRun 编排 Use Case。"""

    def __init__(self, deps: OrchestrationDependencies) -> None:
        self._deps = deps
        # run_id → reservation_ref：进程内记账（M7 同步边界内 run 收敛时释放预算；
        # 跨进程恢复依赖 BudgetLedger 的持久化实现，见 M7 恢复边界声明）。
        self._reservation_refs: dict[str, str] = {}

    def start_run(
        self,
        protocol: ProtocolDefinition,
        catalog: CatalogSnapshot,
        project: ProjectSettings,
        preflight_context: PreflightContext,
        command: StartRunCommand,
    ) -> RunOutcome:
        """执行整条链路；任何阶段失败都收敛到确定的 Run 终态。"""
        # 懒触发 lease 恢复：上次进程崩溃遗留的过期 lease 先收敛再调度新 run
        # （SqliteWorkflowEngine.recover_expired_leases；Fake 恒返回 0）。
        self._deps.workflow.recover_expired_leases()
        run = ResearchRun(
            id=command.run_id,
            project_id=command.project_id,
            protocol_id=command.protocol_id,
        )
        run = run.transition(ResearchRunState.Transition.START_COMPILE)
        plan, report = compile_and_preflight(protocol, catalog, project, preflight_context)
        if plan is None or report.status.value == "FAIL":
            return self._fail_run(run.id.value, "preflight failed", False)
        run = run.transition(ResearchRunState.Transition.COMPILE_OK)
        run = run.transition(ResearchRunState.Transition.PREFLIGHT_OK)
        manifest = freeze_manifest(run.id.value, plan, report, preflight_context)
        run = run.with_manifest(manifest.digest(), manifest.semantic_digest()).transition(
            ResearchRunState.Transition.START
        )
        if manifest.budget_reservation_ref is not None:
            self._reservation_refs[run.id.value] = manifest.budget_reservation_ref
        self._publish(
            EventType.MANIFEST_FROZEN,
            {"run_id": run.id.value, "digest": str(manifest.digest())},
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
        outcome = self._execute(context, command)
        self._release_if_terminal(run.id.value, outcome.state)
        return outcome

    def cancel_run(self, command: CancelRunCommand) -> None:
        """协作式取消信号：WorkflowEngine 移除 lease，事件落 outbox，释放预算预留。"""
        self._deps.workflow.cancel(command.run_id.value)
        self._release_reservation(command.run_id.value)

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
            context.run.id.value,
            context.run.manifest_semantic_digest,
            context.plan,
            context.report,
            context.preflight,
        )
        resumed = context.run.transition(ResearchRunState.Transition.RESUME)
        context = replace(context, run=resumed)
        outcome = self._execute(context, None, pending=pending)
        self._release_if_terminal(resumed.id.value, outcome.state)
        return outcome

    def _execute(
        self,
        context: RunContext,
        command: StartRunCommand | None,
        *,
        pending: tuple[SessionSpec, ...] = (),
    ) -> RunOutcome:
        """委托 phase_runner 执行；service 负责事件发布与失败收敛。"""
        return execute_phases(
            PhaseRunnerDeps(
                workflow=self._deps.workflow,
                runtime=self._deps.runtime,
                artifacts=self._deps.artifacts,
                budget=self._deps.budget,
                publish=self._publish_phase_event,
                fail_run=self._fail_run,
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

    def _resolve_sessions(self, context: RunContext) -> tuple[SessionSpec, ...]:
        """M4 team resolution：phase assignments → ResearchTask + session spec。"""
        resolved: list[SessionSpec] = []
        assignments = {item.phase_id: item for item in context.plan.phase_assignments}
        for phase in context.plan.phases:
            assignment = assignments.get(phase.id)
            if assignment is None:
                continue
            for agent_id in assigned_agents(assignment):
                agent = context.catalog.agents[agent_id]
                role = context.catalog.roles[agent.role]
                contract = self._contract_for(context, phase.task_contract_refs)
                task = ResearchTask(
                    id=ID.generate(),
                    run_id=context.run.id,
                    contract_id=contract.id,
                    assigned_agent_id=agent_id,
                    status="CREATED",
                    idempotency_key=f"{context.run.id.value}:{phase.id}:{agent_id}",
                )
                resolved.append((
                    task,
                    contract,
                    SessionSpecContext(
                        role=role,
                        agent=agent,
                        frozen_manifest_digest=context.frozen_manifest_digest,
                        frozen_tool_set=flatten_tool_providers(context.plan),
                    ),
                ))
        return tuple(resolved)

    def _contract_for(self, context: RunContext, refs: tuple[str, ...]) -> TaskContract:
        if not refs:
            raise ValueError("phase declares no task contract")
        contract = context.catalog.task_contracts.get(refs[0])
        if contract is None:
            raise ValueError(f"task contract {refs[0]} is unavailable")
        return contract

    def _fail_run(self, run_id: str, message: str, system_failure: bool) -> RunOutcome:
        self._release_reservation(run_id)
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

    def _release_reservation(self, run_id: str) -> None:
        """幂等释放预算预留（BUDGET_QUOTA.md §2）。"""
        release_reservation(self._reservation_refs, self._deps.budget, run_id)

    def _release_if_terminal(self, run_id: str, state: str) -> None:
        if state in ResearchRunState.terminal():
            self._release_reservation(run_id)

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
        envelope = EventEnvelope(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            schema_version="1",
            occurred_at=Timestamp.now(),
            actor=self._deps.default_actor,
            scope=f"run:{run_id}" + (f" task:{task_id}" if task_id else ""),
            payload=payload,
            payload_digest=digest_of_payload(payload),
            run_id=run_id,
            task_id=task_id,
            trace_id=trace_id,
        )
        self._deps.events.publish(envelope)


__all__ = [
    "OrchestrationDependencies",
    "RunOrchestrationService",
    "RunOutcome",
    "SessionSpec",
    "TaskOutcome",
]
