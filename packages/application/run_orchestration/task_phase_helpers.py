"""Shared phase-runner helper functions (IG-1 refactor for source limits)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packages.application.experiments.types import ExperimentExecutionOutcome
from packages.application.ports.agent_runtime import AgentSessionResult
from packages.application.ports.errors import InvalidInputError
from packages.application.run_orchestration.evaluation_gate import (
    EvaluationInputs,
    GateOutcome,
    evaluate_task_gate,
)
from packages.application.run_orchestration.memory_promotion import (
    MemoryPromotionContext,
    promote_memory_from_registration,
)
from packages.application.run_orchestration.outcomes import TaskOutcome
from packages.application.run_orchestration.result_handler import (
    RegistrationDeps,
    ResultRegistration,
    register_declared_input_sources,
    register_session_result,
)
from packages.domain.enums import MemoryType
from packages.domain.events import EventType
from packages.domain.evidence import Evidence, EvidenceRelation, EvidenceRelationType
from packages.domain.experiment_state import ExperimentRunState
from packages.domain.failure_policy import OnTaskFailure
from packages.domain.session_state import AgentSessionState
from packages.domain.tasks import ResearchTask


@dataclass(frozen=True, slots=True)
class PhaseStep:
    """Return type for phase-runner step helpers."""

    handoff: object | None = None
    verdict: str | None = None
    failure: Any | None = None
    # 这次失败是"交回派发方的重排"（durable 侧已 RETRY_SCHEDULED、等 deadline），
    # 不是终局失败：run 级据此停车（PAUSED）而不是判 FAILED（PLAN-20260915-081）。
    retry_deferred: bool = False
    # GOAL-004 cycle 3（EC-03）：终局失败但契约声明了 `on_task_failure: CONTINUE`
    # ⇒ 失败被记账（消息在这里）但不返回 RunOutcome，run 继续跑剩余工作。
    tolerated_failure: str | None = None


def tolerated_outcome(task: ResearchTask, message: str) -> TaskOutcome:
    """被容忍失败的 `TaskOutcome`（GOAL-004 cycle 3）：记账但不改 run 的走向。"""
    return TaskOutcome(
        task=task,
        outcome="FAILED",
        verdict=OnTaskFailure.CONTINUE,
        message=message,
        failure_policy=OnTaskFailure.CONTINUE,
    )


def failure_step(
    deps: Any,
    tctx: Any,
    message: str,
    system_failure: bool,
) -> PhaseStep:
    """一个任务失败该怎么落地——**唯一的失败分叉点**（EC-03）。

    契约视图说容忍（`CONTINUE`）⇒ 返回被容忍的步骤（调用方转成 TaskOutcome 继续跑）；
    否则与基线逐字一致：`deps.fail(...)`（run 立刻失败）。三处失败点（任务失败 /
    结果畸形 / 验收门拒收）都走这里，策略因此没有第二条解释。
    """
    if tctx.contract.failure_policy_view().tolerated:
        deps.emit(
            EventType.TASK_FAILED,
            {
                "task_id": tctx.task.id.value,
                "message": message,
                "failure_policy": tctx.contract.failure_policy_view().on_task_failure,
            },
            tctx.ctx.run_id,
            tctx.ctx.trace_id,
            tctx.task.id.value,
        )
        return PhaseStep(tolerated_failure=message)
    return PhaseStep(failure=deps.fail(tctx.ctx.run_id, message, system_failure))


def registration_from_experiment(
    deps: Any,
    execution: Any,
    tctx: Any,
) -> ResultRegistration:
    outcome = execution.experiment_outcome
    assert outcome is not None
    artifact_ids = (
        set(outcome.run.result.artifact_refs) if outcome.run.result is not None else set()
    )
    artifacts = tuple(
        artifact for artifact in deps.artifacts.list_refs() if artifact.id in artifact_ids
    )
    admission = execution.experiment_admission
    claim_id = admission.claim.id if admission is not None else f"claim:{tctx.task.id.value}:result"
    inputs = register_declared_input_sources(
        RegistrationDeps(
            store=deps.artifacts,
            agent_id=tctx.spec_context.agent.id,
            ledger=deps.ledger,
            declared_inputs=tctx.spec_context.declared_input_artifacts,
        ),
        tctx.task,
        claim_id=claim_id,
    )
    # 声明输入的 evidence 必须挂到 claim 上，否则 `GET /runs/{id}/evidence` 的
    # claim-relation 投影看不到它（GOAL-010 EC-02：判据要求来源**可读**）。
    if admission is not None and deps.ledger is not None:
        for evidence in inputs:
            deps.ledger.attach_relation(
                EvidenceRelation(
                    claim_id=claim_id,
                    evidence_id=evidence.id,
                    relation=EvidenceRelationType.SUPPORTS,
                )
            )
    return ResultRegistration(
        artifacts=artifacts,
        evidence=(admission.evidence if admission is not None else ()) + inputs,
        claims=(admission.claim,) if admission is not None else (),
        # 同一判别性质（GOAL-010 EC-02）：本路径的「自身产物」是该 experiment run
        # 自己登记的 artifact_refs ⇒ 它们不构成覆盖来源。
        self_artifact_ids=frozenset(artifact_ids),
    )


def evaluate_gate_experiment(
    deps: Any,
    tctx: Any,
    registration: ResultRegistration,
    outcome: object,
) -> GateOutcome | None:
    assert isinstance(outcome, ExperimentExecutionOutcome)
    run = outcome.run
    metrics: dict[str, object] = {}
    if run.result is not None:
        for metric in run.result.metrics:
            value = metric.value
            if hasattr(value, "to_eng_string"):
                value = str(value)
            metrics[metric.metric.name] = value
    structured_output: dict[str, object] = {
        "experiment_run_id": run.id.value,
        "status": run.state,
        "artifact_refs": (list(run.result.artifact_refs) if run.result is not None else []),
        "metrics": metrics,
    }
    session_result = AgentSessionResult(
        session_id=f"experiment:{run.id.value}",
        status=AgentSessionState.State.SUCCEEDED,
        structured_output=structured_output,
    )
    return evaluate_gate(deps, tctx, registration, session_result)


def promote_memory(
    deps: Any,
    registration: ResultRegistration,
    *,
    kind: MemoryType = MemoryType.FACT,
) -> None:
    if deps.memory_gate is None:
        return
    promote_memory_from_registration(
        MemoryPromotionContext(memory_gate=deps.memory_gate, kind=kind),
        registration,
    )


def register_or_fail(
    deps: Any,
    tctx: Any,
    session_result: AgentSessionResult,
    retrieved: tuple[Evidence, ...] = (),
) -> ResultRegistration | str:
    try:
        return register_session_result(
            RegistrationDeps(
                store=deps.artifacts,
                agent_id=tctx.spec_context.agent.id,
                ledger=deps.ledger,
                declared_inputs=tctx.spec_context.declared_input_artifacts,
                retrieved_evidence=retrieved,
            ),
            tctx.task,
            tctx.contract,
            session_result.structured_output,
        )
    except InvalidInputError as error:
        return str(error)


def evaluate_gate(
    deps: Any,
    tctx: Any,
    registration: ResultRegistration,
    session_result: AgentSessionResult,
) -> GateOutcome | None:
    gate = evaluate_task_gate(
        tctx.task,
        tctx.contract,
        EvaluationInputs(
            structured_output=session_result.structured_output,
            artifacts=artifact_view(registration),
            evidence_source_count=registration.evidence_source_count,
        ),
        reviewer=f"gate:{tctx.spec_context.agent.id}",
    )
    return gate if gate.passed else None


def artifact_view(registration: ResultRegistration) -> dict[str, object]:
    view: dict[str, object] = {}
    for artifact in registration.artifacts:
        view[artifact.id] = artifact
        view[artifact.id.split(":")[-1]] = artifact
    return view


def register_and_gate(
    deps: Any,
    tctx: Any,
    session_result: AgentSessionResult,
    retrieved: tuple[Evidence, ...] = (),
) -> PhaseStep:
    """Register session output, evaluate gate, promote claim/memory, handoff.

    `retrieved` = 运行链自己取得的证据（GOAL-011 EC-01）：它随会话结果**同一个** claim
    登记，读面与覆盖计数因此看得到它（experiment 路径暂不携带——EC-03 的范围）。
    """
    task = tctx.task
    registered = register_or_fail(deps, tctx, session_result, retrieved)
    if isinstance(registered, str):
        return failure_step(
            deps,
            tctx,
            f"task {task.id.value} produced malformed result: {registered}",
            True,
        )
    registration = registered
    gate = evaluate_gate(deps, tctx, registration, session_result)
    if gate is None:
        return failure_step(
            deps,
            tctx,
            f"task {task.id.value} rejected by acceptance gate",
            False,
        )
    return _finish_task_step(
        deps,
        tctx,
        registration,
        gate,
        producer=f"agent:{tctx.spec_context.agent.id}",
    )


def register_and_gate_experiment(
    deps: Any,
    tctx: Any,
    execution: Any,
) -> PhaseStep:
    """Register/gate/handoff an ExperimentTask execution result."""
    task = tctx.task
    assert execution.experiment_outcome is not None
    registration = registration_from_experiment(deps, execution, tctx)
    gate = evaluate_gate_experiment(deps, tctx, registration, execution.experiment_outcome)
    if gate is None:
        return failure_step(
            deps,
            tctx,
            f"task {task.id.value} rejected by acceptance gate",
            False,
        )
    kind = (
        MemoryType.NEGATIVE_RESULT
        if execution.experiment_outcome is not None
        and execution.experiment_outcome.run.state == ExperimentRunState.State.NEGATIVE_RESULT
        else MemoryType.FACT
    )
    return _finish_task_step(
        deps,
        tctx,
        registration,
        gate,
        producer=f"experiment:{tctx.spec_context.agent.id}",
        kind=kind,
    )


def _finish_task_step(  # noqa: PLR0913
    deps: Any,
    tctx: Any,
    registration: ResultRegistration,
    gate: Any,
    *,
    producer: str,
    kind: MemoryType = MemoryType.FACT,
) -> PhaseStep:
    """Promote claims/memory, record usage, and build the handoff step."""
    from packages.application.run_orchestration.claim_promotion import (
        ClaimPromotionContext,
        promote_registered_claims,
    )
    from packages.application.run_orchestration.handoff_builder import (
        HandoffPayload,
        build_handoff,
    )
    from packages.application.run_orchestration.usage_recording import record_task_usage

    task = tctx.task
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
    promote_memory(deps, registration, kind=kind)
    record_task_usage(deps.budget, task)
    return PhaseStep(
        handoff=build_handoff(
            HandoffPayload(
                task=task,
                producer=producer,
                summary=f"phase output for {task.contract_id}",
                artifact_refs=registration.artifact_refs(),
                evidence_refs=registration.evidence_refs(),
                claim_refs=registration.claim_refs(),
                decision_refs=(gate.decision.id,),
            )
        ),
        verdict=gate.verdict,
    )
