"""M15 trend + comparability 测试(DoD 13-16)。

- COMPARABLE 时才有回归;每个 ComparabilityVerdict 分支可触发;
- 回归判定来自 compare_reports(trend 不发明阈值);
- INFRA_ERROR 独立计数;missing evaluation 第三态;
- 改 dataset/gate/scorer/evaluator/system_version → 对应分歧。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from adapters.fakes.eval_report_store import FakeEvalReportStore
from packages.application.evaluation.comparability import (
    ComparabilityVerdict,
    comparability,
)
from packages.application.evaluation.eval_index import stored_from_report
from packages.application.evaluation.runner import (
    RunRequest,
    run_evaluation,
)
from packages.application.evaluation.trend import build_trend, missing_evaluations
from packages.application.ports.eval_report_store import EvalReportIndexEntry
from packages.domain.core import Version
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_result import EvalReport
from packages.domain.eval_spec import EvalCase, EvalDataset, EvalScope, ScorerRef

_T0 = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)


def _report(case_answer: int = 42, dataset_id: str = "m15-ds") -> EvalReport:
    dataset = EvalDataset(
        id=dataset_id,
        version=Version("1.0.0"),
        cases=(
            EvalCase(
                id="c1",
                version=Version("1.0.0"),
                scope=EvalScope.UNIT,
                input_ref="input://c1",
                expected={"answer": case_answer},
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
            inputs={"input://c1": {"answer": case_answer}},
        )
    ).report


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


def test_identical_conditions_are_comparable() -> None:
    store, entries = _store_with_reports(_report(), _report())
    pair = comparability(entries[0], entries[1])
    assert pair.verdict is ComparabilityVerdict.COMPARABLE
    trend = build_trend(tuple(entries), store)
    assert len(trend.segments) == 1
    assert len(trend.segments[0].points) == 2
    assert not trend.divergences


def test_same_answer_reports_have_no_regression_marker() -> None:
    store, entries = _store_with_reports(_report(), _report())
    trend = build_trend(tuple(entries), store)
    assert trend.segments[0].comparisons[0].verdict == "PASS"
    assert trend.segments[0].comparisons[0].newly_regressed == ()


def test_dataset_change_is_detected() -> None:
    _, entries = _store_with_reports(_report(), _report(dataset_id="other-ds"))
    pair = comparability(entries[0], entries[1])
    assert pair.verdict is ComparabilityVerdict.DATASET_CHANGED


def test_system_version_change_is_detected() -> None:
    first = _report()
    second = run_evaluation(
        RunRequest(
            dataset=replace(_dataset_of(first), cases=(_case_of(first),)),
            config=GateConfig(id="gate", version=Version("1.0.0")),
            mode="OFFLINE_FAKE",
            system_version="0.5.0",
            inputs={"input://c1": {"answer": 42}},
        )
    ).report
    store = FakeEvalReportStore()
    stored_a = stored_from_report(first, recorded_at=_T0)
    stored_b = stored_from_report(second, recorded_at=_T0 + timedelta(minutes=1))
    store.put(stored_a)
    store.put(stored_b)
    pair = comparability(stored_a.index, stored_b.index)
    assert pair.verdict is ComparabilityVerdict.SYSTEM_VERSION_CHANGED
    trend = build_trend((stored_a.index, stored_b.index), store)
    assert len(trend.segments) == 2
    assert trend.divergences[0].verdict is ComparabilityVerdict.SYSTEM_VERSION_CHANGED


def test_case_set_change_is_detected() -> None:
    first = _report()
    second_index = replace(first_index_of(first), case_ids=("c1", "c2"))
    pair = comparability(first_index_of(first), second_index)
    assert pair.verdict is ComparabilityVerdict.CASE_SET_CHANGED


def test_evaluator_change_is_detected() -> None:
    first = first_index_of(_report())
    second = replace(first, evaluator_identities=("reviewer-x",))
    assert comparability(first, second).verdict is ComparabilityVerdict.EVALUATOR_CHANGED


def test_missing_evaluation_is_distinct_third_state() -> None:
    _, entries = _store_with_reports(_report())
    present_digest = entries[0].report_digest
    missing = missing_evaluations((present_digest, "digest-absent"), tuple(entries))
    assert [point.report_digest for point in missing] == ["digest-absent"]
    assert all(point.missing for point in missing)
    assert missing[0].verdict == "MISSING_EVALUATION"


def test_infra_error_counts_carry_through_trend() -> None:
    report = _report()
    entry = first_index_of(report)
    patched = replace(
        entry,
        pass_count=0,
        fail_count=0,
        infra_error_count=entry.pass_count + entry.fail_count + entry.infra_error_count,
        verdict="INDETERMINATE",
    )
    assert patched.infra_error_count > 0
    point = build_trend((patched,), FakeEvalReportStore()).segments[0].points[0]
    assert point.infra_error_count == patched.infra_error_count


# --- helpers ---------------------------------------------------------------


def _dataset_of(report: EvalReport) -> EvalDataset:
    frozen = report.frozen_conditions
    return EvalDataset(
        id=frozen.dataset_id,
        version=Version(frozen.dataset_version.text),
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


def _case_of(report: EvalReport) -> EvalCase:
    _ = report
    return EvalCase(
        id="c1",
        version=Version("1.0.0"),
        scope=EvalScope.UNIT,
        input_ref="input://c1",
        expected={"answer": 42},
        scorer_refs=(ScorerRef("exact_match", Version("1.0.0")),),
    )


def first_index_of(report: EvalReport) -> EvalReportIndexEntry:
    return stored_from_report(report, recorded_at=_T0).index
