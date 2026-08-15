"""M11 runtime scorers 测试：Port 故障 → INFRA，deny → FAIL，gate 包装。"""

from __future__ import annotations

from decimal import Decimal

from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.policy_evaluator import FakePolicyEvaluator
from packages.application.evaluation.scorer_types import ScorerContext, ScorerInput
from packages.application.evaluation.scorers_runtime import (
    artifact_integrity_scorer,
    gate_outcome_scorer,
    policy_compliance_scorer,
)
from packages.application.ports.errors import InvalidInputError
from packages.application.run_orchestration.evaluation_gate import EvaluationInputs
from packages.domain.artifacts import Artifact, ArtifactRetentionPolicy
from packages.domain.core import ID, Digest, Timestamp, Version
from packages.domain.enums import (
    AcceptanceCriterionType,
    ArtifactState,
    ComparisonOperator,
    PolicyDecision,
)
from packages.domain.eval_result import EvalFindingStatus
from packages.domain.eval_spec import EvalCase, EvalScope
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, TaskContract


def _case(case_id: str, expected: object) -> EvalCase:
    return EvalCase(
        id=case_id,
        version=Version("1.0.0"),
        scope=EvalScope.INTEGRATION,
        input_ref=f"input://{case_id}",
        expected=expected,
        scorer_refs=(),
    )


def _context(case: EvalCase, **extra: object) -> ScorerContext:
    return ScorerContext(
        case=case,
        input=ScorerInput(actual={}, extra=extra),
    )


# --- artifact_integrity ---


def test_artifact_integrity_pass_and_corruption_fail() -> None:
    store = FakeArtifactStore()
    content = b"payload"
    artifact = Artifact(
        id="art-1",
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="text/plain",
        storage_uri="mem://art-1",
        created_by="test",
        retention_policy=ArtifactRetentionPolicy.keep_forever(),
        state=ArtifactState.STAGED,
        created_at=Timestamp.now(),
    )
    store.put(artifact, content)
    scorer = artifact_integrity_scorer(store)
    case = _case("a1", {"artifact_id": "art-1"})
    assert scorer(_context(case)).status is EvalFindingStatus.PASS
    store._content["art-1"] = b"corrupted"  # noqa: SLF001 - 故障注入
    assert scorer(_context(case)).status is EvalFindingStatus.FAIL


def test_artifact_integrity_unknown_id_is_infra() -> None:
    store = FakeArtifactStore()
    scorer = artifact_integrity_scorer(store)
    case = _case("a2", {"artifact_id": "missing"})
    finding = scorer(_context(case))
    assert finding.status is EvalFindingStatus.INFRA_ERROR
    assert isinstance(finding.detail, str)


def test_artifact_integrity_broken_store_is_infra() -> None:
    class BrokenStore(FakeArtifactStore):
        def verify(self, artifact_id: str) -> bool:
            raise InvalidInputError("down")

    scorer = artifact_integrity_scorer(BrokenStore())
    case = _case("a3", {"artifact_id": "x"})
    assert scorer(_context(case)).status is EvalFindingStatus.INFRA_ERROR


# --- policy_compliance ---


def test_policy_compliance_allow_and_deny() -> None:
    evaluator = FakePolicyEvaluator()
    scorer = policy_compliance_scorer(evaluator)
    case = _case("p1", {"actor": "agent-1", "capability": "tool.use"})
    assert scorer(_context(case)).status is EvalFindingStatus.PASS
    evaluator.set_decision("tool.use", PolicyDecision.DENY)
    assert scorer(_context(case)).status is EvalFindingStatus.FAIL


def test_policy_compliance_expected_deny_matches() -> None:
    evaluator = FakePolicyEvaluator()
    evaluator.set_decision("tool.use", PolicyDecision.DENY)
    scorer = policy_compliance_scorer(evaluator)
    case = _case("p2", {"actor": "a", "capability": "tool.use", "decision": "DENY"})
    assert scorer(_context(case)).status is EvalFindingStatus.PASS


def test_policy_compliance_requires_approval_is_fail() -> None:
    evaluator = FakePolicyEvaluator()
    evaluator.set_decision("tool.use", PolicyDecision.REQUIRE_APPROVAL)
    scorer = policy_compliance_scorer(evaluator)
    case = _case("p3", {"actor": "a", "capability": "tool.use"})
    assert scorer(_context(case)).status is EvalFindingStatus.FAIL


# --- gate_outcome ---


def _task_and_contract() -> tuple[ResearchTask, TaskContract]:
    task = ResearchTask(id=ID.generate(), run_id=ID.generate())
    contract = TaskContract(
        id="contract-1",
        version="1",
        purpose="test",
        acceptance_criteria=[
            AcceptanceCriterion(
                type=AcceptanceCriterionType.METRIC_THRESHOLD,
                metric="precision",
                operator=ComparisonOperator.GTE,
                threshold=Decimal("0.8"),
            )
        ],
    )
    return task, contract


def test_gate_outcome_pass_and_reject() -> None:
    scorer = gate_outcome_scorer()
    task, contract = _task_and_contract()
    case = _case("g1", {"verdict": "PASS"})
    inputs = EvaluationInputs(
        structured_output={},
        artifacts={},
        evidence_source_count=1,
    )
    context = _context(case, task=task, contract=contract, inputs=inputs, reviewer="gate:t")
    finding = scorer(context)
    assert finding.status is EvalFindingStatus.FAIL  # metric 缺失 → REJECT

    passing = EvaluationInputs(
        structured_output={},
        artifacts={},
        evidence_source_count=1,
        review_score=Decimal("0.9"),
        human_approved=True,
    )
    # METRIC_THRESHOLD 不可由 EvaluationInputs 注入 → 恒不通过（M7 语义）
    assert (
        scorer(_context(case, task=task, contract=contract, inputs=passing, reviewer="g")).status
        is EvalFindingStatus.FAIL
    )


def test_gate_outcome_missing_extra_is_infra() -> None:
    scorer = gate_outcome_scorer()
    case = _case("g2", {"verdict": "PASS"})
    assert scorer(_context(case)).status is EvalFindingStatus.INFRA_ERROR
