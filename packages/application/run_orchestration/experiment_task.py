"""Experiment task dispatcher for run_orchestration (IG-1 seam).

When a TaskContract is `experiment_execution`, the normal AgentRuntime session
path must not be used.  This module dispatches to a GovernedExperimentExecutor,
admits the resulting scientific ExperimentRun into the EvidenceLedger, and
returns a TaskExecutionResult that the phase runner can continue to gate and
handoff processing.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from packages.application.experiments.evidence_admission import (
    ExperimentEvidenceResult,
    ExperimentProvenance,
    register_experiment_evidence,
)
from packages.application.experiments.governed import GovernedExperimentExecutor
from packages.application.experiments.types import ExperimentExecutionRequest
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import (
    InvalidInputError,
    PortCancelledError,
    PortError,
)
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.run_orchestration.task_executor import (
    SessionSpecContext,
    TaskExecutionResult,
)
from packages.domain.enums import FailureCategory
from packages.domain.experiment_state import ExperimentRunState
from packages.domain.tasks import ResearchTask, TaskContract

_SCIENTIFIC_STATES = (
    ExperimentRunState.State.SUCCEEDED,
    ExperimentRunState.State.NEGATIVE_RESULT,
)


@dataclass(frozen=True, slots=True)
class ExperimentTaskDeps:
    """Port/dependency set for experiment task execution in orchestration."""

    executor: GovernedExperimentExecutor
    artifacts: ArtifactStore
    ledger: EvidenceLedger | None = None
    request_builder: (
        Callable[[ResearchTask, TaskContract, SessionSpecContext], ExperimentExecutionRequest]
        | None
    ) = None
    provenance_builder: Callable[[ResearchTask], ExperimentProvenance] | None = None


def dispatch_experiment(deps: Any, tctx: Any) -> TaskExecutionResult:
    """GOAL-011 EC-03：契约**声明了**「由沙箱实验后端执行」⇒ 交给装配方声明的缝。

    声明是承诺：装配方没把实验执行链接进来时**点名拒绝**（fail-closed），**不**静默回退到
    会话——否则「声明了实验」与「真的跑了实验」会分叉，而 run 仍会显示成功。

    落在本模块（而不是 `phase_runner`）是因为 `phase_runner.py` 恰好 450 行（硬上限），
    派发分支换成本函数一次调用后它净减；判定与拒绝文案归这里。
    """
    runner = deps.experiment_task
    if runner is None:
        return TaskExecutionResult(
            task=tctx.task,
            outcome="FAILED",
            message=(
                f"contract {tctx.contract.id} declares a sandboxed experiment but no "
                "experiment runner is wired into this assembly"
            ),
            failure_category=FailureCategory.CONFIGURATION,
        )
    return cast(
        TaskExecutionResult,
        runner(tctx.task, tctx.contract, tctx.spec_context, tctx.ctx.trace_id),
    )


def execute_experiment_task(
    deps: ExperimentTaskDeps,
    task: ResearchTask,
    contract: TaskContract,
    spec_context: SessionSpecContext,
    trace_id: str,
) -> TaskExecutionResult:
    """Execute one experiment task and return a TaskExecutionResult."""
    if deps.request_builder is None:
        return TaskExecutionResult(
            task=task,
            outcome="FAILED",
            message="experiment task runner has no request_builder",
            failure_category=FailureCategory.CONFIGURATION,
        )
    request = deps.request_builder(task, contract, spec_context)
    try:
        outcome = deps.executor.execute(request)
    except PortCancelledError as error:
        return _cancelled_result(task, error)
    except PortError as error:
        return _failed_result(task, error)
    if outcome.run.state not in _SCIENTIFIC_STATES:
        return _non_scientific_result(task, outcome)
    admission = _admit_or_reuse(deps, task, outcome)
    return _success_result(task, outcome, admission)


def _admit_or_reuse(
    deps: ExperimentTaskDeps,
    task: ResearchTask,
    outcome: object,
) -> ExperimentEvidenceResult | None:
    from packages.application.experiments.types import ExperimentExecutionOutcome

    assert isinstance(outcome, ExperimentExecutionOutcome)
    if deps.ledger is None:
        return None
    provenance = (
        deps.provenance_builder(task)
        if deps.provenance_builder is not None
        else ExperimentProvenance(run_id=str(task.run_id.value))
    )
    claim_id = f"claim:{outcome.run.id.value}:result"
    try:
        existing_claim = deps.ledger.get_claim(claim_id)
    except InvalidInputError:
        existing_claim = None
    if existing_claim is not None:
        relations = deps.ledger.relations_for_claim(claim_id)
        evidence = tuple(deps.ledger.get_evidence(relation.evidence_id) for relation in relations)
        return ExperimentEvidenceResult(
            claim=existing_claim,
            evidence=evidence,
            artifact_ids=tuple(
                outcome.run.result.artifact_refs if outcome.run.result is not None else ()
            ),
        )
    return register_experiment_evidence(
        deps.ledger,
        outcome.run,
        deps.artifacts,
        provenance=provenance,
    )


def _non_scientific_result(task: ResearchTask, outcome: object) -> TaskExecutionResult:
    from packages.application.experiments.types import ExperimentExecutionOutcome

    assert isinstance(outcome, ExperimentExecutionOutcome)
    state = outcome.run.state
    failure_category: FailureCategory | None = FailureCategory.EXECUTION_FAILURE
    if state == ExperimentRunState.State.CANCELLED:
        failure_category = None
    return TaskExecutionResult(
        task=task,
        outcome="FAILED",
        experiment_outcome=outcome,
        message=(
            outcome.run.result.failure_reason
            if outcome.run.result is not None and outcome.run.result.failure_reason
            else f"experiment terminated in {state}"
        ),
        failure_category=failure_category,
        attempts=task.attempt,
    )


def _success_result(
    task: ResearchTask,
    outcome: object,
    admission: ExperimentEvidenceResult | None,
) -> TaskExecutionResult:
    from packages.application.experiments.types import ExperimentExecutionOutcome

    assert isinstance(outcome, ExperimentExecutionOutcome)
    return TaskExecutionResult(
        task=task,
        outcome="SUCCEEDED",
        experiment_outcome=outcome,
        experiment_admission=admission,
        attempts=task.attempt,
        message=(
            f"experiment {outcome.run.id.value} {outcome.run.state}"
            + (f" admitted={admission.claim.id}" if admission is not None else "")
        ),
    )


def _cancelled_result(task: ResearchTask, error: PortCancelledError) -> TaskExecutionResult:
    return TaskExecutionResult(
        task=task,
        outcome="CANCELLED",
        message=str(error),
        attempts=task.attempt,
    )


def _failed_result(task: ResearchTask, error: PortError) -> TaskExecutionResult:
    return TaskExecutionResult(
        task=task,
        outcome="FAILED",
        message=str(error),
        failure_category=error.failure_category,
        attempts=task.attempt,
    )
