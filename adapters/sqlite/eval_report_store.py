"""SQLite implementation of the immutable, validated M15 EvalReportStore."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from adapters.sqlite.base import SqliteAdapterBase
from packages.application.ports.eval_report_store import (
    EvalReportIndexEntry,
    EvalReportQuery,
    EvalReportQueryPage,
    StoredEvalReport,
)
from packages.domain.enums import QualityGateVerdict

_SCHEMA = """
CREATE TABLE IF NOT EXISTS eval_reports (
    report_digest TEXT PRIMARY KEY,
    body TEXT NOT NULL,
    comparison_digest TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    dataset_version TEXT NOT NULL,
    dataset_digest TEXT NOT NULL,
    gate_config_id TEXT NOT NULL,
    gate_config_version TEXT NOT NULL,
    gate_config_digest TEXT NOT NULL,
    scorer_versions TEXT NOT NULL,
    system_version TEXT NOT NULL,
    rubric_digest TEXT,
    case_ids TEXT NOT NULL,
    evaluator_identities TEXT NOT NULL,
    verdict TEXT NOT NULL CHECK (verdict IN ('PASS', 'PASS_WITH_WARNINGS', 'REVISE', 'BLOCK')),
    pass_count INTEGER NOT NULL CHECK (pass_count >= 0),
    fail_count INTEGER NOT NULL CHECK (fail_count >= 0),
    infra_error_count INTEGER NOT NULL CHECK (infra_error_count >= 0),
    reviewer_failure_count INTEGER NOT NULL DEFAULT 0 CHECK (reviewer_failure_count >= 0),
    usage_ref TEXT,
    cost_ref TEXT,
    run_id TEXT,
    recorded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_eval_reports_latest
    ON eval_reports(recorded_at DESC, report_digest DESC);
"""

_IMMUTABLE_RECORDED_AT = """
CREATE TRIGGER IF NOT EXISTS eval_reports_recorded_at_immutable
BEFORE UPDATE OF recorded_at ON eval_reports
FOR EACH ROW WHEN NEW.recorded_at <> OLD.recorded_at
BEGIN
    SELECT RAISE(ABORT, 'eval_reports.recorded_at is immutable');
END;
"""

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class SqliteEvalReportStore(SqliteAdapterBase):
    """SQLite store; duplicate digests retain the first canonical ingestion record."""

    def __init__(
        self,
        connection: sqlite3.Connection | str = ":memory:",
        *,
        now: datetime | None = None,
    ) -> None:
        super().__init__("eval_report_store")
        self._connection = (
            sqlite3.connect(connection) if isinstance(connection, str) else connection
        )
        self._connection.row_factory = sqlite3.Row
        self._now = now or datetime.now(timezone.utc)
        self._connection.executescript(_SCHEMA)
        self._ensure_compatible_schema()

    def put(self, report: StoredEvalReport) -> None:
        self._ensure_open()
        index = report.index
        with self._connection:
            self._connection.execute(
                "INSERT INTO eval_reports ("
                "report_digest, body, comparison_digest, dataset_id, dataset_version, "
                "dataset_digest, gate_config_id, gate_config_version, gate_config_digest, "
                "scorer_versions, system_version, rubric_digest, case_ids, evaluator_identities, "
                "verdict, pass_count, fail_count, infra_error_count, reviewer_failure_count, "
                "usage_ref, cost_ref, run_id, recorded_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(report_digest) DO NOTHING",
                _insert_values(report),
            )
        self._record("put", index.report_digest)

    def get(self, report_digest: str) -> StoredEvalReport | None:
        self._ensure_open()
        row = self._connection.execute(
            "SELECT * FROM eval_reports WHERE report_digest = ?", (report_digest,)
        ).fetchone()
        self._record("get", report_digest, result="hit" if row is not None else "miss")
        return None if row is None else _stored_from_row(row)

    def query(self, query: EvalReportQuery) -> tuple[EvalReportIndexEntry, ...]:
        return self.query_page(query).entries

    def query_page(self, query: EvalReportQuery) -> EvalReportQueryPage:
        self._ensure_open()
        clauses, params = _query_parts(query)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._connection.execute(
            "SELECT * FROM eval_reports "
            + where
            + " ORDER BY recorded_at DESC, report_digest DESC LIMIT ?",
            (*params, query.limit + 1),
        ).fetchall()
        truncated = len(rows) > query.limit
        entries = tuple(_index_from_row(row) for row in rows[: query.limit])
        self._record("query", query.dataset_id or "", result=f"{len(entries)} hits")
        return EvalReportQueryPage(entries=entries, truncated=truncated)

    def _ensure_compatible_schema(self) -> None:
        """Additive local-index migration for SQLite files created before hardening."""
        columns = {
            str(row["name"])
            for row in self._connection.execute("PRAGMA table_info(eval_reports)").fetchall()
        }
        additions = {
            "rubric_digest": "TEXT",
            "reviewer_failure_count": "INTEGER NOT NULL DEFAULT 0",
        }
        for name, declaration in additions.items():
            if name not in columns:
                self._connection.execute(
                    f"ALTER TABLE eval_reports ADD COLUMN {name} {declaration}"
                )
        self._connection.executescript(_IMMUTABLE_RECORDED_AT)
        self._connection.commit()


def _insert_values(report: StoredEvalReport) -> tuple[object, ...]:
    index = report.index
    return (
        index.report_digest,
        report.body.decode("utf-8"),
        index.comparison_digest,
        index.dataset_id,
        index.dataset_version,
        index.dataset_digest,
        index.gate_config_id,
        index.gate_config_version,
        index.gate_config_digest,
        json.dumps([list(pair) for pair in index.scorer_versions]),
        index.system_version,
        index.rubric_digest,
        json.dumps(list(index.case_ids)),
        json.dumps(list(index.evaluator_identities)),
        index.verdict.value,
        index.pass_count,
        index.fail_count,
        index.infra_error_count,
        index.reviewer_failure_count,
        index.usage_ref,
        index.cost_ref,
        index.run_id,
        index.recorded_at.isoformat(),
    )


def _query_parts(query: EvalReportQuery) -> tuple[list[str], list[str]]:
    clauses: list[str] = []
    params: list[str] = []
    if query.comparison_digest is not None:
        clauses.append("comparison_digest = ?")
        params.append(query.comparison_digest)
    if query.dataset_id is not None:
        clauses.append("dataset_id = ?")
        params.append(query.dataset_id)
    if query.run_id is not None:
        clauses.append("run_id = ?")
        params.append(query.run_id)
    return clauses, params


def _stored_from_row(row: sqlite3.Row) -> StoredEvalReport:
    return StoredEvalReport(index=_index_from_row(row), body=str(row["body"]).encode("utf-8"))


def _index_from_row(row: sqlite3.Row) -> EvalReportIndexEntry:
    recorded = row["recorded_at"]
    return EvalReportIndexEntry(
        report_digest=str(row["report_digest"]),
        comparison_digest=str(row["comparison_digest"]),
        dataset_id=str(row["dataset_id"]),
        dataset_version=str(row["dataset_version"]),
        dataset_digest=str(row["dataset_digest"]),
        gate_config_id=str(row["gate_config_id"]),
        gate_config_version=str(row["gate_config_version"]),
        gate_config_digest=str(row["gate_config_digest"]),
        scorer_versions=tuple(
            (pair[0], pair[1]) for pair in json.loads(str(row["scorer_versions"]))
        ),
        system_version=str(row["system_version"]),
        verdict=QualityGateVerdict(str(row["verdict"])),
        recorded_at=datetime.fromisoformat(str(recorded)) if recorded else _EPOCH,
        rubric_digest=str(row["rubric_digest"]) if row["rubric_digest"] is not None else None,
        case_ids=tuple(json.loads(str(row["case_ids"]))),
        evaluator_identities=tuple(json.loads(str(row["evaluator_identities"]))),
        pass_count=int(row["pass_count"]),
        fail_count=int(row["fail_count"]),
        infra_error_count=int(row["infra_error_count"]),
        reviewer_failure_count=int(row["reviewer_failure_count"]),
        usage_ref=row["usage_ref"],
        cost_ref=row["cost_ref"],
        run_id=row["run_id"],
    )
