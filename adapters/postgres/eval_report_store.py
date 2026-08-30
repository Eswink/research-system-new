"""PostgreSQL implementation of the immutable, validated M15 EvalReportStore."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from psycopg.rows import dict_row

from adapters.postgres.base import PostgresAdapterBase
from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env
from packages.application.ports.eval_report_store import (
    EvalReportIndexEntry,
    EvalReportQuery,
    EvalReportQueryPage,
    StoredEvalReport,
)
from packages.domain.enums import QualityGateVerdict

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class PostgresEvalReportStore(PostgresAdapterBase):
    """PostgreSQL store whose first write fixes a report's ordering provenance."""

    def __init__(
        self,
        *,
        dsn: str | None = None,
        connection: Any | None = None,
    ) -> None:
        super().__init__("eval_report_store")
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresEvalReportStore requires dsn or connection")
            self._conn = pg_connect(resolved)
        try:
            self._conn.row_factory = dict_row
        except Exception:
            pass

    def close(self) -> None:
        if getattr(self, "_owns_connection", False):
            try:
                self._conn.close()
            except Exception:
                pass
        super().close()

    def put(self, report: StoredEvalReport) -> None:
        self._ensure_open()
        self._conn.execute(
            "INSERT INTO eval_reports ("
            "report_digest, body, comparison_digest, dataset_id, dataset_version, "
            "dataset_digest, gate_config_id, gate_config_version, gate_config_digest, "
            "scorer_versions, system_version, rubric_digest, case_ids, evaluator_identities, "
            "verdict, pass_count, fail_count, infra_error_count, reviewer_failure_count, "
            "usage_ref, cost_ref, run_id, recorded_at"
            ") VALUES ("
            "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
            "%s, %s, %s, %s) ON CONFLICT (report_digest) DO NOTHING",
            _insert_values(report),
        )
        self._record("put", report.index.report_digest)

    def get(self, report_digest: str) -> StoredEvalReport | None:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT * FROM eval_reports WHERE report_digest = %s", (report_digest,)
        ).fetchone()
        self._record("get", report_digest, result="hit" if row is not None else "miss")
        return None if row is None else _stored_from_row(row)

    def query(self, query: EvalReportQuery) -> tuple[EvalReportIndexEntry, ...]:
        return self.query_page(query).entries

    def query_page(self, query: EvalReportQuery) -> EvalReportQueryPage:
        self._ensure_open()
        clauses, params = _query_parts(query)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._conn.execute(
            "SELECT * FROM eval_reports "
            + where
            + " ORDER BY recorded_at DESC, report_digest DESC LIMIT %s",
            (*params, query.limit + 1),
        ).fetchall()
        truncated = len(rows) > query.limit
        entries = tuple(_index_from_row(row) for row in rows[: query.limit])
        self._record("query", query.dataset_id or "", result=f"{len(entries)} hits")
        return EvalReportQueryPage(entries=entries, truncated=truncated)


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
        index.recorded_at,
    )


def _query_parts(query: EvalReportQuery) -> tuple[list[str], list[object]]:
    clauses: list[str] = []
    params: list[object] = []
    if query.comparison_digest is not None:
        clauses.append("comparison_digest = %s")
        params.append(query.comparison_digest)
    if query.dataset_id is not None:
        clauses.append("dataset_id = %s")
        params.append(query.dataset_id)
    if query.run_id is not None:
        clauses.append("run_id = %s")
        params.append(query.run_id)
    return clauses, params


def _stored_from_row(row: Any) -> StoredEvalReport:
    return StoredEvalReport(index=_index_from_row(row), body=str(row["body"]).encode("utf-8"))


def _index_from_row(row: Any) -> EvalReportIndexEntry:
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
        recorded_at=recorded if isinstance(recorded, datetime) else _EPOCH,
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
