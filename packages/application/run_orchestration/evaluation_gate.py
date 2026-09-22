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
    #: 其中的**检索来源**数（`TrustLabel.RETRIEVED`）。由编排按 canonical 的 SourceRecord
    #: 判出（`count_retrieved_sources`）；未知即 `None` ⇒ 声明了性质维度的合约 fail-closed。
    retrieved_source_count: int | None = None
    review_score: Decimal | None = None
    human_approved: bool | None = None

    def to_criterion_inputs(self) -> CriterionInputs:
        return CriterionInputs(
            structured_output=dict(self.structured_output),
            artifacts=dict(self.artifacts),
            evidence_source_count=self.evidence_source_count,
            retrieved_source_count=self.retrieved_source_count,
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
    evidence_count: int | None,
) -> bool:
    """VERIFIED Claim 的前置：存在 EVIDENCE_COVERAGE 或至少 1 条证据。

    参数是**证据总条数**（含自述证据），**不是** `evidence_source_count`。
    GOAL-010 EC-02 之前这里传的是后者——当时两者同值，所以看不出问题；覆盖判据
    收紧成「只数非模型自述的来源」之后，用覆盖数当「有没有证据」的代理就成了
    **类目错误**：一个只有自述证据的任务覆盖数为 0，但它明明有证据可升级，
    会被这条前置拦下（实测：vertical slice 的 execution claim 停在 PROPOSED）。
    本函数问的是「有没有证据」，就该拿证据条数回答。
    """
    if evidence_count is not None and evidence_count >= 1:
        return True
    return any(
        item.criterion_type is AcceptanceCriterionType.EVIDENCE_COVERAGE for item in evaluations
    )
