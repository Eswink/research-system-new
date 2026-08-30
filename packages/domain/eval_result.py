"""M11 Evaluation Plane 评测结果域契约（frozen、stdlib-only）。

来源（权威）：docs/roadmap/MILESTONES.md M11 DoD（"这个分数是在什么冻结
条件下产生的"）、docs/architecture/EVALUATION.md、
docs/evaluation/QUALITY_GATES.md。
约束：
- EvalResult 必须保留计算依据（case/输入/scorer/reviewer/frozen
  conditions），不得只保存 PASS 或分数；
- Reviewer finding 是 Evaluation Plane 的判断来源，不是 Research truth
  变更（Reviewer Is Not Truth Owner）；
- 确定性评测的 EvalReport digest 必须 byte-identical：report_id 与
  generated_at 不参与 digest；
- 被评对象输出中自报的 score/PASS 不得进入本契约（由 runner 保证）。
报告编解码（report_to_dict/report_from_dict）在
eval_report_codec.py（独立模块以保持单文件行数阈值；EvalReport.digest
对其延迟 import，属模块内受控循环，运行时单向安全）。
本模块不 import application/adapter 或第三方类型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Mapping

from packages.domain.core import Digest, Version
from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_spec import EvalScope
from packages.domain.serialization import digest_of

EVAL_REPORT_FORMAT = "eval_report.v1"


class EvalFindingStatus(StrEnum):
    """scorer finding 状态；INFRA_ERROR 区分评测设施故障与被评对象不合格。"""

    PASS = "PASS"
    FAIL = "FAIL"
    INFRA_ERROR = "INFRA_ERROR"


class ReviewerVerdict(StrEnum):
    """Reviewer 对单个 rubric 维度的判断。"""

    PASS = "PASS"
    FAIL = "FAIL"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class ScorerFinding:
    """确定性 scorer 的结构化 finding；不修改被评对象。"""

    scorer_id: str
    scorer_version: Version
    case_id: str
    status: EvalFindingStatus
    detail: str
    value: object | None = None


@dataclass(frozen=True, slots=True)
class ReviewerFinding:
    """Reviewer 判断记录；failure 非空表示评测设施失败而非被评对象不合格。"""

    reviewer_id: str
    model_identity: str
    rubric_id: str
    verdict: ReviewerVerdict
    rationale: str = ""
    score: Decimal | None = None
    failure: str | None = None
    temperature: str | None = None
    repetitions: int = 1


@dataclass(frozen=True, slots=True)
class FrozenConditions:
    """评测冻结条件：回答"这个分数是在什么冻结条件下产生的"。"""

    dataset_id: str
    dataset_version: Version
    dataset_digest: Digest
    gate_config_id: str
    gate_config_version: Version
    gate_config_digest: Digest
    system_version: str
    scorer_versions: Mapping[str, str]
    input_digests: Mapping[str, str]
    rubric_digest: Digest | None = None

    def digest(self) -> Digest:
        payload = {
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version.text,
            "dataset_digest": str(self.dataset_digest),
            "gate_config_id": self.gate_config_id,
            "gate_config_version": self.gate_config_version.text,
            "gate_config_digest": str(self.gate_config_digest),
            "system_version": self.system_version,
            "scorer_versions": dict(self.scorer_versions),
            "input_digests": dict(self.input_digests),
            "rubric_digest": str(self.rubric_digest) if self.rubric_digest else None,
        }
        return digest_of(payload)

    def comparison_digest(self) -> Digest:
        """回归比较键：评测配置冻结条件（不含被评输入 digest）。

        before/after 比较的本质是"同一评测配置 + 不同被评输入"；
        输入变化不改变比较键，dataset/gate/scorer/system 变化则拒绝比较。
        """

        payload = {
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version.text,
            "dataset_digest": str(self.dataset_digest),
            "gate_config_id": self.gate_config_id,
            "gate_config_version": self.gate_config_version.text,
            "gate_config_digest": str(self.gate_config_digest),
            "system_version": self.system_version,
            "scorer_versions": dict(self.scorer_versions),
            "rubric_digest": str(self.rubric_digest) if self.rubric_digest else None,
        }
        return digest_of(payload)


@dataclass(frozen=True, slots=True)
class EvalResult:
    """单个 case 的评测结果：输入引用 + 全部 finding。"""

    case_id: str
    case_version: Version
    case_digest: Digest
    scope: EvalScope
    input_ref: str
    scorer_findings: tuple[ScorerFinding, ...]
    reviewer_findings: tuple[ReviewerFinding, ...] = ()
    usage: Mapping[str, object] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """fail-closed：无 scorer finding 或任一非 PASS 均不通过。"""

        return bool(self.scorer_findings) and all(
            item.status is EvalFindingStatus.PASS for item in self.scorer_findings
        )


@dataclass(frozen=True, slots=True)
class EvalScore:
    """聚合分数；只用于排序/可视化，不替代 gate verdict。"""

    passed_cases: int
    failed_cases: int
    infra_error_cases: int
    total_cases: int

    @property
    def pass_ratio(self) -> Decimal:
        if self.total_cases == 0:
            return Decimal("0")
        return Decimal(self.passed_cases) / Decimal(self.total_cases)


def eval_score_of(results: tuple[EvalResult, ...] | list[EvalResult]) -> EvalScore:
    """从结果集聚合 EvalScore（INFRA_ERROR 独立计数，不参与 pass_ratio）。"""

    passed = 0
    failed = 0
    infra = 0
    for result in results:
        statuses = [item.status for item in result.scorer_findings]
        if not statuses:
            infra += 1
        elif all(status is EvalFindingStatus.PASS for status in statuses):
            passed += 1
        elif any(status is EvalFindingStatus.INFRA_ERROR for status in statuses):
            infra += 1
        else:
            failed += 1
    return EvalScore(
        passed_cases=passed,
        failed_cases=failed,
        infra_error_cases=infra,
        total_cases=passed + failed,
    )


@dataclass(frozen=True, slots=True)
class EvalReport:
    """一次评测运行的完整报告；digest 即 replay 身份。"""

    report_id: str
    generated_at: str
    mode: str
    scope: EvalScope
    gate_verdict: QualityGateVerdict
    frozen_conditions: FrozenConditions
    results: tuple[EvalResult, ...]

    def digest(self) -> Digest:
        # 受控循环：codec 依赖本模块类型；digest 实现归属 codec。
        from packages.domain.eval_report_codec import report_digest

        return report_digest(self)
