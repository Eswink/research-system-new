"""M15 trend and comparability regression tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from adapters.fakes.eval_report_store import FakeEvalReportStore
from packages.application.evaluation.comparability import (
    ComparabilityVerdict,
    comparability,
)
from packages.application.evaluation.eval_index import stored_from_report
from packages.application.evaluation.runner import RunRequest, run_evaluation
from packages.application.evaluation.trend import build_trend, missing_evaluations
from packages.application.ports.eval_report_store import EvalReportIndexEntry
from packages.domain.core import Version
from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_result import EvalReport, EvalResult, ReviewerFinding, ReviewerVerdict
from packages.domain.eval_spec import EvalCase, EvalDataset, EvalScope, RubricSpec, ScorerRef

_T0 = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)


@dataclass(frozen=True, slots=True)
class _ReportOptions:
    dataset_id: str = "m15-ds"
    config: GateConfig | None = None
    system_version: str = "0.4.0"
    scorer: ScorerRef | None = None
    rubric: tuple[RubricSpec, ...] = ()


def _report(
    answers: tuple[int, ...] = (42,),
    *,
    options: _ReportOptions = _ReportOptions(),
) -> EvalReport:
    scorer_ref = options.scorer or ScorerRef("exact_match", Version("1.0.0"))
    cases = tuple(
        EvalCase(
            id=f"c{index}",
            version=Version("1.0.0"),
            scope=EvalScope.UNIT,
            input_ref=f"input://c{index}",
            expected={"answer": answer},
            rubric=options.rubric,
            scorer_refs=(scorer_ref,),
        )
        for index, answer in enumerate(answers, start=1)
    )
    dataset = EvalDataset(id=options.dataset_id, version=Version("1.0.0"), cases=cases)
    inputs = {
        case.input_ref: {"answer": answer} for case, answer in zip(cases, answers, strict=True)
    }
    return run_evaluation(
        RunRequest(
            dataset=dataset,
            config=options.config or GateConfig(id="gate", version=Version("1.0.0")),
            mode="OFFLINE_FAKE",
            system_version=options.system_version,
            inputs=inputs,
        )
    ).report


def _report_without_input() -> EvalReport:
    dataset = EvalDataset(
        id="m15-ds",
        version=Version("1.0.0"),
        cases=(
            EvalCase(
                id="c1",
                version=Version("1.0.0"),
                scope=EvalScope.UNIT,
                input_ref="input://c1",
                expected={"answer": 42},
                scorer_refs=(ScorerRef("exact_match", Version("1.0.0")),),
            ),
        ),
    )
    return run_evaluation(
        RunRequest(
            dataset=dataset,
            config=GateConfig(id="gate", version=Version("1.0.0")),
            mode="OFFLINE_FAKE",
            system_version="0.4.0",
            inputs={},
        )
    ).report


def _report_with_reviewer(identity: str) -> EvalReport:
    report = _report()
    result = report.results[0]
    reviewed = EvalResult(
        case_id=result.case_id,
        case_version=result.case_version,
        case_digest=result.case_digest,
        scope=result.scope,
        input_ref=result.input_ref,
        scorer_findings=result.scorer_findings,
        reviewer_findings=(
            ReviewerFinding(
                reviewer_id=f"reviewer-{identity}",
                model_identity=identity,
                rubric_id="soundness",
                verdict=ReviewerVerdict.PASS,
            ),
        ),
        usage=result.usage,
    )
    return EvalReport(
        report_id=report.report_id,
        generated_at=report.generated_at,
        mode=report.mode,
        scope=report.scope,
        gate_verdict=report.gate_verdict,
        frozen_conditions=report.frozen_conditions,
        results=(reviewed,),
    )


def _store_with_reports(
    *reports: EvalReport,
) -> tuple[FakeEvalReportStore, tuple[EvalReportIndexEntry, ...]]:
    store = FakeEvalReportStore()
    entries: list[EvalReportIndexEntry] = []
    for index, report in enumerate(reports):
        stored = stored_from_report(report, recorded_at=_T0 + timedelta(minutes=index))
        store.put(stored)
        entries.append(stored.index)
    return store, tuple(entries)


def _synthetic_index(report_digest: str, comparison_digest: str) -> EvalReportIndexEntry:
    """Create an invalid derived index only for corruption-classification branches."""
    return EvalReportIndexEntry(
        report_digest=report_digest,
        comparison_digest=comparison_digest,
        dataset_id="dataset",
        dataset_version="1.0.0",
        dataset_digest="sha256:" + "d" * 64,
        gate_config_id="gate",
        gate_config_version="1.0.0",
        gate_config_digest="sha256:" + "g" * 64,
        scorer_versions=(("exact_match", "1.0.0"),),
        system_version="0.4.0",
        verdict=QualityGateVerdict.PASS,
        recorded_at=_T0,
        rubric_digest="sha256:" + "r" * 64,
        case_ids=("c1",),
    )


def _count_tampered_index(entry: EvalReportIndexEntry) -> EvalReportIndexEntry:
    """Represent a stored index corrupted outside the validated Port write path."""
    return EvalReportIndexEntry(
        report_digest=entry.report_digest,
        comparison_digest=entry.comparison_digest,
        dataset_id=entry.dataset_id,
        dataset_version=entry.dataset_version,
        dataset_digest=entry.dataset_digest,
        gate_config_id=entry.gate_config_id,
        gate_config_version=entry.gate_config_version,
        gate_config_digest=entry.gate_config_digest,
        scorer_versions=entry.scorer_versions,
        system_version=entry.system_version,
        verdict=entry.verdict,
        recorded_at=entry.recorded_at,
        rubric_digest=entry.rubric_digest,
        case_ids=entry.case_ids,
        evaluator_identities=entry.evaluator_identities,
        pass_count=entry.pass_count + 1,
        fail_count=entry.fail_count,
        infra_error_count=entry.infra_error_count,
        reviewer_failure_count=entry.reviewer_failure_count,
        usage_ref=entry.usage_ref,
        cost_ref=entry.cost_ref,
        run_id=entry.run_id,
    )


def test_identical_conditions_are_comparable() -> None:
    store, entries = _store_with_reports(_report(), _report())
    assert comparability(entries[0], entries[1]).verdict is ComparabilityVerdict.COMPARABLE
    trend = build_trend(entries, store)
    assert len(trend.segments) == 1
    assert len(trend.segments[0].points) == 2
    assert not trend.divergences


def test_same_answer_reports_have_no_regression_marker() -> None:
    store, entries = _store_with_reports(_report(), _report())
    trend = build_trend(entries, store)
    assert trend.segments[0].comparisons[0].verdict == "PASS"
    assert trend.segments[0].comparisons[0].newly_regressed == ()


def test_dataset_change_is_detected_from_real_report_bodies() -> None:
    _, entries = _store_with_reports(
        _report(),
        _report(options=_ReportOptions(dataset_id="other-ds")),
    )
    assert comparability(entries[0], entries[1]).verdict is ComparabilityVerdict.DATASET_CHANGED


def test_system_version_change_is_detected() -> None:
    store, entries = _store_with_reports(
        _report(),
        _report(options=_ReportOptions(system_version="0.5.0")),
    )
    assert (
        comparability(entries[0], entries[1]).verdict is ComparabilityVerdict.SYSTEM_VERSION_CHANGED
    )
    trend = build_trend(entries, store)
    assert len(trend.segments) == 2
    assert trend.divergences[0].verdict is ComparabilityVerdict.SYSTEM_VERSION_CHANGED


def test_case_set_change_is_detected_from_real_report_bodies() -> None:
    _, entries = _store_with_reports(_report((42,)), _report((42, 43)))
    assert comparability(entries[0], entries[1]).verdict is ComparabilityVerdict.CASE_SET_CHANGED


def test_evaluator_change_is_detected_from_real_report_bodies() -> None:
    _, entries = _store_with_reports(
        _report_with_reviewer("model-a"),
        _report_with_reviewer("model-b"),
    )
    assert comparability(entries[0], entries[1]).verdict is ComparabilityVerdict.EVALUATOR_CHANGED


def test_rubric_change_is_detected_from_real_report_bodies() -> None:
    first_rubric = (RubricSpec("soundness", "soundness", "first rubric"),)
    second_rubric = (RubricSpec("soundness", "soundness", "second rubric"),)
    _, entries = _store_with_reports(
        _report(options=_ReportOptions(rubric=first_rubric)),
        _report(options=_ReportOptions(rubric=second_rubric)),
    )
    assert comparability(entries[0], entries[1]).verdict is ComparabilityVerdict.RUBRIC_CHANGED


def test_scorer_change_is_detected_from_real_report_bodies() -> None:
    first = _report(options=_ReportOptions(scorer=ScorerRef("exact_match", Version("1.0.0"))))
    second = _report(options=_ReportOptions(scorer=ScorerRef("unknown_scorer", Version("2.0.0"))))
    _, entries = _store_with_reports(first, second)
    assert comparability(entries[0], entries[1]).verdict is ComparabilityVerdict.SCORER_CHANGED


def test_gate_config_change_is_detected_from_real_report_bodies() -> None:
    first = _report(options=_ReportOptions(config=GateConfig(id="gate", version=Version("1.0.0"))))
    second = _report(options=_ReportOptions(config=GateConfig(id="gate", version=Version("2.0.0"))))
    _, entries = _store_with_reports(first, second)
    assert comparability(entries[0], entries[1]).verdict is ComparabilityVerdict.GATE_CONFIG_CHANGED


def test_unexplained_generation_difference_is_segmented() -> None:
    baseline = _synthetic_index("sha256:" + "a" * 64, "sha256:" + "b" * 64)
    candidate = _synthetic_index("sha256:" + "c" * 64, "sha256:" + "d" * 64)
    assert comparability(baseline, candidate).verdict is ComparabilityVerdict.SEGMENTED


def test_same_report_digest_with_changed_comparison_is_incompatible_generation() -> None:
    report_digest = "sha256:" + "a" * 64
    baseline = _synthetic_index(report_digest, "sha256:" + "b" * 64)
    candidate = _synthetic_index(report_digest, "sha256:" + "c" * 64)
    assert (
        comparability(baseline, candidate).verdict is ComparabilityVerdict.INCOMPATIBLE_GENERATION
    )


def test_missing_evaluation_is_distinct_third_state() -> None:
    _, entries = _store_with_reports(_report())
    present_digest = entries[0].report_digest
    missing = missing_evaluations((present_digest, "digest-absent"), entries)
    assert [point.report_digest for point in missing] == ["digest-absent"]
    assert all(point.missing for point in missing)
    assert missing[0].verdict == "MISSING_EVALUATION"


def test_infra_error_counts_carry_through_trend() -> None:
    report = _report_without_input()
    store, entries = _store_with_reports(report)
    point = build_trend(entries, store).segments[0].points[0]
    assert point.infra_error_count == entries[0].infra_error_count == 1
    assert point.verdict == "REVISE"


def test_trend_rejects_index_body_count_mismatch() -> None:
    store, entries = _store_with_reports(_report())
    point = build_trend((_count_tampered_index(entries[0]),), store).segments[0].points[0]
    assert point.verdict == "INDETERMINATE"
    assert point.integrity_error is not None


def test_build_trend_marks_expected_digest_missing() -> None:
    store, entries = _store_with_reports(_report())
    missing = build_trend(
        entries,
        store,
        expected_digests=(entries[0].report_digest, "sha256:" + "f" * 64),
    ).missing
    assert [point.report_digest for point in missing] == ["sha256:" + "f" * 64]
    assert missing[0].missing is True
