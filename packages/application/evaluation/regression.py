"""M11 Regression 比较：baseline vs candidate 的 before/after 判定。

约束：
- 冻结条件不一致 → 拒绝比较（不得声称"同一 dataset 上通过"）；
- 只比较 aggregate score 会被掩盖的回归不得漏判：任一 per-case
  PASS→FAIL 记 newly_regressed，任一 newly_regressed 存在即 BLOCK；
- comparison 是纯函数，不修改 baseline/candidate 报告；
- 空报告 / 结果集不匹配（case 集合不同）拒绝比较。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_result import (
    EvalFindingStatus,
    EvalReport,
    EvalResult,
)
from packages.domain.serialization import digest_of


@dataclass(frozen=True, slots=True)
class RegressionComparison:
    """baseline → candidate 的结构化差异。"""

    comparable: bool
    verdict: QualityGateVerdict
    baseline_digest: str
    candidate_digest: str
    newly_regressed: tuple[str, ...]
    newly_fixed: tuple[str, ...]
    failure_set_baseline: tuple[str, ...]
    failure_set_candidate: tuple[str, ...]
    reason: str = ""

    @property
    def blocked(self) -> bool:
        return self.verdict is QualityGateVerdict.BLOCK


def compare_reports(
    baseline: EvalReport,
    candidate: EvalReport,
) -> RegressionComparison:
    """比较两份报告；case 集合或评测配置不一致 → 拒绝比较。"""

    baseline_cases = {item.case_id for item in baseline.results}
    candidate_cases = {item.case_id for item in candidate.results}
    if baseline_cases != candidate_cases:
        return _refusal(baseline, candidate, "case sets differ")
    baseline_config = baseline.frozen_conditions.comparison_digest()
    candidate_config = candidate.frozen_conditions.comparison_digest()
    if baseline_config != candidate_config:
        return _refusal(baseline, candidate, "frozen conditions differ")
    deltas = _deltas(baseline, candidate)
    if deltas.newly_regressed:
        verdict = QualityGateVerdict.BLOCK
    elif candidate.gate_verdict is QualityGateVerdict.PASS:
        verdict = QualityGateVerdict.PASS
    else:
        verdict = candidate.gate_verdict
    return RegressionComparison(
        comparable=True,
        verdict=verdict,
        baseline_digest=str(digest_of(baseline)),
        candidate_digest=str(digest_of(candidate)),
        newly_regressed=deltas.newly_regressed,
        newly_fixed=deltas.newly_fixed,
        failure_set_baseline=deltas.failure_set_baseline,
        failure_set_candidate=deltas.failure_set_candidate,
        reason="",
    )


@dataclass(frozen=True, slots=True)
class _Deltas:
    newly_regressed: tuple[str, ...]
    newly_fixed: tuple[str, ...]
    failure_set_baseline: tuple[str, ...]
    failure_set_candidate: tuple[str, ...]


def _deltas(baseline: EvalReport, candidate: EvalReport) -> _Deltas:
    baseline_status = _case_statuses(baseline.results)
    candidate_status = _case_statuses(candidate.results)

    def transitioned(from_status: str, to_status: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                case_id
                for case_id in candidate_status
                if candidate_status[case_id] == to_status
                and baseline_status[case_id] == from_status
            )
        )

    def failed(statuses: dict[str, str]) -> tuple[str, ...]:
        return tuple(sorted(case_id for case_id, status in statuses.items() if status == "FAIL"))

    return _Deltas(
        newly_regressed=transitioned("PASS", "FAIL"),
        newly_fixed=transitioned("FAIL", "PASS"),
        failure_set_baseline=failed(baseline_status),
        failure_set_candidate=failed(candidate_status),
    )


def _refusal(baseline: EvalReport, candidate: EvalReport, reason: str) -> RegressionComparison:
    return RegressionComparison(
        comparable=False,
        verdict=QualityGateVerdict.BLOCK,
        baseline_digest=str(digest_of(baseline)),
        candidate_digest=str(digest_of(candidate)),
        newly_regressed=(),
        newly_fixed=(),
        failure_set_baseline=(),
        failure_set_candidate=(),
        reason=reason,
    )


def _case_statuses(results: tuple[EvalResult, ...] | list[EvalResult]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for result in results:
        findings = result.scorer_findings
        if not findings:
            statuses[result.case_id] = "INFRA"
            continue
        if all(item.status is EvalFindingStatus.PASS for item in findings):
            statuses[result.case_id] = "PASS"
        elif any(item.status is EvalFindingStatus.INFRA_ERROR for item in findings):
            statuses[result.case_id] = "INFRA"
        else:
            statuses[result.case_id] = "FAIL"
    return statuses
