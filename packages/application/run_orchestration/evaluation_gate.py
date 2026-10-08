"""AcceptanceCriteria 评估门（Evaluation Gate）。

Research Runtime 不能自行认证成功（AGENTS.md §13、QUALITY_GATES.md）：
本模块把 TaskContract 的 AcceptanceCriteria 与独立输入事实求值，
产出 ReviewFinding/Decision；不依赖聊天记录或 Agent 自述。

- valid evidence → PASS；
- unsupported claim（无证据/证据不足）→ REJECT；
- failed acceptance criteria → REJECT（任务失败路径）。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from packages.domain.acceptance import (
    CriterionEvaluation,
    CriterionInputs,
    SchemaCheck,
    contract_passes,
    evaluate_contract,
)
from packages.domain.core import Timestamp
from packages.domain.enums import AcceptanceCriterionType, PolicyDecision
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
    #: 实验**自报**的测试结果（名 → 通过与否）。生产者是实验产物
    #: （`experiment_result.json` / `stdout.log` / `stderr.log` 与 `ExperimentRunResult`
    #: 既有字段）**算出来**的逐项事实（GOAL-014 EC-02 / F-11 的四维之一）。
    #: 缺省空映射 ⇒ `TEST_PASSES` 维持 `no test results provided`（fail-closed）。
    tests: Mapping[str, bool] = field(default_factory=dict)
    #: 实验**自报**的数值指标（`ExperimentRunResult.metrics` 的 NUMBER 类投影）；
    #: 缺省空映射 ⇒ `METRIC_THRESHOLD` 维持 `metric … missing`（fail-closed）。
    metrics: Mapping[str, Decimal] = field(default_factory=dict)
    #: **执行期已经发生**的那次策略求值的如实记录（不是门自己再判一次）；
    #: 未知即 `None` ⇒ `POLICY_COMPLIANT` 维持 `policy decision unknown`（fail-closed）。
    policy_decision: PolicyDecision | None = None
    #: `SCHEMA_VALID` 要用的校验回调：按**合约自己声明的** `output_schema` 由装配方给出
    #: （应用层不读 schema 文件）；未注入 ⇒ 维持 `schema validator unavailable`（fail-closed）。
    schema_check: SchemaCheck | None = None

    def to_criterion_inputs(self) -> CriterionInputs:
        return CriterionInputs(
            structured_output=dict(self.structured_output),
            artifacts=dict(self.artifacts),
            tests=dict(self.tests),
            metrics=dict(self.metrics),
            evidence_source_count=self.evidence_source_count,
            retrieved_source_count=self.retrieved_source_count,
            review_score=self.review_score,
            policy_decision=self.policy_decision,
            human_approved=self.human_approved,
        )


def declared_review_score(
    contract: TaskContract, structured_output: Mapping[str, Any]
) -> Decimal | None:
    """按合约**自己声明的**路径取评审分数（GOAL-20261008-035 EC-03）。

    「评审结论进入判据面」的前提是分数**有来源**。来源只有一处：合约在
    `REVIEW_SCORE` 判据里用 `metric` 写明的**结构化输出字段路径**（如
    `review_decision.score`）—— 那是这次会话交付物里**评审者自己给出**的数。

    fail-closed（返回 `None` ⇒ 既有判词 `review score unknown`）：没声明路径、路径缺失、
    值不是数（布尔/字符串/缺失）。**绝不**回落到 0 或某个默认分：那会把「没有评审结论」
    伪装成「评审结论很差」，两者处置完全相反。
    """
    paths = [
        criterion.metric
        for criterion in contract.acceptance_criteria
        if criterion.type is AcceptanceCriterionType.REVIEW_SCORE
    ]
    for path in paths:
        if not path:
            continue
        value: Any = structured_output
        for part in path.split("."):
            if not isinstance(value, Mapping) or part not in value:
                value = None
                break
            value = value[part]
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
            continue
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            continue
    return None


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
    """对一次任务的全部验收标准求值，产出 ReviewFinding 与 Decision。

    `schema_check` 随 `EvaluationInputs` 一起进来（GOAL-014 EC-02 / F-11 的四维之一）：
    它是**按合约声明的 `output_schema` 由装配方给出**的校验回调；未注入时域函数维持
    既有的 fail-closed 判词（`schema validator unavailable`）。
    """
    # GOAL-20261008-035 EC-03：合约声明了 `REVIEW_SCORE` 时，分数从**它自己声明的**字段
    # 路径取（评审交付物里评审判给自己的数）；取不到即维持 fail-closed。显式传入的分数
    # （若有）优先——那是装配方更近的事实。
    effective = inputs
    if inputs.review_score is None:
        resolved = declared_review_score(contract, inputs.structured_output)
        if resolved is not None:
            effective = replace(inputs, review_score=resolved)
    evaluations = evaluate_contract(
        contract.acceptance_criteria,
        effective.to_criterion_inputs(),
        schema_check=effective.schema_check,
    )
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
