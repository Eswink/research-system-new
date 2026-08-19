"""M11 runtime scorers（经现有 Port 的确定性 scorer 工厂）。

与 scorers.py 的纯 scorer 不同，这些 scorer 依赖 Port 实例（显式注入、
工厂构造），供 EvalRunner 的 runtime_scorers 挂载（composition root）。
约束：Port 异常一律转换为 INFRA_ERROR（评测设施故障不得判为被评对象
质量失败）；被评对象输入不含 secret；不做写操作。
"""

from __future__ import annotations

from typing import Mapping

from packages.application.evaluation.scorer_types import (
    V1,
    ScorerContext,
    ScorerFn,
    make_finding,
)
from packages.application.evaluation.scorers_evidence import (
    _EVIDENCE_SCORER,
    _EXPERIMENT_SCORER,
    evidence_provenance_scorer,
    experiment_reproducibility_scorer,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.policy_evaluator import (
    PolicyEvaluation,
    PolicyEvaluator,
    PolicyRequest,
)
from packages.application.run_orchestration.evaluation_gate import (
    EvaluationInputs,
    evaluate_task_gate,
)
from packages.domain.enums import PolicyDecision
from packages.domain.eval_result import EvalFindingStatus, ScorerFinding
from packages.domain.tasks import ResearchTask, TaskContract

_ARTIFACT_SCORER = "artifact_integrity"
_POLICY_SCORER = "policy_compliance"
_GATE_SCORER = "gate_outcome"


def artifact_integrity_scorer(store: ArtifactStore) -> ScorerFn:
    """expected = {'artifact_id': str}；digest 校验通过 → PASS。"""

    def score(ctx: ScorerContext) -> ScorerFinding:
        spec = ctx.case.expected
        if not isinstance(spec, Mapping) or not isinstance(spec.get("artifact_id"), str):
            return make_finding(
                _ARTIFACT_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "expected must be {'artifact_id': str}",
            )
        artifact_id = str(spec["artifact_id"])
        try:
            verified = store.verify(artifact_id)
        except Exception as exc:  # noqa: BLE001 - Port 故障 = 评测设施故障
            return make_finding(
                _ARTIFACT_SCORER,
                ctx,
                EvalFindingStatus.INFRA_ERROR,
                f"artifact store failure: {type(exc).__name__}",
            )
        if verified:
            return make_finding(
                _ARTIFACT_SCORER, ctx, EvalFindingStatus.PASS, "artifact digest verified"
            )
        return make_finding(
            _ARTIFACT_SCORER,
            ctx,
            EvalFindingStatus.FAIL,
            f"artifact {artifact_id} integrity check failed",
        )

    return score


def policy_compliance_scorer(evaluator: PolicyEvaluator) -> ScorerFn:
    """expected = {'actor','capability','decision'}；decision 默认 ALLOW。"""

    def score(ctx: ScorerContext) -> ScorerFinding:
        spec = ctx.case.expected
        if not isinstance(spec, Mapping):
            return make_finding(
                _POLICY_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "expected must be {'actor': str, 'capability': str, 'decision': str}",
            )
        actor = spec.get("actor")
        capability = spec.get("capability")
        if not isinstance(actor, str) or not isinstance(capability, str):
            return make_finding(
                _POLICY_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "actor and capability must be strings",
            )
        expected_decision = spec.get("decision", "ALLOW")
        try:
            evaluation = evaluator.evaluate(PolicyRequest(actor=actor, capability=capability))
        except Exception as exc:  # noqa: BLE001 - Port 故障 = 评测设施故障
            return make_finding(
                _POLICY_SCORER,
                ctx,
                EvalFindingStatus.INFRA_ERROR,
                f"policy evaluator failure: {type(exc).__name__}",
            )
        return _policy_finding(ctx, evaluation, str(expected_decision))

    return score


def _policy_finding(
    ctx: ScorerContext, evaluation: PolicyEvaluation, expected_decision: str
) -> ScorerFinding:
    if evaluation.decision.value == expected_decision:
        return make_finding(
            _POLICY_SCORER,
            ctx,
            EvalFindingStatus.PASS,
            f"policy decision {evaluation.decision.value}",
        )
    if evaluation.decision is PolicyDecision.REQUIRE_APPROVAL:
        return make_finding(_POLICY_SCORER, ctx, EvalFindingStatus.FAIL, "policy requires approval")
    return make_finding(
        _POLICY_SCORER,
        ctx,
        EvalFindingStatus.FAIL,
        f"policy decision {evaluation.decision.value} != {expected_decision}",
    )


def gate_outcome_scorer() -> ScorerFn:
    """包装 M7 evaluate_task_gate 为被观测对象（Research Runtime 不自证）。

    输入来自 ScorerInput.extra：{'task','contract','inputs','reviewer'}；
    expected = {'verdict': 'PASS'}。实际 GateOutcome 由 M7 纯求值产生，
    本 scorer 只把 verdict 转成结构化 finding（不记录时间戳字段）。
    """

    def score(ctx: ScorerContext) -> ScorerFinding:
        spec = ctx.case.expected
        if not isinstance(spec, Mapping) or spec.get("verdict") != "PASS":
            return make_finding(
                _GATE_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "expected must be {'verdict': 'PASS'}",
            )
        extra = _gate_extra(ctx)
        if extra is None:
            return make_finding(
                _GATE_SCORER,
                ctx,
                EvalFindingStatus.INFRA_ERROR,
                "gate_outcome requires valid extra task/contract/inputs/reviewer",
            )
        task, contract, inputs, reviewer = extra
        outcome = evaluate_task_gate(task=task, contract=contract, inputs=inputs, reviewer=reviewer)
        if outcome.passed:
            return make_finding(
                _GATE_SCORER, ctx, EvalFindingStatus.PASS, "m7 acceptance gate PASS"
            )
        return make_finding(
            _GATE_SCORER,
            ctx,
            EvalFindingStatus.FAIL,
            "m7 acceptance gate REJECT: " + "; ".join(item.reason for item in outcome.evaluations),
        )

    return score


def _gate_extra(
    ctx: ScorerContext,
) -> tuple[ResearchTask, TaskContract, EvaluationInputs, str] | None:
    task = ctx.input.extra.get("task")
    contract = ctx.input.extra.get("contract")
    inputs = ctx.input.extra.get("inputs")
    reviewer = ctx.input.extra.get("reviewer")
    if not isinstance(task, ResearchTask) or not isinstance(contract, TaskContract):
        return None
    if not isinstance(inputs, EvaluationInputs) or not isinstance(reviewer, str):
        return None
    return task, contract, inputs, reviewer


RUNTIME_SCORER_VERSIONS = {
    _ARTIFACT_SCORER: V1,
    _POLICY_SCORER: V1,
    _GATE_SCORER: V1,
    _EVIDENCE_SCORER: V1,
    _EXPERIMENT_SCORER: V1,
}

__all__ = [
    "RUNTIME_SCORER_VERSIONS",
    "artifact_integrity_scorer",
    "evidence_provenance_scorer",
    "experiment_reproducibility_scorer",
    "gate_outcome_scorer",
    "policy_compliance_scorer",
]
