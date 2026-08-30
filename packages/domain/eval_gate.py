"""M11 Quality Gate 配置域契约（frozen、stdlib-only）。

来源（权威）：docs/architecture/EVALUATION.md（Quality Gate 四值）、
docs/evaluation/QUALITY_GATES.md（Hard Invariant 失败必须 BLOCK）。
约束：
- threshold / hard-invariant 规则版本化且可 digest；阈值改变必须导致
  config digest 变化，不得伪装成同一基线；
- hard-invariant 规则不携带阈值（语义：该 scorer 必须全 PASS）；
- 同一 scorer 在 config 中最多出现一次；
- 评测设施故障（INFRA_ERROR）不得判为被评对象质量失败。
本模块不 import application/adapter 或第三方类型。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from packages.domain.core import Digest, Version
from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_result import (
    EvalFindingStatus,
    EvalResult,
    eval_score_of,
)
from packages.domain.serialization import digest_of

GATE_CONFIG_FORMAT = "eval_gate_config.v1"


@dataclass(frozen=True, slots=True)
class ThresholdRule:
    """针对单个 scorer 的阈值规则；无阈值 + hard_invariant 即硬门。"""

    scorer_id: str
    threshold: Decimal | None = None
    hard_invariant: bool = False

    def __post_init__(self) -> None:
        if not self.scorer_id.strip():
            raise ValueError("scorer_id must not be empty")
        if self.hard_invariant and self.threshold is not None:
            raise ValueError("hard invariant rules must not carry a threshold")
        if self.threshold is not None and not (Decimal("0") <= self.threshold <= Decimal("1")):
            raise ValueError(f"threshold out of range: {self.threshold}")


@dataclass(frozen=True, slots=True)
class GateConfig:
    """版本化评测门配置；digest 是回归比较的基线身份组成部分。"""

    id: str
    version: Version
    rules: tuple[ThresholdRule, ...] = ()
    min_pass_ratio: Decimal = Decimal("0")
    description: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("gate config id must not be empty")
        if not (Decimal("0") <= self.min_pass_ratio <= Decimal("1")):
            raise ValueError(f"min_pass_ratio out of range: {self.min_pass_ratio}")
        seen: set[str] = set()
        for rule in self.rules:
            if rule.scorer_id in seen:
                raise ValueError(f"duplicate rule for scorer {rule.scorer_id}")
            seen.add(rule.scorer_id)

    def digest(self) -> Digest:
        payload = {
            "format": GATE_CONFIG_FORMAT,
            "id": self.id,
            "version": self.version.text,
            "rules": [
                {
                    "scorer_id": rule.scorer_id,
                    "threshold": rule.threshold,
                    "hard_invariant": rule.hard_invariant,
                }
                for rule in self.rules
            ],
            "min_pass_ratio": self.min_pass_ratio,
        }
        return digest_of(payload)


def compute_verdict(config: GateConfig, results: tuple[EvalResult, ...]) -> QualityGateVerdict:
    """由 frozen config + 结果集求 gate verdict（纯函数，fail-closed）。

    语义（deterministic-first）：
    1. 任何确定性 FAIL finding → BLOCK（聚合分数/阈值不可掩盖失败）；
    2. 任何 INFRA_ERROR finding → REVISE（评测设施故障：不得认证 PASS，
       也不得判被评对象质量失败）；
    3. rule 引用与结果集一致性：rule 声明的 scorer 必须实际执行，否则
       REVISE（config/dataset 不匹配，fail-closed）；
    4. min_pass_ratio（PASS case 数 / 全部 case 数）不满足 → BLOCK；
    5. 其余 → PASS。
    threshold 规则进入 config digest 实现版本化；M11 不做软分聚合
    （reviewer score 聚合归 M15 eval operations 前不引入）。
    """

    if not results:
        return QualityGateVerdict.BLOCK
    if _has_fail(results):
        return QualityGateVerdict.BLOCK
    if _has_infra(results):
        return QualityGateVerdict.REVISE
    if _has_reviewer_failure(results):
        return QualityGateVerdict.REVISE
    statuses_by_scorer = _collect_statuses(results)
    for rule in config.rules:
        if rule.scorer_id not in statuses_by_scorer:
            return QualityGateVerdict.REVISE
    score = eval_score_of(results)
    if score.pass_ratio < config.min_pass_ratio:
        return QualityGateVerdict.BLOCK
    return QualityGateVerdict.PASS


def _collect_statuses(
    results: tuple[EvalResult, ...],
) -> dict[str, tuple[EvalFindingStatus, ...]]:
    collected: dict[str, list[EvalFindingStatus]] = {}
    for result in results:
        for finding in result.scorer_findings:
            collected.setdefault(finding.scorer_id, []).append(finding.status)
    return {key: tuple(values) for key, values in collected.items()}


def _has_fail(results: tuple[EvalResult, ...]) -> bool:
    return any(
        finding.status is EvalFindingStatus.FAIL
        for result in results
        for finding in result.scorer_findings
    )


def _has_infra(results: tuple[EvalResult, ...]) -> bool:
    return any(
        finding.status is EvalFindingStatus.INFRA_ERROR
        for result in results
        for finding in result.scorer_findings
    )


def _has_reviewer_failure(results: tuple[EvalResult, ...]) -> bool:
    return any(
        finding.failure is not None for result in results for finding in result.reviewer_findings
    )
