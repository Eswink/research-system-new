"""PostgresProgramStore：研究程序的声明与推进决策的 PostgreSQL 实现（GOAL-20261008-037 EC-01）。

表结构见 `migrations/017_research_programs.sql`。决策表 append-only：主键是
`(program_id, after_index, decided_at)` 自然键 + `ON CONFLICT DO NOTHING`；
被引 canonical 事实的**原文**存 `cited_facts_json`（读面原文，不再加工）。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from adapters.postgres.base import PostgresAdapterBase
from packages.domain.core import Timestamp
from packages.domain.program import (
    ProgramContinueRule,
    ProgramDecision,
    ProgramDecisionKind,
    ResearchProgram,
)

_PROGRAM_SELECT = (
    "SELECT program_id, project_id, protocol_id, max_runs, continue_rule_json,"
    " created_at, updated_at FROM research_programs"
)
_DECISION_SELECT = (
    "SELECT program_id, after_index, decided_at, kind, reason, cited_run_id,"
    " cited_facts_json FROM program_decisions"
)


def _json_object(value: Any) -> Any:
    """JSONB 列可能是**已解析对象**（psycopg 的 jsonb 返回）或字符串（驱动差异）。

    两种形态都接住：把已解析的转回文本再统一 `json.loads`，避免 `str(dict)` 产出
    单引号伪 JSON（实测：直接用 ``str(row[...])`` 会抛 JSONDecodeError）。
    """
    if isinstance(value, str):
        return json.loads(value)
    if isinstance(value, (dict, list)):
        return json.loads(json.dumps(value))
    return json.loads(str(value))


def _as_datetime(value: Any) -> datetime:
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    assert isinstance(value, datetime)
    return value


def _decode_program(row: Any) -> ResearchProgram:
    payload = _json_object(row["continue_rule_json"])
    return ResearchProgram(
        id=str(row["program_id"]),
        project_id=str(row["project_id"]),
        protocol_id=str(row["protocol_id"]),
        max_runs=int(row["max_runs"]),
        continue_rule=ProgramContinueRule(
            verdict_in=tuple(str(item) for item in payload["verdict_in"])
        ),
        created_at=Timestamp(_as_datetime(row["created_at"])),
        updated_at=Timestamp(_as_datetime(row["updated_at"])),
    )


def _decode_decision(row: Any) -> ProgramDecision:
    return ProgramDecision(
        program_id=str(row["program_id"]),
        after_index=int(row["after_index"]),
        kind=ProgramDecisionKind(str(row["kind"])),
        reason=str(row["reason"]),
        cited_run_id=None if row["cited_run_id"] is None else str(row["cited_run_id"]),
        cited_facts=tuple(str(item) for item in _json_object(row["cited_facts_json"])),
        decided_at=Timestamp(_as_datetime(row["decided_at"])),
    )


class PostgresProgramStore(PostgresAdapterBase):
    """研究程序声明 + 推进决策的 PostgreSQL 存储。"""

    def __init__(self, *, dsn: str | None = None, connection: Any | None = None) -> None:
        from psycopg.rows import dict_row

        from adapters.postgres.db import connect as pg_connect
        from adapters.postgres.db import dsn_from_env

        super().__init__("program_store")
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresProgramStore requires dsn or connection")
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

    def create(self, program: ResearchProgram) -> None:
        self._ensure_open()
        self._conn.execute(
            "INSERT INTO research_programs (program_id, project_id, protocol_id, max_runs,"
            " continue_rule_json, created_at, updated_at)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s)"
            " ON CONFLICT (program_id) DO NOTHING",
            (
                program.id,
                program.project_id,
                program.protocol_id,
                program.max_runs,
                json.dumps(
                    {"verdict_in": list(program.continue_rule.verdict_in)},
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                program.created_at.value,
                program.updated_at.value,
            ),
        )
        self._record("create", program.id, result="ok")

    def get(self, program_id: str) -> ResearchProgram:
        self._ensure_open()
        row: Any = self._conn.execute(
            f"{_PROGRAM_SELECT} WHERE program_id = %s", (program_id,)
        ).fetchone()
        if row is None:
            self._record("get", program_id, error="KeyError")
            raise KeyError(f"program not found: {program_id!r}")
        self._record("get", program_id, result=program_id)
        return _decode_program(row)

    def for_project(self, project_id: str) -> tuple[ResearchProgram, ...]:
        self._ensure_open()
        rows: list[Any] = self._conn.execute(
            f"{_PROGRAM_SELECT} WHERE project_id = %s ORDER BY program_id", (project_id,)
        ).fetchall()
        self._record("for_project", project_id, result=str(len(rows)))
        return tuple(_decode_program(row) for row in rows)

    def record_decision(self, decision: ProgramDecision) -> None:
        self._ensure_open()
        self._conn.execute(
            "INSERT INTO program_decisions (program_id, after_index, decided_at, kind,"
            " reason, cited_run_id, cited_facts_json)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s)"
            " ON CONFLICT (program_id, after_index, decided_at) DO NOTHING",
            (
                decision.program_id,
                decision.after_index,
                decision.decided_at.value,
                decision.kind.value,
                decision.reason,
                decision.cited_run_id,
                json.dumps(list(decision.cited_facts), ensure_ascii=False),
            ),
        )
        self._record("record_decision", decision.program_id, result=decision.kind.value)

    def decisions_of(self, program_id: str) -> tuple[ProgramDecision, ...]:
        self._ensure_open()
        rows: list[Any] = self._conn.execute(
            f"{_DECISION_SELECT} WHERE program_id = %s ORDER BY decided_at, after_index",
            (program_id,),
        ).fetchall()
        self._record("decisions_of", program_id, result=str(len(rows)))
        return tuple(_decode_decision(row) for row in rows)
