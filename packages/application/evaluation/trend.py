"""M15 评测趋势投影(WP3)。

- 仅当相邻两点 COMPARABLE 才计算回归;分歧处切段并携带 `ComparabilityVerdict`;
- 回归判定唯一来源是 M11 `compare_reports`(本层不发明阈值、不产 verdict);
- INFRA_ERROR 是独立计数,永不折算为分数、永不 PASS、永不丢弃;
- missing evaluation 是与 quality failure 不同的第三态(独立携带)。
输入只来自 EvalReportStore(报告正文经 store 反查),不改 FrozenConditions。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from packages.application.evaluation.comparability import (
    Comparability,
    ComparabilityVerdict,
    comparability,
)
from packages.application.evaluation.eval_index import decode_report_body
from packages.application.evaluation.regression import compare_reports
from packages.application.ports.eval_report_store import EvalReportIndexEntry, EvalReportStore

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

_MISSING_VERDICT = "MISSING_EVALUATION"


@dataclass(frozen=True, slots=True)
class TrendPoint:
    """序列上的一个评测数据点。"""

    report_digest: str
    recorded_at: datetime | None
    verdict: str
    pass_count: int = 0
    fail_count: int = 0
    infra_error_count: int = 0
    missing: bool = False


@dataclass(frozen=True, slots=True)
class RegressionMarker:
    """相邻可比点对的回归结论(来自 compare_reports,原文转述)。"""

    baseline_digest: str
    candidate_digest: str
    verdict: str
    newly_regressed: tuple[str, ...] = field(default_factory=tuple)
    newly_fixed: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class TrendSegment:
    """一段可比连续序列;比较只在段内进行。"""

    points: tuple[TrendPoint, ...]
    comparisons: tuple[RegressionMarker, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class TrendReport:
    """趋势投影:可比段 + 分歧边界 + 缺失评测点。"""

    segments: tuple[TrendSegment, ...]
    divergences: tuple[Comparability, ...] = field(default_factory=tuple)
    missing: tuple[TrendPoint, ...] = field(default_factory=tuple)


def _point_of(entry: EvalReportIndexEntry) -> TrendPoint:
    return TrendPoint(
        report_digest=entry.report_digest,
        recorded_at=entry.recorded_at,
        verdict=entry.verdict,
        pass_count=entry.pass_count,
        fail_count=entry.fail_count,
        infra_error_count=entry.infra_error_count,
    )


def _marker_between(
    store: EvalReportStore,
    baseline: EvalReportIndexEntry,
    candidate: EvalReportIndexEntry,
) -> RegressionMarker:
    """回归判定经 store 反查正文并交由 compare_reports(唯一权威)。"""
    baseline_body = store.get(baseline.report_digest)
    candidate_body = store.get(candidate.report_digest)
    if baseline_body is None or candidate_body is None:
        return RegressionMarker(
            baseline_digest=baseline.report_digest,
            candidate_digest=candidate.report_digest,
            verdict="INDETERMINATE",
        )
    comparison = compare_reports(
        decode_report_body(baseline_body.body),
        decode_report_body(candidate_body.body),
    )
    return RegressionMarker(
        baseline_digest=baseline.report_digest,
        candidate_digest=candidate.report_digest,
        verdict=comparison.verdict.value,
        newly_regressed=comparison.newly_regressed,
        newly_fixed=comparison.newly_fixed,
    )


def build_trend(
    entries: tuple[EvalReportIndexEntry, ...],
    store: EvalReportStore,
) -> TrendReport:
    """索引条目 → 分段趋势(确定性:按 recorded_at, report_digest 排序)。"""
    ordered = sorted(entries, key=lambda entry: (entry.recorded_at or _EPOCH, entry.report_digest))
    segments: list[TrendSegment] = []
    divergences: list[Comparability] = []
    current_points: list[TrendPoint] = []
    current_comparisons: list[RegressionMarker] = []
    previous: EvalReportIndexEntry | None = None
    for entry in ordered:
        if previous is not None:
            pair = comparability(previous, entry)
            if pair.verdict is not ComparabilityVerdict.COMPARABLE:
                segments.append(
                    TrendSegment(
                        points=tuple(current_points), comparisons=tuple(current_comparisons)
                    )
                )
                divergences.append(pair)
                current_points = []
                current_comparisons = []
            else:
                current_comparisons.append(_marker_between(store, previous, entry))
        current_points.append(_point_of(entry))
        previous = entry
    if current_points:
        segments.append(
            TrendSegment(points=tuple(current_points), comparisons=tuple(current_comparisons))
        )
    return TrendReport(segments=tuple(segments), divergences=tuple(divergences))


def missing_evaluations(
    expected_digests: tuple[str, ...],
    entries: tuple[EvalReportIndexEntry, ...],
) -> tuple[TrendPoint, ...]:
    """期望存在但未存储的评测 → 第三态数据点(与 quality failure 区分)。"""
    present = {entry.report_digest for entry in entries}
    return tuple(
        TrendPoint(
            report_digest=digest,
            recorded_at=None,
            verdict=_MISSING_VERDICT,
            missing=True,
        )
        for digest in expected_digests
        if digest not in present
    )


__all__ = [
    "RegressionMarker",
    "TrendPoint",
    "TrendReport",
    "TrendSegment",
    "build_trend",
    "missing_evaluations",
]
