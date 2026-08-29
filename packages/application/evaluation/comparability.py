"""M15 comparability:两个 eval 报告索引的字段级可比性判定(WP3)。

闭集 `ComparabilityVerdict`;由两个字段级 diff 派生,比 compare_reports 的
两理由拒绝更细粒度,但 COMPARABLE/不可比 的判定与 `compare_reports` 一致
(case 集合相同 + comparison_digest 相同 ⇔ COMPARABLE)。
判定纯函数,不修改 FrozenConditions,不发明阈值。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from packages.application.ports.eval_report_store import EvalReportIndexEntry


class ComparabilityVerdict(StrEnum):
    COMPARABLE = "COMPARABLE"
    CASE_SET_CHANGED = "CASE_SET_CHANGED"
    DATASET_CHANGED = "DATASET_CHANGED"
    GATE_CONFIG_CHANGED = "GATE_CONFIG_CHANGED"
    SCORER_CHANGED = "SCORER_CHANGED"
    EVALUATOR_CHANGED = "EVALUATOR_CHANGED"
    SYSTEM_VERSION_CHANGED = "SYSTEM_VERSION_CHANGED"
    SEGMENTED = "SEGMENTED"
    INCOMPATIBLE_GENERATION = "INCOMPATIBLE_GENERATION"


@dataclass(frozen=True, slots=True)
class Comparability:
    """一对报告的可比性:verdict + 人读 reason(仅描述,不含内容)。"""

    verdict: ComparabilityVerdict
    reason: str = ""


def _reason(field: str) -> str:
    return f"{field} differs between reports"


def comparability(
    baseline: EvalReportIndexEntry,
    candidate: EvalReportIndexEntry,
) -> Comparability:
    """字段级 diff → ComparabilityVerdict;单一最早分歧(确定性)。

    COMPARABLE ⇔ 与 `compare_reports` 同判定:case 集合相同 +
    comparison_digest 相同(且 evaluator 身份一致)。
    已知限制:rubric 文本折叠进 dataset_digest → 仅 rubric 变化也表现为
    DATASET_CHANGED,除非拿到 dataset 做更细 diff(如实声明,见 trend.py)。
    """
    if baseline.case_ids != candidate.case_ids:
        return Comparability(ComparabilityVerdict.CASE_SET_CHANGED, _reason("case set"))
    if baseline.comparison_digest == candidate.comparison_digest:
        if baseline.evaluator_identities != candidate.evaluator_identities:
            # comparison_digest 不含 evaluator 身份;evaluator 变化单独暴露
            return Comparability(
                ComparabilityVerdict.EVALUATOR_CHANGED,
                _reason("evaluator identities"),
            )
        return Comparability(ComparabilityVerdict.COMPARABLE)
    if (
        baseline.dataset_id != candidate.dataset_id
        or baseline.dataset_version != candidate.dataset_version
        or baseline.dataset_digest != candidate.dataset_digest
    ):
        return Comparability(ComparabilityVerdict.DATASET_CHANGED, _reason("dataset"))
    if (
        baseline.gate_config_id != candidate.gate_config_id
        or baseline.gate_config_version != candidate.gate_config_version
        or baseline.gate_config_digest != candidate.gate_config_digest
    ):
        return Comparability(ComparabilityVerdict.GATE_CONFIG_CHANGED, _reason("gate config"))
    if baseline.scorer_versions != candidate.scorer_versions:
        return Comparability(ComparabilityVerdict.SCORER_CHANGED, _reason("scorer_versions"))
    if baseline.system_version != candidate.system_version:
        return Comparability(
            ComparabilityVerdict.SYSTEM_VERSION_CHANGED,
            _reason("system_version"),
        )
    if baseline.report_digest == candidate.report_digest:
        return Comparability(
            ComparabilityVerdict.INCOMPATIBLE_GENERATION,
            "identical report digests with divergent comparison digests",
        )
    return Comparability(ComparabilityVerdict.SEGMENTED, _reason("comparison digest"))


def is_comparable(verdict: ComparabilityVerdict) -> bool:
    return verdict is ComparabilityVerdict.COMPARABLE


__all__ = [
    "Comparability",
    "ComparabilityVerdict",
    "comparability",
    "is_comparable",
]
