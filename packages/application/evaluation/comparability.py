"""Field-level M15 evaluation comparability derived from validated indexes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from packages.application.ports.eval_report_store import EvalReportIndexEntry


class ComparabilityVerdict(StrEnum):
    """Closed explanation for why two reports can or cannot be compared."""

    COMPARABLE = "COMPARABLE"
    CASE_SET_CHANGED = "CASE_SET_CHANGED"
    RUBRIC_CHANGED = "RUBRIC_CHANGED"
    DATASET_CHANGED = "DATASET_CHANGED"
    GATE_CONFIG_CHANGED = "GATE_CONFIG_CHANGED"
    SCORER_CHANGED = "SCORER_CHANGED"
    EVALUATOR_CHANGED = "EVALUATOR_CHANGED"
    SYSTEM_VERSION_CHANGED = "SYSTEM_VERSION_CHANGED"
    SEGMENTED = "SEGMENTED"
    INCOMPATIBLE_GENERATION = "INCOMPATIBLE_GENERATION"


@dataclass(frozen=True, slots=True)
class Comparability:
    """A deterministic comparability result; it never creates a quality verdict."""

    verdict: ComparabilityVerdict
    reason: str = ""


def comparability(
    baseline: EvalReportIndexEntry,
    candidate: EvalReportIndexEntry,
) -> Comparability:
    """Return the first meaningful field-level difference in stable priority order.

    Rubric and scorer checks intentionally precede dataset comparison because
    both are included in the dataset digest.  Without that precedence, a
    scorer-only change was mislabeled as a dataset change and its branch was
    unreachable in authentic reports.
    """
    if baseline.case_ids != candidate.case_ids:
        return _different(ComparabilityVerdict.CASE_SET_CHANGED, "case set")
    if _has_incompatible_generation(baseline, candidate):
        return Comparability(
            ComparabilityVerdict.INCOMPATIBLE_GENERATION,
            "identical report digests have different comparison digests",
        )
    if baseline.comparison_digest == candidate.comparison_digest:
        return _same_comparison(baseline, candidate)
    difference = _frozen_condition_difference(baseline, candidate)
    if difference is not None:
        return difference
    return _different(ComparabilityVerdict.SEGMENTED, "unexplained frozen-condition change")


def _same_comparison(
    baseline: EvalReportIndexEntry,
    candidate: EvalReportIndexEntry,
) -> Comparability:
    if baseline.evaluator_identities != candidate.evaluator_identities:
        return _different(ComparabilityVerdict.EVALUATOR_CHANGED, "evaluator identities")
    return Comparability(ComparabilityVerdict.COMPARABLE)


def _frozen_condition_difference(
    baseline: EvalReportIndexEntry,
    candidate: EvalReportIndexEntry,
) -> Comparability | None:
    differences = (
        (
            baseline.rubric_digest != candidate.rubric_digest,
            ComparabilityVerdict.RUBRIC_CHANGED,
            "rubric",
        ),
        (
            baseline.scorer_versions != candidate.scorer_versions,
            ComparabilityVerdict.SCORER_CHANGED,
            "scorer versions",
        ),
        (
            _gate_changed(baseline, candidate),
            ComparabilityVerdict.GATE_CONFIG_CHANGED,
            "gate config",
        ),
        (
            baseline.evaluator_identities != candidate.evaluator_identities,
            ComparabilityVerdict.EVALUATOR_CHANGED,
            "evaluator identities",
        ),
        (
            baseline.system_version != candidate.system_version,
            ComparabilityVerdict.SYSTEM_VERSION_CHANGED,
            "system version",
        ),
        (_dataset_changed(baseline, candidate), ComparabilityVerdict.DATASET_CHANGED, "dataset"),
    )
    for changed, verdict, field in differences:
        if changed:
            return _different(verdict, field)
    return None


def _has_incompatible_generation(
    baseline: EvalReportIndexEntry,
    candidate: EvalReportIndexEntry,
) -> bool:
    return (
        baseline.report_digest == candidate.report_digest
        and baseline.comparison_digest != candidate.comparison_digest
    )


def is_comparable(verdict: ComparabilityVerdict) -> bool:
    return verdict is ComparabilityVerdict.COMPARABLE


def _different(verdict: ComparabilityVerdict, field: str) -> Comparability:
    return Comparability(verdict, f"{field} differs between reports")


def _gate_changed(
    baseline: EvalReportIndexEntry,
    candidate: EvalReportIndexEntry,
) -> bool:
    return (
        baseline.gate_config_id != candidate.gate_config_id
        or baseline.gate_config_version != candidate.gate_config_version
        or baseline.gate_config_digest != candidate.gate_config_digest
    )


def _dataset_changed(
    baseline: EvalReportIndexEntry,
    candidate: EvalReportIndexEntry,
) -> bool:
    return (
        baseline.dataset_id != candidate.dataset_id
        or baseline.dataset_version != candidate.dataset_version
        or baseline.dataset_digest != candidate.dataset_digest
    )


__all__ = ["Comparability", "ComparabilityVerdict", "comparability", "is_comparable"]
