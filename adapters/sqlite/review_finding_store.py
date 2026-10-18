"""SqliteReviewFindingStore：验收门求值结论的 SQLite 持久化（GOAL-20261008-035 EC-01）。

表结构见本模块 `_SCHEMA`；`finding_id` 主键 ⇒ 同一结论重复写是幂等空操作
（`INSERT OR IGNORE`，与 `notification_reads` 同口径的 append-only 语义）。
结论文本（逐字判词）以 JSON 数组存 `findings_json`：它是**读面的原文**，不重排。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso
from packages.application.ports.review_finding_store import ScopedReviewFinding
from packages.domain.core import Timestamp
from packages.domain.evidence import ReviewFinding

_SCHEMA = """
CREATE TABLE IF NOT EXISTS review_findings (
    finding_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    contract_id TEXT NOT NULL,
    review_type TEXT NOT NULL,
    verdict TEXT NOT NULL,
    reviewed_by TEXT,
    reviewed_at TEXT,
    findings_json TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    reviewer_model TEXT
);
CREATE INDEX IF NOT EXISTS idx_review_findings_run ON review_findings(run_id);
"""

#: 既有库的**增量列**（GOAL-20261018-085 EC-01）：`CREATE TABLE IF NOT EXISTS` 不给已存在的
#: 表加列 ⇒ 必须显式 `ALTER`。可空、无缺省 ⇒ 既有行保持 NULL（= 未声明该面）。
_ADDED_COLUMNS: tuple[tuple[str, str], ...] = (
    ("reviewer_model", "ALTER TABLE review_findings ADD COLUMN reviewer_model TEXT"),
)


def _ensure_columns(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(review_findings)")}
    for column, statement in _ADDED_COLUMNS:
        if column not in existing:
            conn.execute(statement)


def _decode(row: sqlite3.Row | tuple[object, ...]) -> ScopedReviewFinding:
    (
        finding_id,
        run_id,
        task_id,
        contract_id,
        review_type,
        verdict,
        by,
        at,
        findings,
        reviewer_model,
    ) = row[:10]
    reviewed_at = datetime.fromisoformat(str(at)) if at else None
    return ScopedReviewFinding(
        finding=ReviewFinding(
            id=str(finding_id),
            review_type=str(review_type),
            verdict=str(verdict),
            findings=[str(item) for item in json.loads(str(findings))],
            reviewed_by=None if by is None else str(by),
            reviewed_at=None if reviewed_at is None else Timestamp(reviewed_at),
            reviewer_model=None if reviewer_model is None else str(reviewer_model),
        ),
        run_id=str(run_id),
        task_id=str(task_id),
        contract_id=str(contract_id),
    )


class SqliteReviewFindingStore(SqliteAdapterBase):
    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("review_finding_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)
        _ensure_columns(self._conn)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def put(self, scoped: ScopedReviewFinding) -> None:
        self._ensure_open()
        finding = scoped.finding
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO review_findings (finding_id, run_id, task_id,"
                " contract_id, review_type, verdict, reviewed_by, reviewed_at,"
                " findings_json, recorded_at, reviewer_model)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    finding.id,
                    scoped.run_id,
                    scoped.task_id,
                    scoped.contract_id,
                    finding.review_type,
                    finding.verdict,
                    finding.reviewed_by,
                    None if finding.reviewed_at is None else finding.reviewed_at.value.isoformat(),
                    json.dumps(list(finding.findings), ensure_ascii=False),
                    now_iso(None),
                    finding.reviewer_model,
                ),
            )
        self._record("put", finding.id, result="ok")

    def for_run(self, run_id: str) -> tuple[ScopedReviewFinding, ...]:
        self._ensure_open()
        rows = self._conn.execute(
            "SELECT finding_id, run_id, task_id, contract_id, review_type, verdict,"
            " reviewed_by, reviewed_at, findings_json, reviewer_model FROM review_findings"
            " WHERE run_id = ? ORDER BY finding_id",
            (run_id,),
        ).fetchall()
        self._record("for_run", run_id, result=str(len(rows)))
        return tuple(_decode(row) for row in rows)
