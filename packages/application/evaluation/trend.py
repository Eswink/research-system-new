"""Validated EvalReport trend projection for M15 operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from packages.application.evaluation.comparability import (
    Comparability,
    ComparabilityVerdict,
    comparability,
)
from packages.application.evaluation.eval_index import decode_report_body, index_matches_body
from packages.application.evaluation.regression import compare_reports
from packages.application.ports.eval_report_store import EvalReportIndexEntry, EvalReportStore

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_MISSING_VERDICT = "MISSING_EVALUATION"
_INDETERMINATE_VERDICT = "INDETERMINATE"


@dataclass(frozen=True, slots=True)
class TrendPoint:
    """A report point with its report-body integrity state."""

    report_digest: str
    recorded_at: datetime | None
    verdict: str
    dataset_id: str | None = None
    dataset_version: str | None = None
    dataset_digest: str | None = None
    gate_config_id: str | None = None
    gate_config_version: str | None = None
    gate_config_digest: str | None = None
    system_version: str | None = None
    comparison_digest: str | None = None
    run_id: str | None = None
    pass_count: int = 0
    fail_count: int = 0
    infra_error_count: int = 0
    reviewer_failure_count: int = 0
    missing: bool = False
    integrity_error: str | None = None


@dataclass(frozen=True, slots=True)
class RegressionMarker:
    """Adjacent comparable report result, sourced only from M11 comparison."""

    baseline_digest: str
    candidate_digest: str
    verdict: str
    newly_regressed: tuple[str, ...] = field(default_factory=tuple)
    newly_fixed: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class TrendSegment:
    """A contiguous sequence in which adjacent report bodies are comparable."""

    points: tuple[TrendPoint, ...]
    comparisons: tuple[RegressionMarker, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class TrendReport:
    """Trend projection with divergence reasons and third-state missing reports."""

    segments: tuple[TrendSegment, ...]
    divergences: tuple[Comparability, ...] = field(default_factory=tuple)
    missing: tuple[TrendPoint, ...] = field(default_factory=tuple)


def build_trend(
    entries: tuple[EvalReportIndexEntry, ...],
    store: EvalReportStore,
    *,
    expected_digests: tuple[str, ...] = (),
) -> TrendReport:
    """Build chronological comparable segments from a bounded newest-first query."""
    ordered = sorted(entries, key=lambda item: (item.recorded_at or _EPOCH, item.report_digest))
    segments: list[TrendSegment] = []
    divergences: list[Comparability] = []
    current_points: list[TrendPoint] = []
    current_markers: list[RegressionMarker] = []
    previous: EvalReportIndexEntry | None = None

    for entry in ordered:
        point = _point_of(store, entry)
        if point.integrity_error is not None:
            _append_segment(segments, current_points, current_markers)
            current_points = []
            current_markers = []
            segments.append(TrendSegment(points=(point,)))
            divergences.append(
                Comparability(ComparabilityVerdict.INCOMPATIBLE_GENERATION, point.integrity_error)
            )
            previous = None
            continue
        if previous is not None:
            pair = comparability(previous, entry)
            if pair.verdict is ComparabilityVerdict.COMPARABLE:
                current_markers.append(_marker_between(store, previous, entry))
            else:
                _append_segment(segments, current_points, current_markers)
                divergences.append(pair)
                current_points = []
                current_markers = []
        current_points.append(point)
        previous = entry
    _append_segment(segments, current_points, current_markers)
    return TrendReport(
        segments=tuple(segments),
        divergences=tuple(divergences),
        missing=_missing_from_store(expected_digests, entries, store),
    )


def _missing_from_store(
    expected_digests: tuple[str, ...],
    entries: tuple[EvalReportIndexEntry, ...],
    store: EvalReportStore,
) -> tuple[TrendPoint, ...]:
    """Distinguish absent reports from reports hidden by a bounded query window."""
    present = {entry.report_digest for entry in entries}
    missing = tuple(
        digest for digest in expected_digests if digest not in present and store.get(digest) is None
    )
    return _missing_points(missing)


def _missing_points(digests: tuple[str, ...]) -> tuple[TrendPoint, ...]:
    return tuple(
        TrendPoint(
            report_digest=digest,
            recorded_at=None,
            verdict=_MISSING_VERDICT,
            missing=True,
        )
        for digest in digests
    )


def missing_evaluations(
    expected_digests: tuple[str, ...],
    entries: tuple[EvalReportIndexEntry, ...],
) -> tuple[TrendPoint, ...]:
    """Return expected reports absent from the store as a third, non-quality state."""
    present = {entry.report_digest for entry in entries}
    return _missing_points(tuple(digest for digest in expected_digests if digest not in present))


def _point_of(store: EvalReportStore, entry: EvalReportIndexEntry) -> TrendPoint:
    """Cross-check body and index before publishing a verdict or count."""
    stored = store.get(entry.report_digest)
    if stored is None:
        return _indeterminate(entry, "canonical report body is unavailable")
    try:
        report = decode_report_body(stored.body)
    except (UnicodeDecodeError, ValueError):
        return _indeterminate(entry, "canonical report body is invalid")
    if not index_matches_body(entry, report):
        return _indeterminate(entry, "derived index does not match canonical report body")
    return TrendPoint(
        report_digest=entry.report_digest,
        recorded_at=entry.recorded_at,
        verdict=entry.verdict.value,
        dataset_id=entry.dataset_id,
        dataset_version=entry.dataset_version,
        dataset_digest=entry.dataset_digest,
        gate_config_id=entry.gate_config_id,
        gate_config_version=entry.gate_config_version,
        gate_config_digest=entry.gate_config_digest,
        system_version=entry.system_version,
        comparison_digest=entry.comparison_digest,
        run_id=entry.run_id,
        pass_count=entry.pass_count,
        fail_count=entry.fail_count,
        infra_error_count=entry.infra_error_count,
        reviewer_failure_count=entry.reviewer_failure_count,
    )


def _marker_between(
    store: EvalReportStore,
    baseline: EvalReportIndexEntry,
    candidate: EvalReportIndexEntry,
) -> RegressionMarker:
    """Use M11 ``compare_reports`` for the only regression verdict authority."""
    baseline_body = store.get(baseline.report_digest)
    candidate_body = store.get(candidate.report_digest)
    if baseline_body is None or candidate_body is None:
        return _indeterminate_marker(baseline, candidate)
    try:
        comparison = compare_reports(
            decode_report_body(baseline_body.body),
            decode_report_body(candidate_body.body),
        )
    except (UnicodeDecodeError, ValueError):
        return _indeterminate_marker(baseline, candidate)
    return RegressionMarker(
        baseline_digest=baseline.report_digest,
        candidate_digest=candidate.report_digest,
        verdict=comparison.verdict.value,
        newly_regressed=comparison.newly_regressed,
        newly_fixed=comparison.newly_fixed,
    )


def _append_segment(
    segments: list[TrendSegment],
    points: list[TrendPoint],
    markers: list[RegressionMarker],
) -> None:
    if points:
        segments.append(TrendSegment(points=tuple(points), comparisons=tuple(markers)))


def _indeterminate(entry: EvalReportIndexEntry, reason: str) -> TrendPoint:
    return TrendPoint(
        report_digest=entry.report_digest,
        recorded_at=entry.recorded_at,
        verdict=_INDETERMINATE_VERDICT,
        dataset_id=entry.dataset_id,
        dataset_version=entry.dataset_version,
        dataset_digest=entry.dataset_digest,
        gate_config_id=entry.gate_config_id,
        gate_config_version=entry.gate_config_version,
        gate_config_digest=entry.gate_config_digest,
        system_version=entry.system_version,
        comparison_digest=entry.comparison_digest,
        run_id=entry.run_id,
        integrity_error=reason,
    )


def _indeterminate_marker(
    baseline: EvalReportIndexEntry,
    candidate: EvalReportIndexEntry,
) -> RegressionMarker:
    return RegressionMarker(
        baseline_digest=baseline.report_digest,
        candidate_digest=candidate.report_digest,
        verdict=_INDETERMINATE_VERDICT,
    )


__all__ = [
    "RegressionMarker",
    "TrendPoint",
    "TrendReport",
    "TrendSegment",
    "build_trend",
    "missing_evaluations",
]
