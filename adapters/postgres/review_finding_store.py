"""PostgresReviewFindingStore：验收门求值结论的 PostgreSQL 实现（GOAL-20261008-035 EC-01）。

表结构见 `migrations/016_review_findings.sql`；`finding_id` 主键 +
`ON CONFLICT DO NOTHING`（append-only：同一结论重复写是幂等空操作）。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from adapters.postgres.base import PostgresAdapterBase
from packages.application.ports.review_finding_store import ScopedReviewFinding
from packages.domain.core import Timestamp
from packages.domain.evidence import ReviewFinding

_SELECT = (
    "SELECT finding_id, run_id, task_id, contract_id, review_type, verdict,"
    " reviewed_by, reviewed_at, findings_json FROM review_findings"
)


def _decode(row: Any) -> ScopedReviewFinding:
    reviewed_at = row["reviewed_at"]
    if isinstance(reviewed_at, str):
        reviewed_at = datetime.fromisoformat(reviewed_at)
    return ScopedReviewFinding(
        finding=ReviewFinding(
            id=str(row["finding_id"]),
            review_type=str(row["review_type"]),
            verdict=str(row["verdict"]),
            findings=[str(item) for item in json.loads(str(row["findings_json"]))],
            reviewed_by=None if row["reviewed_by"] is None else str(row["reviewed_by"]),
            reviewed_at=None if reviewed_at is None else Timestamp(reviewed_at),
        ),
        run_id=str(row["run_id"]),
        task_id=str(row["task_id"]),
        contract_id=str(row["contract_id"]),
    )


class PostgresReviewFindingStore(PostgresAdapterBase):
    """append-only 的评审结论存储（run 作用域可查）。"""

    def __init__(self, *, dsn: str | None = None, connection: Any | None = None) -> None:
        from psycopg.rows import dict_row

        from adapters.postgres.db import connect as pg_connect
        from adapters.postgres.db import dsn_from_env

        super().__init__("review_finding_store")
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresReviewFindingStore requires dsn or connection")
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

    def put(self, scoped: ScopedReviewFinding) -> None:
        self._ensure_open()
        finding = scoped.finding
        self._conn.execute(
            "INSERT INTO review_findings (finding_id, run_id, task_id, contract_id,"
            " review_type, verdict, reviewed_by, reviewed_at, findings_json)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            " ON CONFLICT (finding_id) DO NOTHING",
            (
                finding.id,
                scoped.run_id,
                scoped.task_id,
                scoped.contract_id,
                finding.review_type,
                finding.verdict,
                finding.reviewed_by,
                None if finding.reviewed_at is None else finding.reviewed_at.value,
                json.dumps(list(finding.findings), ensure_ascii=False),
            ),
        )
        self._record("put", finding.id, result="ok")

    def for_run(self, run_id: str) -> tuple[ScopedReviewFinding, ...]:
        self._ensure_open()
        rows = self._conn.execute(
            f"{_SELECT} WHERE run_id = %s ORDER BY finding_id", (run_id,)
        ).fetchall()
        self._record("for_run", run_id, result=str(len(rows)))
        return tuple(_decode(row) for row in rows)
