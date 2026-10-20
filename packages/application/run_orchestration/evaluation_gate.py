"""AcceptanceCriteria 评估门（Evaluation Gate）。

Research Runtime 不能自行认证成功（AGENTS.md §13、QUALITY_GATES.md）：
本模块把 TaskContract 的 AcceptanceCriteria 与独立输入事实求值，
产出 ReviewFinding/Decision；不依赖聊天记录或 Agent 自述。

- valid evidence → PASS；
- unsupported claim（无证据/证据不足）→ REJECT；
- failed acceptance criteria → REJECT（任务失败路径）。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from packages.application.ports.errors import InvalidInputError
from packages.application.run_orchestration.phase_input_material import declared_object
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
    #: **本任务自己的**工具证据条数（`Evidence.tool_refs` 非空，GOAL-20261020-090）。
    #: 由编排按证据条数算（`count_tool_evidences`）；与 `retrieved_source_count` 判的是
    #: **不同的面**（后者是来源性质、可由跨相输入的产出方声明推出；本项是调用事实）。
    #: 未知即 `None` ⇒ 声明了本维度的合约 fail-closed。
    tool_evidence_count: int | None = None
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
    #: GOAL-20261008-038 EC-03：`CUSTOM_EVALUATOR` 的**编排层求值结论**（按判据下标）。
    #: 由装配方在**求值点之前**算好（域层不执行外部求值器 —— 那是它的设计与既有判据）；
    #: 未注入 ⇒ 维持域层的既有判词「must be executed by the orchestration layer」。
    consumption: Mapping[int, Any] = field(default_factory=dict)

    def to_criterion_inputs(self) -> CriterionInputs:
        return CriterionInputs(
            structured_output=dict(self.structured_output),
            artifacts=dict(self.artifacts),
            tests=dict(self.tests),
            metrics=dict(self.metrics),
            evidence_source_count=self.evidence_source_count,
            retrieved_source_count=self.retrieved_source_count,
            tool_evidence_count=self.tool_evidence_count,
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

    **信封形态**（GOAL-20261020-091 EC-01）：真实会话的交付物是**信封** ——
    `{declared_artifact: {content: "<模型正文>", message_count: …}}`（见
    `adapters/openhands/runtime_adapter.py::_deliverable`）。模型自己写下的分数在
    **正文**里，不在顶层键下；只按顶层路径取值会让每一份真实评审都落进
    `review score unknown` ⇒ 两个评审模型无论各自判什么，判定面看到的都是同一个
    「不知道」——「评审真的用不同模型判出负」因此**结构不可达**。
    本函数在**路径的每一段**上先看它是不是信封，是则用**既有** `declared_object`
    的解包口径取出模型声明的那份对象，再继续走路径。

    解包**只**发生在信封的两个判别键同时成立时（`declared_artifact` 在场 + `content`
    是字符串）；解析不出 / 不是对象 ⇒ 走既有 fail-closed（**不**猜、**不**回落）。
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
            unwrapped = _unwrap_deliverable(value, key=part)
            if unwrapped is not None:
                value = unwrapped
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
            continue
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            continue
    return None


def _unwrap_deliverable(value: Any, *, key: str) -> Mapping[str, Any] | None:
    """一个值若是**交付物信封** ⇒ 模型声明的那份对象；否则 `None`（原样继续）。

    为什么复用 `phase_input_material.declared_object` 而不是在这里写第二份解包：两处问的是
    同一个问题（「模型正文里它声明的对象是哪个」），两份解析必然漂 —— 运行链参数材料与
    验收判据会给出不同的答案，而那种漂移在读数上表现为「分数在某些路径上取得到、
    在另一些路径上取不到」。**解不出来 ⇒ `None`**（信封判别键不在场 / 正文不是字符串 /
    正文里没有带该键的对象）⇒ 调用方保持既有 fail-closed。
    """
    if not isinstance(value, Mapping):
        return None
    if "declared_artifact" not in value or not isinstance(value.get("content"), str):
        return None
    try:
        declared = declared_object(value, key=key)
    except InvalidInputError:
        # 正文里没有带该键的对象 ⇒ 不可判 ⇒ 不猜（由调用方 fail-closed）。
        return None
    # 正文里的形状是 `{产物名: {...}}`（合约给的形状）；取**内层**，与
    # `phase_input_material.input_material` 的取法逐字一致（同一个解包口径，不双挂）。
    inner = declared.get(key)
    return inner if isinstance(inner, Mapping) else declared


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


def _apply_consumption(
    evaluations: Sequence[CriterionEvaluation],
    inputs: EvaluationInputs,
) -> list[CriterionEvaluation]:
    """把编排层的跨轮消费结论**贴回**判据下标（GOAL-20261008-038 EC-03）。

    **只在调用方给了结论时替换**（键 = 判据下标）：没给 ⇒ 域层的既有判词**逐字保留**
    （`must be executed by the orchestration layer`）—— 两条路径互不覆盖，既有判据不受影响。
    """
    if not inputs.consumption:
        return list(evaluations)
    updated: list[CriterionEvaluation] = []
    for index, evaluation in enumerate(evaluations):
        verdict = inputs.consumption.get(index)
        if verdict is None:
            updated.append(evaluation)
            continue
        updated.append(
            CriterionEvaluation(
                criterion_type=evaluation.criterion_type,
                passed=bool(verdict.passed),
                reason=str(verdict.reason),
            )
        )
    return updated


def evaluate_task_gate(
    task: ResearchTask,
    contract: TaskContract,
    inputs: EvaluationInputs,
    *,
    reviewer: str,
    reviewer_model: str | None = None,
) -> GateOutcome:
    """对一次任务的全部验收标准求值，产出 ReviewFinding 与 Decision。

    `schema_check` 随 `EvaluationInputs` 一起进来（GOAL-014 EC-02 / F-11 的四维之一）：
    它是**按合约声明的 `output_schema` 由装配方给出**的校验回调；未注入时域函数维持
    既有的 fail-closed 判词（`schema validator unavailable`）。

    `reviewer_model`（GOAL-20261018-085 EC-01）：评审者**跑在哪个模型上**的稳定串形
    （`endpoint/model_name`）。缺省 `None` = 调用方未声明该面 ⇒ 判词的 `reviewer_model`
    保持 `None`（既有调用点逐字不变）；记上模型**不等于**「独立」—— 独立性由
    `evaluation.panel_verdict.aggregate_panel` 按目标是否互异来判。
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
    evaluations = _apply_consumption(evaluations, effective)
    passed = contract_passes(evaluations)
    return _gate_outcome(
        task,
        evaluations,
        passed,
        GateAttribution(reviewer=reviewer, reviewer_model=reviewer_model),
    )


