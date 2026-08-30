"""M15 EvalReportStore 回归：正文真相、索引派生与查询窗口语义。"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from adapters.fakes.eval_report_store import FakeEvalReportStore
from adapters.sqlite.eval_report_store import SqliteEvalReportStore
from packages.application.evaluation.eval_index import (
    build_index_entry,
    decode_report_body,
    stored_from_report,
)
from packages.application.evaluation.runner import RunRequest, run_evaluation
from packages.application.evaluation.trend import build_trend
from packages.application.ports.eval_report_store import EvalReportQuery, StoredEvalReport
from packages.domain.core import Version
from packages.domain.enums import QualityGateVerdict
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_result import (
    EvalReport,
    ReviewerFinding,
    ReviewerVerdict,
)
from packages.domain.eval_spec import EvalCase, EvalDataset, EvalScope, ScorerRef

_RECORDED = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)


def _report(case_answer: int = 42) -> EvalReport:
    dataset = EvalDataset(
        id="m15-ds",
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


def test_index_entry_is_derived_from_body() -> None:
    report = _report()
    index = build_index_entry(report, run_id="run-1", recorded_at=_RECORDED)
    assert index.report_digest == str(report.digest())
    assert index.comparison_digest == str(report.frozen_conditions.comparison_digest())
    assert index.dataset_id == "m15-ds"
    assert index.gate_config_id == "gate"
    assert index.system_version == "0.4.0"
    assert index.verdict is report.gate_verdict
    assert index.run_id == "run-1"
    total = index.pass_count + index.fail_count + index.infra_error_count
    expected_findings = sum(len(result.scorer_findings) for result in report.results)
    assert total == expected_findings


def test_body_roundtrip_verifies_digest() -> None:
    report = _report()
    stored = stored_from_report(report, run_id="run-1", recorded_at=_RECORDED)
    rebuilt = decode_report_body(stored.body)
    assert rebuilt.digest() == report.digest()
    assert json.loads(stored.body.decode("utf-8"))["gate_verdict"] == report.gate_verdict.value


def test_stored_report_rejects_body_digest_mismatch() -> None:
    stored = stored_from_report(_report(), recorded_at=_RECORDED)
    invalid_index = replace(stored.index, report_digest="sha256:" + "0" * 64)
    with pytest.raises(ValueError, match="digest"):
        StoredEvalReport(index=invalid_index, body=stored.body)


def test_stored_report_rejects_body_verdict_mismatch() -> None:
    stored = stored_from_report(_report(), recorded_at=_RECORDED)
    invalid_index = replace(stored.index, verdict=QualityGateVerdict.BLOCK)
    with pytest.raises(ValueError, match="verdict"):
        StoredEvalReport(index=invalid_index, body=stored.body)


def test_stored_report_rejects_non_bytes_body() -> None:
    stored = stored_from_report(_report(), recorded_at=_RECORDED)
    with pytest.raises(ValueError, match="body"):
        StoredEvalReport(index=stored.index, body="not-bytes")  # type: ignore[arg-type]


def test_sqlite_store_put_get_query_and_rebuild() -> None:
    store = SqliteEvalReportStore(":memory:")
    stored = stored_from_report(_report(), run_id="run-1", recorded_at=_RECORDED)
    store.put(stored)
    fetched = store.get(stored.index.report_digest)
    assert fetched is not None
    rebuilt = decode_report_body(fetched.body)
    assert str(rebuilt.digest()) == stored.index.report_digest
    assert build_index_entry(rebuilt, run_id="run-1", recorded_at=_RECORDED) == fetched.index
    assert store.query(EvalReportQuery(dataset_id="m15-ds")) == (stored.index,)
    assert store.query(EvalReportQuery(run_id="other")) == ()


def test_fake_store_put_is_idempotent() -> None:
    store = FakeEvalReportStore()
    stored = stored_from_report(_report(), run_id="run-1", recorded_at=_RECORDED)
    replacement = stored_from_report(
        _report(), run_id="run-1", recorded_at=_RECORDED + timedelta(days=1)
    )
    store.put(stored)
    store.put(replacement)
    assert store.get(stored.index.report_digest) == stored
    assert store.query(EvalReportQuery()) == (stored.index,)


def test_sqlite_duplicate_digest_preserves_first_timestamp() -> None:
    store = SqliteEvalReportStore(":memory:")
    first = stored_from_report(_report(), recorded_at=_RECORDED)
    second = stored_from_report(_report(), recorded_at=_RECORDED + timedelta(days=1))
    store.put(first)
    store.put(second)
    fetched = store.get(first.index.report_digest)
    assert fetched is not None
    assert fetched.index.recorded_at == _RECORDED


def test_sqlite_query_page_is_newest_first_and_reports_truncation() -> None:
    store = SqliteEvalReportStore(":memory:")
    first = stored_from_report(_report(), recorded_at=_RECORDED)
    second = stored_from_report(
        _report(case_answer=43),
        recorded_at=_RECORDED + timedelta(minutes=1),
    )
    store.put(first)
    store.put(second)
    page = store.query_page(EvalReportQuery(limit=1))
    assert page.truncated is True
    assert page.entries == (second.index,)


def test_sqlite_recorded_at_update_is_rejected() -> None:
    connection = sqlite3.connect(":memory:")
    store = SqliteEvalReportStore(connection)
    stored = stored_from_report(_report(), recorded_at=_RECORDED)
    store.put(stored)
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute(
            "UPDATE eval_reports SET recorded_at = ? WHERE report_digest = ?",
            ((_RECORDED + timedelta(days=1)).isoformat(), stored.index.report_digest),
        )


def test_reviewer_failure_count_is_projected_from_body() -> None:
    report = _report()
    reviewed_result = replace(
        report.results[0],
        reviewer_findings=(
            ReviewerFinding(
                reviewer_id="reviewer-1",
                model_identity="scripted-reviewer",
                rubric_id="soundness",
                verdict=ReviewerVerdict.AMBIGUOUS,
                failure="timeout",
            ),
        ),
    )
    reviewed = replace(
        report,
        gate_verdict=QualityGateVerdict.REVISE,
        results=(reviewed_result,),
    )
    stored = stored_from_report(reviewed, recorded_at=_RECORDED)
    assert stored.index.reviewer_failure_count == 1
    store = FakeEvalReportStore()
    store.put(stored)
    point = build_trend((stored.index,), store).segments[0].points[0]
    assert point.reviewer_failure_count == 1


def test_infra_error_counts_stay_distinct() -> None:
    """INFRA_ERROR 保留为独立计数(不折算 fail、不丢弃)。"""
    report = _report_without_input()
    index = build_index_entry(report, recorded_at=_RECORDED)
    expected = sum(len(result.scorer_findings) for result in report.results)
    assert index.pass_count + index.fail_count + index.infra_error_count == expected
    assert index.infra_error_count == 1


def test_postgres_hardening_migration_closes_eval_report_invariants() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "adapters" / "postgres" / "migrations" / "007_eval_report_hardening.sql"
    sql = migration.read_text(encoding="utf-8")
    assert "rubric_digest" in sql
    assert "reviewer_failure_count" in sql
    assert "eval_reports_verdict_closed" in sql
    assert "eval_reports_pass_count_nonnegative" in sql
    assert "eval_reports_fail_count_nonnegative" in sql
    assert "eval_reports_infra_error_count_nonnegative" in sql
    assert "eval_reports_reviewer_failure_count_nonnegative" in sql
    assert "eval_reports_recorded_at_immutable" in sql


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
