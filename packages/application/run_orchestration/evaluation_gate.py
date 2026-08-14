"""AcceptanceCriteria 评估门（Evaluation Gate）。

Research Runtime 不能自行认证成功（AGENTS.md §13、QUALITY_GATES.md）：
本模块把 TaskContract 的 AcceptanceCriteria 与独立输入事实求值，
产出 ReviewFinding/Decision；不依赖聊天记录或 Agent 自述。

- valid evidence → PASS；
- unsupported claim（无证据/证据不足）→ REJECT；
- failed acceptance criteria → REJECT（任务失败路径）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Mapping

from packages.domain.acceptance import (
    CriterionEvaluation,
    CriterionInputs,
    contract_passes,
    evaluate_contract,
)
from packages.domain.core import Timestamp
from packages.domain.enums import AcceptanceCriterionType
from packages.domain.evidence import Decision, ReviewFinding
from packages.domain.tasks import ResearchTask, TaskContract


@dataclass(frozen=True, slots=True)
class EvaluationInputs:
    """门禁求值所需的独立事实（由 orchestration 层组装）。"""

    structured_output: Mapping[str, Any] = field(default_factory=dict)
    artifacts: Mapping[str, object] = field(default_factory=dict)
    evidence_source_count: int | None = None
    review_score: Decimal | None = None
    human_approved: bool | None = None

    def to_criterion_inputs(self) -> CriterionInputs:
        return CriterionInputs(
            structured_output=dict(self.structured_output),
            artifacts=dict(self.artifacts),
            evidence_source_count=self.evidence_source_count,
            review_score=self.review_score,
            human_approved=self.human_approved,
        )


@dataclass(frozen=True, slots=True)
class GateOutcome:
    """门禁结果：verdict + 证据化 findings + decision。"""

    verdict: str
    evaluations: tuple[CriterionEvaluation, ...]
    review_finding: ReviewFinding
    decision: Decision

    @property
    def passed(self) -> bool:
        return self.verdict == "PASS"


def evaluate_task_gate(
    task: ResearchTask,
    contract: TaskContract,
    inputs: EvaluationInputs,
    *,
    reviewer: str,
) -> GateOutcome:
    """对一次任务的全部验收标准求值，产出 ReviewFinding 与 Decision。"""
    evaluations = evaluate_contract(contract.acceptance_criteria, inputs.to_criterion_inputs())
    passed = contract_passes(evaluations)
    verdict = "PASS" if passed else "REJECT"
    finding = ReviewFinding(
        id=f"finding:{task.id.value}:gate",
        review_type="acceptance_gate",
        verdict=verdict,
        findings=[item.reason for item in evaluations],
        reviewed_by=reviewer,
        reviewed_at=Timestamp.now(),
    )
    decision = Decision(
        id=f"decision:{task.id.value}:gate",
        decision="APPROVE" if passed else "REJECT",
        rationale="; ".join(item.reason for item in evaluations),
        decided_by=reviewer,
        decided_at=Timestamp.now(),
    )
    return GateOutcome(
        verdict=verdict,
        evaluations=tuple(evaluations),
        review_finding=finding,
        decision=decision,
    )


def verify_claim_with_evidence(
    evaluations: tuple[CriterionEvaluation, ...],
    evidence_source_count: int | None,
) -> bool:
    """VERIFIED Claim 的前置：存在 EVIDENCE_COVERAGE 或至少 1 条证据。"""
    if evidence_source_count is not None and evidence_source_count >= 1:
        return True
    return any(
        item.criterion_type is AcceptanceCriterionType.EVIDENCE_COVERAGE for item in evaluations
    )
