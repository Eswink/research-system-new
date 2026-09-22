"""TaskContract 扩展字段、HandoffBundle 结构化与 AcceptanceCriterion 求值器测试。"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

from packages.domain.acceptance import (
    CriterionEvaluation,
    CriterionInputs,
    contract_passes,
    evaluate_contract,
    evaluate_criterion,
)
from packages.domain.core import ID, Digest, Timestamp
from packages.domain.enums import (
    AcceptanceCriterionType,
    ComparisonOperator,
    PolicyDecision,
)
from packages.domain.tasks import AcceptanceCriterion, HandoffBundle, TaskContract


def _criterion(**kwargs: Any) -> AcceptanceCriterion:
    return AcceptanceCriterion(type=AcceptanceCriterionType.SCHEMA_VALID, **kwargs)


def _contract(**kwargs: Any) -> TaskContract:
    criteria = kwargs.pop(
        "acceptance_criteria",
        [AcceptanceCriterion(type=AcceptanceCriterionType.SCHEMA_VALID)],
    )
    return TaskContract(
        id="c1",
        version="1.0.0",
        purpose="p",
        acceptance_criteria=criteria,
        **kwargs,
    )


def test_task_contract_carries_input_schema_and_budget() -> None:
    contract = _contract(
        input_schema="domain_discovery_input_v1",
        budget={"model_cost_usd": Decimal("50.00"), "tool_requests": None},
    )
    assert contract.input_schema == "domain_discovery_input_v1"
    assert contract.budget["model_cost_usd"] == Decimal("50.00")
    assert contract.budget["tool_requests"] is None


def test_task_contract_carries_failure_policy() -> None:
    contract = _contract(
        failure_policy={
            "on_validation_failure": "DEAD_LETTER",
            "allow_partial_evidence": True,
            "max_retries": 2,
            "retryable_artifacts": ["source_set", "metrics"],
        }
    )
    assert contract.failure_policy["on_validation_failure"] == "DEAD_LETTER"
    assert contract.failure_policy["allow_partial_evidence"] is True
    assert contract.failure_policy["max_retries"] == 2
    assert contract.failure_policy["retryable_artifacts"] == ["source_set", "metrics"]


def test_acceptance_criterion_structured_parameters() -> None:
    criterion = AcceptanceCriterion(
        type=AcceptanceCriterionType.METRIC_THRESHOLD,
        metric="f1",
        operator=ComparisonOperator.GTE,
        threshold=Decimal("0.8"),
    )
    assert criterion.metric == "f1"
    assert criterion.operator is ComparisonOperator.GTE
    assert criterion.threshold == Decimal("0.8")
    with pytest.raises(ValueError):
        AcceptanceCriterion(type=AcceptanceCriterionType.EVIDENCE_COVERAGE, minimum_sources=-1)


def test_handoff_bundle_requires_summary() -> None:
    with pytest.raises(ValueError):
        HandoffBundle(
            task_id=ID.generate(),
            producer="agent-a",
            summary="",
            digest=Digest("ab" * 32),
        )


def test_handoff_bundle_defaults_created_at_utc() -> None:
    bundle = HandoffBundle(
        task_id=ID.generate(),
        producer="agent-a",
        summary="done",
        digest=Digest("ab" * 32),
    )
    created = bundle.created_at.value
    assert created.tzinfo is not None
    assert created.utcoffset() == timezone.utc.utcoffset(created)


def test_handoff_bundle_carries_producer_references() -> None:
    bundle = HandoffBundle(
        task_id=ID.generate(),
        producer="agent-a",
        producer_agent_id="agent-a",
        producer_role_id="domain_researcher",
        summary="done",
        digest=Digest("ab" * 32),
        created_at=Timestamp(datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)),
    )
    assert bundle.producer_agent_id == "agent-a"
    assert bundle.producer_role_id == "domain_researcher"
    assert bundle.created_at.value == datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)


def _schema_check(output: object) -> str | None:
    if isinstance(output, dict) and "result" in output:
        return None
    return "missing required key 'result'"


def test_schema_valid_passes_with_validator() -> None:
    criterion = _criterion()
    verdict = evaluate_criterion(
        criterion, CriterionInputs(structured_output={"result": "ok"}), schema_check=_schema_check
    )
    assert verdict.passed is True


def test_schema_valid_fails_closed_without_validator() -> None:
    verdict = evaluate_criterion(_criterion(), CriterionInputs(structured_output={"result": "ok"}))
    assert verdict.passed is False
    assert "validator unavailable" in verdict.reason


def test_schema_valid_rejects_violating_output() -> None:
    verdict = evaluate_criterion(
        _criterion(), CriterionInputs(structured_output={"other": 1}), schema_check=_schema_check
    )
    assert verdict.passed is False
    assert "schema violation" in verdict.reason


def test_schema_valid_fails_on_missing_output() -> None:
    verdict = evaluate_criterion(_criterion(), CriterionInputs())
    assert verdict.passed is False
    assert "missing" in verdict.reason


def test_artifact_exists_requires_name() -> None:
    bare = AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)
    verdict = evaluate_criterion(bare, CriterionInputs(artifacts={"a": object()}))
    assert verdict.passed is False
    assert "not configured" in verdict.reason


def test_artifact_exists_uses_artifact_field() -> None:
    criterion = AcceptanceCriterion(
        type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact="source_set"
    )
    present = evaluate_criterion(criterion, CriterionInputs(artifacts={"source_set": object()}))
    missing = evaluate_criterion(criterion, CriterionInputs(artifacts={}))
    assert present.passed is True
    assert missing.passed is False
    assert "missing" in missing.reason


def test_test_passes_requires_results() -> None:
    criterion = AcceptanceCriterion(type=AcceptanceCriterionType.TEST_PASSES)
    empty = evaluate_criterion(criterion, CriterionInputs(tests={}))
    passed = evaluate_criterion(criterion, CriterionInputs(tests={"a": True, "b": True}))
    failed = evaluate_criterion(criterion, CriterionInputs(tests={"a": True, "b": False}))
    assert empty.passed is False
    assert passed.passed is True
    assert failed.passed is False
    assert "failing" in failed.reason


@pytest.mark.parametrize(
    ("operator", "threshold", "value", "expected"),
    [
        (ComparisonOperator.GT, Decimal("0.5"), Decimal("0.6"), True),
        (ComparisonOperator.GT, Decimal("0.5"), Decimal("0.5"), False),
        (ComparisonOperator.GTE, Decimal("0.5"), Decimal("0.5"), True),
        (ComparisonOperator.EQ, Decimal("1"), Decimal("1"), True),
        (ComparisonOperator.EQ, Decimal("1"), Decimal("2"), False),
        (ComparisonOperator.LTE, Decimal("0.5"), Decimal("0.5"), True),
        (ComparisonOperator.LT, Decimal("0.5"), Decimal("0.5"), False),
    ],
)
def test_metric_threshold_comparison(
    operator: ComparisonOperator, threshold: Decimal, value: Decimal, expected: bool
) -> None:
    criterion = AcceptanceCriterion(
        type=AcceptanceCriterionType.METRIC_THRESHOLD,
        metric="f1",
        operator=operator,
        threshold=threshold,
    )
    verdict = evaluate_criterion(criterion, CriterionInputs(metrics={"f1": value}))
    assert verdict.passed is expected


def test_metric_threshold_fails_when_metric_missing() -> None:
    criterion = AcceptanceCriterion(
        type=AcceptanceCriterionType.METRIC_THRESHOLD,
        metric="f1",
        operator=ComparisonOperator.GTE,
        threshold=Decimal("0.5"),
    )
    verdict = evaluate_criterion(criterion, CriterionInputs(metrics={}))
    assert verdict.passed is False
    assert "missing" in verdict.reason


def test_evidence_coverage_threshold() -> None:
    criterion = AcceptanceCriterion(
        type=AcceptanceCriterionType.EVIDENCE_COVERAGE, minimum_sources=10
    )
    enough = evaluate_criterion(criterion, CriterionInputs(evidence_source_count=10))
    short = evaluate_criterion(criterion, CriterionInputs(evidence_source_count=9))
    unknown = evaluate_criterion(criterion, CriterionInputs())
    assert enough.passed is True
    assert short.passed is False
    assert unknown.passed is False


def test_evidence_coverage_defaults_ignore_the_nature_dimension() -> None:
    """没声明 `minimum_retrieved_sources` 的合约：行为**逐字不变**（不需要那个数）。"""
    criterion = AcceptanceCriterion(
        type=AcceptanceCriterionType.EVIDENCE_COVERAGE, minimum_sources=1
    )
    verdict = evaluate_criterion(criterion, CriterionInputs(evidence_source_count=1))
    assert verdict.passed is True and verdict.reason == "1 >= 1 sources"


def test_evidence_coverage_nature_dimension_requires_a_retrieved_source() -> None:
    """GOAL-011 EC-02：声明了性质维度 ⇒ **总数够也不能顶替**「有检索来源」。"""
    criterion = AcceptanceCriterion(
        type=AcceptanceCriterionType.EVIDENCE_COVERAGE,
        minimum_sources=1,
        minimum_retrieved_sources=1,
    )
    # 计数够（1 条声明输入）、但一条检索来源都没有 ⇒ 判拒，且原因**点名**缺的性质。
    no_retrieval = evaluate_criterion(
        criterion, CriterionInputs(evidence_source_count=1, retrieved_source_count=0)
    )
    assert no_retrieval.passed is False
    assert "0 < 1 retrieved sources" in no_retrieval.reason
    # 有检索来源 ⇒ 过，原因同时给出两个维度（读面/日志能自证判的是哪两个数）。
    with_retrieval = evaluate_criterion(
        criterion, CriterionInputs(evidence_source_count=2, retrieved_source_count=1)
    )
    assert with_retrieval.passed is True
    assert with_retrieval.reason == "2 >= 1 sources; 1 >= 1 retrieved"
    # 未知性质数 ⇒ fail-closed（不把它当成 0，也不当成「没这条要求」）。
    unknown = evaluate_criterion(
        criterion, CriterionInputs(evidence_source_count=2, retrieved_source_count=None)
    )
    assert unknown.passed is False
    assert unknown.reason == "retrieved source count unknown"


def test_evidence_coverage_nature_dimension_still_needs_the_total() -> None:
    """反方向也成立：有检索来源但总数不够 ⇒ 仍然判拒（不是「有一条检索来源就够」）。"""
    criterion = AcceptanceCriterion(
        type=AcceptanceCriterionType.EVIDENCE_COVERAGE,
        minimum_sources=3,
        minimum_retrieved_sources=1,
    )
    verdict = evaluate_criterion(
        criterion, CriterionInputs(evidence_source_count=1, retrieved_source_count=1)
    )
    assert verdict.passed is False
    assert verdict.reason == "1 < 3 sources"


def test_acceptance_criterion_rejects_negative_nature_threshold() -> None:
    with pytest.raises(ValueError, match="minimum_retrieved_sources must be >= 0"):
        AcceptanceCriterion(
            type=AcceptanceCriterionType.EVIDENCE_COVERAGE,
            minimum_sources=1,
            minimum_retrieved_sources=-1,
        )


def test_review_score_threshold() -> None:
    criterion = AcceptanceCriterion(
        type=AcceptanceCriterionType.REVIEW_SCORE,
        operator=ComparisonOperator.GTE,
        threshold=Decimal("3.5"),
    )
    passed = evaluate_criterion(criterion, CriterionInputs(review_score=Decimal("4.0")))
    failed = evaluate_criterion(criterion, CriterionInputs(review_score=Decimal("3.0")))
    assert passed.passed is True
    assert failed.passed is False


def test_policy_compliant_decision() -> None:
    criterion = AcceptanceCriterion(type=AcceptanceCriterionType.POLICY_COMPLIANT)
    allowed = evaluate_criterion(criterion, CriterionInputs(policy_decision=PolicyDecision.ALLOW))
    denied = evaluate_criterion(criterion, CriterionInputs(policy_decision=PolicyDecision.DENY))
    unknown = evaluate_criterion(criterion, CriterionInputs())
    assert allowed.passed is True
    assert denied.passed is False
    assert unknown.passed is False


def test_human_approval() -> None:
    criterion = AcceptanceCriterion(type=AcceptanceCriterionType.HUMAN_APPROVAL)
    assert evaluate_criterion(criterion, CriterionInputs(human_approved=True)).passed is True
    assert evaluate_criterion(criterion, CriterionInputs(human_approved=False)).passed is False
    assert evaluate_criterion(criterion, CriterionInputs()).passed is False


def test_custom_evaluator_defers_to_orchestration() -> None:
    criterion = AcceptanceCriterion(
        type=AcceptanceCriterionType.CUSTOM_EVALUATOR, evaluator="reproducibility_check"
    )
    verdict = evaluate_criterion(criterion, CriterionInputs())
    assert verdict.passed is False
    assert "orchestration" in verdict.reason


def test_contract_passes_requires_all() -> None:
    ok = CriterionEvaluation(AcceptanceCriterionType.SCHEMA_VALID, True, "ok")
    bad = CriterionEvaluation(AcceptanceCriterionType.ARTIFACT_EXISTS, False, "missing")
    assert contract_passes([ok, ok]) is True
    assert contract_passes([ok, bad]) is False
    assert contract_passes([]) is False


def test_evaluate_contract_maps_all_criteria() -> None:
    contract = _contract(
        acceptance_criteria=[
            AcceptanceCriterion(type=AcceptanceCriterionType.SCHEMA_VALID),
            AcceptanceCriterion(
                type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact="source_set"
            ),
        ]
    )
    verdicts = evaluate_contract(
        contract.acceptance_criteria,
        CriterionInputs(structured_output={"result": 1}, artifacts={"source_set": object()}),
        schema_check=_schema_check,
    )
    assert len(verdicts) == 2
    assert all(item.passed for item in verdicts)
    assert contract_passes(verdicts) is True