@dataclass(frozen=True, slots=True)
class GateAttribution:
    """**谁判的**：agent 实例 + 它跑在哪个模型上（GOAL-20261018-085 EC-01）。

    两者分开：`reviewer` 是既有语义（`gate:<agent id>`，逐字不变），`reviewer_model`
    是新增的**可归因到模型**那一格（`endpoint/model_name`，缺省 `None` = 未声明）。
    """

    reviewer: str
    reviewer_model: str | None = None


def _gate_outcome(
    task: ResearchTask,
    evaluations: Sequence[CriterionEvaluation],
    passed: bool,
    who: GateAttribution,
) -> GateOutcome:
    """把求值结果包成 `GateOutcome`（判词 + 裁决；两处构造集中在这里）。"""
    verdict = "PASS" if passed else "REJECT"
    finding = ReviewFinding(
        id=f"finding:{task.id.value}:gate",
        review_type="acceptance_gate",
        verdict=verdict,
        findings=[item.reason for item in evaluations],
        reviewed_by=who.reviewer,
        reviewed_at=Timestamp.now(),
        reviewer_model=who.reviewer_model,
    )
    decision = Decision(
        id=f"decision:{task.id.value}:gate",
        decision="APPROVE" if passed else "REJECT",
        rationale="; ".join(item.reason for item in evaluations),
        decided_by=who.reviewer,
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
