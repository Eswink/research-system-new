"""EvalReportStore 的 SQLite 实现(M15 WP3)。

canonical truth 是 `body` 原文(TEXT);索引列由 `eval_index` 派生并可从
body 完整重建(rebuild-from-bodies 测试)。put 幂等(UPSERT by
report_digest);query 确定性排序(comparison_digest, recorded_at)。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from adapters.sqlite.base import SqliteAdapterBase
from packages.application.ports.eval_report_store import (
    EvalReportIndexEntry,
    EvalReportQuery,
    StoredEvalReport,
)

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
    case_ids TEXT NOT NULL,
    evaluator_identities TEXT NOT NULL,
    verdict TEXT NOT NULL,
    pass_count INTEGER NOT NULL,
    fail_count INTEGER NOT NULL,
    infra_error_count INTEGER NOT NULL,
    usage_ref TEXT,
    cost_ref TEXT,
    run_id TEXT,
    recorded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_eval_reports_comparison
    ON eval_reports(comparison_digest, recorded_at);
"""

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class SqliteEvalReportStore(SqliteAdapterBase):
    """SQLite 持久化 EvalReportStore;`now` 可注入用于确定性测试。"""

    def __init__(
        self,
        connection: sqlite3.Connection | str = ":memory:",
        *,
        now: datetime | None = None,
    ) -> None:
        super().__init__("eval_report_store")
        if isinstance(connection, str):
            self._connection = sqlite3.connect(connection)
        else:
            self._connection = connection
        self._connection.row_factory = sqlite3.Row
        self._now = now or datetime.now(timezone.utc)
        self._connection.executescript(_SCHEMA)

    def put(self, report: StoredEvalReport) -> None:
        self._ensure_open()
        index = report.index
        self._connection.execute(
            "INSERT OR REPLACE INTO eval_reports ("
            " report_digest, body, comparison_digest, dataset_id, dataset_version,"
            " dataset_digest, gate_config_id, gate_config_version, gate_config_digest,"
            " scorer_versions, system_version, case_ids, evaluator_identities, verdict,"
            " pass_count, fail_count, infra_error_count, usage_ref, cost_ref, run_id,"
            " recorded_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
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
                json.dumps(list(index.case_ids)),
                json.dumps(list(index.evaluator_identities)),
                index.verdict,
                index.pass_count,
                index.fail_count,
                index.infra_error_count,
                index.usage_ref,
                index.cost_ref,
                index.run_id,
                (index.recorded_at or self._now).isoformat(),
            ),
        )
        self._connection.commit()
        self._record("put", index.report_digest)

    def get(self, report_digest: str) -> StoredEvalReport | None:
        self._ensure_open()
        row = self._connection.execute(
            "SELECT * FROM eval_reports WHERE report_digest = ?", (report_digest,)
        ).fetchone()
        self._record("get", report_digest, result="hit" if row is not None else "miss")
        if row is None:
            return None
        return StoredEvalReport(index=_decode_row(row), body=str(row["body"]).encode("utf-8"))

    def query(self, query: EvalReportQuery) -> tuple[EvalReportIndexEntry, ...]:
        self._ensure_open()
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
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            "SELECT * FROM eval_reports " + where + " ORDER BY comparison_digest, recorded_at"
            " LIMIT ?"
        )
        rows = self._connection.execute(sql, (*params, query.limit)).fetchall()
        self._record("query", query.dataset_id or "", result=f"{len(rows)} hits")
        return tuple(_decode_row(row) for row in rows)


def _decode_row(row: sqlite3.Row) -> EvalReportIndexEntry:
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
        case_ids=tuple(json.loads(str(row["case_ids"]))),
        evaluator_identities=tuple(json.loads(str(row["evaluator_identities"]))),
        verdict=str(row["verdict"]),
        pass_count=int(row["pass_count"]),
        fail_count=int(row["fail_count"]),
        infra_error_count=int(row["infra_error_count"]),
        usage_ref=row["usage_ref"],
        cost_ref=row["cost_ref"],
        run_id=row["run_id"],
        recorded_at=datetime.fromisoformat(str(recorded)) if recorded else _EPOCH,
    )
