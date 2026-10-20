"""AcceptanceCriterion 求值器（纯函数，无副作用）。

来源：docs/architecture/TASK_HANDOFF.md §3、CODEX_BOOTSTRAP.md §M4。
约束："LLM 不能自行宣布验收通过" —— 每个 criterion 的判定只依赖显式注入的
CriterionInputs，不依赖任何聊天记录或 Agent 自述。

SCHEMA_VALID 的 JSON Schema 校验由调用方通过 schema_check 回调注入
（application 层使用 jsonschema）；未注入校验器时 fail-closed（不通过）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Callable, Mapping

from packages.domain.enums import AcceptanceCriterionType, ComparisonOperator, PolicyDecision
from packages.domain.tasks import AcceptanceCriterion

SchemaCheck = Callable[[object], str | None]


@dataclass(frozen=True, slots=True)
class CriterionInputs:
    """求值所需的全部外部事实；未提供的维度视为未知（fail-closed）。"""

    structured_output: object = None
    artifacts: Mapping[str, object] = field(default_factory=dict)
    tests: Mapping[str, bool] = field(default_factory=dict)
    metrics: Mapping[str, Decimal] = field(default_factory=dict)
    evidence_source_count: int | None = None
    #: 其中的**检索来源**数（`TrustLabel.RETRIEVED`，GOAL-011 EC-02）。它是**性质分类下的
    #: 计数**，由编排从 canonical 的 SourceRecord 判出来，不是由证据条数推的。
    retrieved_source_count: int | None = None
    #: 本任务**自己的**工具证据条数（`Evidence.tool_refs` 非空，GOAL-20261020-090）。
    #: 与 `retrieved_source_count` 判的是**不同的面**：后者是「来源的性质」（可由跨相输入的
    #: 产出方声明推出），本项是「本任务真的调用过工具」。两者都不彼此顶替。
    tool_evidence_count: int | None = None
    review_score: Decimal | None = None
    policy_decision: PolicyDecision | None = None
    human_approved: bool | None = None


@dataclass(frozen=True, slots=True)
class CriterionEvaluation:
    criterion_type: AcceptanceCriterionType
    passed: bool
    reason: str


def evaluate_criterion(
    criterion: AcceptanceCriterion,
    inputs: CriterionInputs,
    *,
    schema_check: SchemaCheck | None = None,
) -> CriterionEvaluation:
    """对单个验收标准求值；未知维度一律判定为不通过并给出原因。"""
    evaluator = _EVALUATORS.get(criterion.type)
    if evaluator is None:
        return CriterionEvaluation(
            criterion.type, False, f"no evaluator for criterion type {criterion.type}"
        )
    return evaluator(criterion, inputs, schema_check)


def evaluate_contract(
    criteria: list[AcceptanceCriterion],
    inputs: CriterionInputs,
    *,
    schema_check: SchemaCheck | None = None,
) -> list[CriterionEvaluation]:
    """对 TaskContract 的全部验收标准求值；任一不通过即整体不通过。"""
    return [evaluate_criterion(item, inputs, schema_check=schema_check) for item in criteria]


def contract_passes(verdicts: list[CriterionEvaluation]) -> bool:
    if not verdicts:
        return False
    return all(item.passed for item in verdicts)


Evaluator = Callable[
    [AcceptanceCriterion, CriterionInputs, SchemaCheck | None], CriterionEvaluation
]


def _evaluate_schema_valid(
    criterion: AcceptanceCriterion, inputs: CriterionInputs, schema_check: SchemaCheck | None
) -> CriterionEvaluation:
    if inputs.structured_output is None:
        return CriterionEvaluation(criterion.type, False, "structured output missing")
    if schema_check is None:
        return CriterionEvaluation(criterion.type, False, "schema validator unavailable")
    error = schema_check(inputs.structured_output)
    if error is None:
        return CriterionEvaluation(criterion.type, True, "structured output matches schema")
    return CriterionEvaluation(criterion.type, False, f"schema violation: {error}")


def _evaluate_artifact_exists(
    criterion: AcceptanceCriterion, inputs: CriterionInputs, schema_check: SchemaCheck | None
) -> CriterionEvaluation:
    name = criterion.artifact or criterion.target
    if not name:
        return CriterionEvaluation(criterion.type, False, "artifact name not configured")
    if name in inputs.artifacts:
        return CriterionEvaluation(criterion.type, True, f"artifact {name} exists")
    return CriterionEvaluation(criterion.type, False, f"artifact {name} missing")


def _evaluate_test_passes(
    criterion: AcceptanceCriterion, inputs: CriterionInputs, schema_check: SchemaCheck | None
) -> CriterionEvaluation:
    failed = [name for name, passed in inputs.tests.items() if not passed]
    if failed:
        return CriterionEvaluation(criterion.type, False, f"failing tests: {', '.join(failed)}")
    if not inputs.tests:
        return CriterionEvaluation(criterion.type, False, "no test results provided")
    return CriterionEvaluation(criterion.type, True, "all tests pass")


def _evaluate_metric_threshold(
    criterion: AcceptanceCriterion, inputs: CriterionInputs, schema_check: SchemaCheck | None
) -> CriterionEvaluation:
    if not criterion.metric:
        return CriterionEvaluation(criterion.type, False, "metric name not configured")
    if criterion.operator is None or criterion.threshold is None:
        return CriterionEvaluation(criterion.type, False, "operator/threshold not configured")
    value = inputs.metrics.get(criterion.metric)
    if value is None:
        return CriterionEvaluation(criterion.type, False, f"metric {criterion.metric} missing")
    passed = _compare(value, criterion.operator, criterion.threshold)
    reason = f"{criterion.metric}={value} {criterion.operator.value} {criterion.threshold}"
    return CriterionEvaluation(criterion.type, passed, reason)


def _compare(value: Decimal, operator: ComparisonOperator, threshold: Decimal) -> bool:
    if operator is ComparisonOperator.GT:
        return value > threshold
    if operator is ComparisonOperator.GTE:
        return value >= threshold
    if operator is ComparisonOperator.EQ:
        return value == threshold
    if operator is ComparisonOperator.LTE:
        return value <= threshold
    if operator is ComparisonOperator.LT:
        return value < threshold
    return False


def _missing_dimension(
    criterion: AcceptanceCriterion, inputs: CriterionInputs
) -> CriterionEvaluation | None:
    """三维各自「声明了但事实未知」的 fail-closed 点名（任一 ⇒ 返回判负）。"""
    if criterion.minimum_sources is None:
        return CriterionEvaluation(criterion.type, False, "minimum_sources not configured")
    if inputs.evidence_source_count is None:
        return CriterionEvaluation(criterion.type, False, "evidence source count unknown")
    if criterion.minimum_retrieved_sources is not None and inputs.retrieved_source_count is None:
        return CriterionEvaluation(criterion.type, False, "retrieved source count unknown")
    if criterion.minimum_tool_evidences is not None and inputs.tool_evidence_count is None:
        return CriterionEvaluation(criterion.type, False, "tool evidence count unknown")
    return None


def _dimension_failure(
    criterion: AcceptanceCriterion, inputs: CriterionInputs
) -> CriterionEvaluation | None:
    """三维各自「事实不足阈值」的判负（判词**点名缺的是哪一维**）。"""
    # 三者在 `_missing_dimension` 之后都非空；用局部名让下面的比较可读。
    count = inputs.evidence_source_count
    assert count is not None and criterion.minimum_sources is not None
    if count < criterion.minimum_sources:
        return CriterionEvaluation(
            criterion.type, False, f"{count} < {criterion.minimum_sources} sources"
        )
    if criterion.minimum_retrieved_sources is not None:
        retrieved = inputs.retrieved_source_count
        assert retrieved is not None
        if retrieved < criterion.minimum_retrieved_sources:
            return CriterionEvaluation(
                criterion.type,
                False,
                f"{retrieved} < {criterion.minimum_retrieved_sources} retrieved sources "
                f"({count} >= {criterion.minimum_sources} sources)",
            )
    if criterion.minimum_tool_evidences is not None:
        tools = inputs.tool_evidence_count
        assert tools is not None
        if tools < criterion.minimum_tool_evidences:
            return CriterionEvaluation(
                criterion.type,
                False,
                f"{tools} < {criterion.minimum_tool_evidences} tool evidences owned by this task "
                f"({count} >= {criterion.minimum_sources} sources); "
                "a cross-phase input is not a tool call",
            )
    return None


def _coverage_reason(criterion: AcceptanceCriterion, inputs: CriterionInputs) -> str:
    """通过时的判词：只拼**已声明**的维度（未声明的不出现在判词里）。"""
    parts = [f"{inputs.evidence_source_count} >= {criterion.minimum_sources} sources"]
    if criterion.minimum_retrieved_sources is not None:
        parts.append(
            f"{inputs.retrieved_source_count} >= {criterion.minimum_retrieved_sources} retrieved"
        )
    if criterion.minimum_tool_evidences is not None:
        parts.append(
            f"{inputs.tool_evidence_count} >= {criterion.minimum_tool_evidences} tool evidences"
        )
    return "; ".join(parts)


def _evaluate_evidence_coverage(
    criterion: AcceptanceCriterion, inputs: CriterionInputs, schema_check: SchemaCheck | None
) -> CriterionEvaluation:
    """覆盖判据：**计数**维（非自产来源数）＋可选的**性质**维 ＋可选的**工具**维。

    三个维度各自只在合约**显式声明**时生效，且**都要过**：

    * `minimum_sources` —— 被计的非自产来源数；
    * `minimum_retrieved_sources`（GOAL-011 EC-02）—— 其中性质为 `TrustLabel.RETRIEVED`
      的条数（由编排从 canonical 的 SourceRecord 判出，不采信调用方自称）；
    * `minimum_tool_evidences`（GOAL-20261020-090）—— **本任务自己的**工具证据条数
      （`Evidence.tool_refs` 非空）。它补的是前两维**结构上补不了**的那一格：跨相输入的
      `trust_label` 由**产出方**的声明推出（`producer_trust_label`），于是一个「声明了
      run_chain 但没有真的执行任何检索调用」的会话格也会被算成 `RETRIEVED` ⇒ 性质维
      可被一条与被测能力无关的跨相边满足（GOAL-089 `W-6`）。工具维只数带 `tool_refs`
      的证据（工具证据登记时必然带 provider/tool，跨相输入的为空）⇒ 它问的是
      「**本任务**真的调用过工具吗」，不能被间接满足。

    缺维度一律 fail-closed 判拒并**点名缺的是哪一维**，不给出一个含糊的 False。
    三段判定拆成三个小函数（规模门：本函数此前 59 行超过 50 行上限）。
    """
    missing = _missing_dimension(criterion, inputs)
    if missing is not None:
        return missing
    failure = _dimension_failure(criterion, inputs)
    if failure is not None:
        return failure
    return CriterionEvaluation(criterion.type, True, _coverage_reason(criterion, inputs))


def _evaluate_review_score(
    criterion: AcceptanceCriterion, inputs: CriterionInputs, schema_check: SchemaCheck | None
) -> CriterionEvaluation:
    if criterion.operator is None or criterion.threshold is None:
        return CriterionEvaluation(criterion.type, False, "operator/threshold not configured")
    score = inputs.review_score
    if score is None:
        return CriterionEvaluation(criterion.type, False, "review score unknown")
    passed = _compare(score, criterion.operator, criterion.threshold)
    reason = f"review score {score} {criterion.operator.value} {criterion.threshold}"
    return CriterionEvaluation(criterion.type, passed, reason)


def _evaluate_policy_compliant(
    criterion: AcceptanceCriterion, inputs: CriterionInputs, schema_check: SchemaCheck | None
) -> CriterionEvaluation:
    decision = inputs.policy_decision
    if decision is None:
        return CriterionEvaluation(criterion.type, False, "policy decision unknown")
    if decision is PolicyDecision.ALLOW or decision is PolicyDecision.ALLOW_WITH_CONSTRAINTS:
        return CriterionEvaluation(criterion.type, True, f"policy decision {decision.value}")
    return CriterionEvaluation(criterion.type, False, f"policy decision {decision.value}")


def _evaluate_human_approval(
    criterion: AcceptanceCriterion, inputs: CriterionInputs, schema_check: SchemaCheck | None
) -> CriterionEvaluation:
    if inputs.human_approved is None:
        return CriterionEvaluation(criterion.type, False, "human approval unknown")
    if inputs.human_approved:
        return CriterionEvaluation(criterion.type, True, "human approved")
    return CriterionEvaluation(criterion.type, False, "human did not approve")


def _evaluate_custom_evaluator(
    criterion: AcceptanceCriterion, inputs: CriterionInputs, schema_check: SchemaCheck | None
) -> CriterionEvaluation:
    if not criterion.evaluator:
        return CriterionEvaluation(criterion.type, False, "evaluator id not configured")
    return CriterionEvaluation(
        criterion.type,
        False,
        f"custom evaluator {criterion.evaluator} must be executed by the orchestration layer",
    )


_EVALUATORS: dict[AcceptanceCriterionType, Evaluator] = {
    AcceptanceCriterionType.SCHEMA_VALID: _evaluate_schema_valid,
    AcceptanceCriterionType.ARTIFACT_EXISTS: _evaluate_artifact_exists,
    AcceptanceCriterionType.TEST_PASSES: _evaluate_test_passes,
    AcceptanceCriterionType.METRIC_THRESHOLD: _evaluate_metric_threshold,
    AcceptanceCriterionType.EVIDENCE_COVERAGE: _evaluate_evidence_coverage,
    AcceptanceCriterionType.REVIEW_SCORE: _evaluate_review_score,
    AcceptanceCriterionType.POLICY_COMPLIANT: _evaluate_policy_compliant,
    AcceptanceCriterionType.HUMAN_APPROVAL: _evaluate_human_approval,
    AcceptanceCriterionType.CUSTOM_EVALUATOR: _evaluate_custom_evaluator,
}
