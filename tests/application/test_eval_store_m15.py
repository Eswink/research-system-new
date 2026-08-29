"""M15 eval index + store 测试:rebuild-from-bodies、索引派生、查询语义。"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from adapters.fakes.eval_report_store import FakeEvalReportStore
from adapters.sqlite.eval_report_store import SqliteEvalReportStore
from packages.application.evaluation.eval_index import (
    build_index_entry,
    decode_report_body,
    stored_from_report,
)
from packages.application.evaluation.runner import RunRequest, run_evaluation
from packages.application.ports.eval_report_store import EvalReportQuery
from packages.domain.core import Version
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_result import EvalFindingStatus, EvalReport
from packages.domain.eval_spec import EvalCase, EvalDataset, EvalScope, ScorerRef

_RECORDED = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)


def _report() -> EvalReport:
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
            inputs={"input://c1": {"answer": 42}},
        )
    ).report


def test_index_entry_is_derived_from_body() -> None:
    report = _report()
    index = build_index_entry(report, run_id="run-1", recorded_at=_RECORDED)
    assert index.report_digest == str(report.digest())
    assert index.comparison_digest == str(report.frozen_conditions.comparison_digest())
    assert index.dataset_id == "m15-ds"
    assert index.gate_config_id == "gate"
    assert index.system_version == "0.4.0"
    assert index.verdict == report.gate_verdict.value
    assert index.run_id == "run-1"
    total = index.pass_count + index.fail_count + index.infra_error_count
    expected_findings = sum(len(r.scorer_findings) for r in report.results)
    assert total == expected_findings


def test_body_roundtrip_verifies_digest() -> None:
    report = _report()
    stored = stored_from_report(report, run_id="run-1", recorded_at=_RECORDED)
    rebuilt = decode_report_body(stored.body)
    assert rebuilt.digest() == report.digest()
    assert json.loads(stored.body.decode("utf-8"))["gate_verdict"] == report.gate_verdict.value


def _put_report(store: object) -> str:
    stored = stored_from_report(_report(), run_id="run-1", recorded_at=_RECORDED)
    store.put(stored)  # type: ignore[attr-defined]
    return stored.index.report_digest


def test_sqlite_store_put_get_query_and_rebuild() -> None:
    store = SqliteEvalReportStore(":memory:")
    digest = _put_report(store)
    fetched = store.get(digest)
    assert fetched is not None
    rebuilt = decode_report_body(fetched.body)
    assert str(rebuilt.digest()) == digest
    assert build_index_entry(rebuilt, run_id="run-1", recorded_at=_RECORDED) == fetched.index
    entries = store.query(EvalReportQuery(dataset_id="m15-ds"))
    assert len(entries) == 1
    assert entries[0].report_digest == digest
    assert store.query(EvalReportQuery(run_id="other")) == ()


def test_fake_store_put_is_idempotent() -> None:
    store = FakeEvalReportStore()
    digest = _put_report(store)
    digest_again = _put_report(store)
    assert digest == digest_again
    assert len(store.query(EvalReportQuery())) == 1


def test_infra_error_counts_stay_distinct() -> None:
    """INFRA_ERROR 保留为独立计数(不折算 fail、不丢弃):计数完备性。"""
    report = _report()
    index = build_index_entry(report, recorded_at=_RECORDED)
    expected = sum(len(r.scorer_findings) for r in report.results)
    assert index.pass_count + index.fail_count + index.infra_error_count == expected
    for result in report.results:
        for finding in result.scorer_findings:
            if finding.status is EvalFindingStatus.INFRA_ERROR:
                assert index.infra_error_count >= 1
