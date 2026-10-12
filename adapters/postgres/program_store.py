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
    "SELECT program_id, project_id, protocol_id, max_runs, max_attempts_per_index,"
    " human_gate_at_index, human_gate_on_verdicts_json, human_gate_at_indexes_json,"
    " gate_nudge_after_seconds, human_gate_hybrid_indexes_json,"
    " human_gate_hybrid_verdicts_json, continue_rule_json, created_at, updated_at"
    " FROM research_programs"
)
_DECISION_SELECT = (
    "SELECT program_id, after_index, decided_at, kind, reason, cited_run_id,"
    " cited_facts_json FROM program_decisions"
)


_PROGRAM_INSERT = (
    "INSERT INTO research_programs (program_id, project_id, protocol_id, max_runs,"
    " max_attempts_per_index, human_gate_at_index, human_gate_on_verdicts_json,"
    " human_gate_at_indexes_json, gate_nudge_after_seconds,"
    " human_gate_hybrid_indexes_json, human_gate_hybrid_verdicts_json,"
    " continue_rule_json, created_at, updated_at)"
    " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    " ON CONFLICT (program_id) DO NOTHING"
)


def _json_or_none(items: Any) -> Any:
    """列表 ⇒ JSON 文本；`None` ⇒ `NULL`（**未声明**与「空列表」在落库层分得开）。"""
    if items is None:
        return None
    return json.dumps(list(items), ensure_ascii=False, sort_keys=True)


def _insert_values(program: ResearchProgram) -> tuple[Any, ...]:
    """`create` 的取值元组（**列序与 `_PROGRAM_SELECT` 同源**）。

    **为什么单列**：`create` 有 50 行硬上限 —— 声明形态变多之后，取值列表一度把它顶爆
    ⇒ 逐项搬到这里（**语义一字未动**，只是换落点），并守住那道门。
    """
    hybrid = program.human_gate_hybrid
    return (
        program.id,
        program.project_id,
        program.protocol_id,
        program.max_runs,
        program.max_attempts_per_index,
        program.human_gate_at_index,
        _json_or_none(program.human_gate_on_verdicts),
        _json_or_none(program.human_gate_at_indexes),
        # GOAL-20261012-059 EC-02：NULL = 未声明（列序与 `_PROGRAM_SELECT` 同源）。
        program.gate_nudge_after_seconds,
        _json_or_none(hybrid.at_indexes if hybrid is not None else None),
        _json_or_none(hybrid.on_verdicts if hybrid is not None else None),
        json.dumps(
            {"verdict_in": list(program.continue_rule.verdict_in)},
            ensure_ascii=False,
            sort_keys=True,
        ),
        program.created_at.value,
        program.updated_at.value,
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


def _decode_hybrid(row: Any) -> Any:
    """混合式声明的两列解码（**成对**；任一为 `NULL` ⇒ 整条未声明）。

    与 SQLite 侧同名助手**同一口径**（一列有一列无 = 落库被外部改写，**不猜**）。
    """
    if (
        row["human_gate_hybrid_indexes_json"] is None
        or row["human_gate_hybrid_verdicts_json"] is None
    ):
        return None
    from packages.domain.program import HybridGateDeclaration

    return HybridGateDeclaration(
        at_indexes=tuple(
            int(str(item)) for item in _json_object(row["human_gate_hybrid_indexes_json"])
        ),
        on_verdicts=tuple(
            str(item) for item in _json_object(row["human_gate_hybrid_verdicts_json"])
        ),
    )


def _decode_program(row: Any) -> ResearchProgram:
    payload = _json_object(row["continue_rule_json"])
    return ResearchProgram(
        id=str(row["program_id"]),
        project_id=str(row["project_id"]),
        protocol_id=str(row["protocol_id"]),
        max_runs=int(row["max_runs"]),
        # GOAL-20261008-040 EC-02：每序号尝试上界（缺省 1 = 不重试）。
        max_attempts_per_index=int(row["max_attempts_per_index"]),
        # GOAL-20261010-046 EC-02：NULL = 不设闸门（既有行为逐字不变）。
        human_gate_at_index=(
            int(row["human_gate_at_index"]) if row["human_gate_at_index"] is not None else None
        ),
        # GOAL-20261010-048 EC-02：NULL = 未声明条件闸门（不是空数组；见 sqlite 侧同名助手）。
        human_gate_on_verdicts=(
            tuple(str(item) for item in _json_object(row["human_gate_on_verdicts_json"]))
            if row["human_gate_on_verdicts_json"] is not None
            else None
        ),
        # GOAL-20261011-055 EC-02：NULL = 未声明多点闸门（不是空数组；见 sqlite 侧同名助手）。
        human_gate_at_indexes=(
            tuple(int(str(item)) for item in _json_object(row["human_gate_at_indexes_json"]))
            if row["human_gate_at_indexes_json"] is not None
            else None
        ),
        # GOAL-20261012-059 EC-02：NULL = 未声明超期界（不是 0；见 sqlite 侧同名列）。
        gate_nudge_after_seconds=(
            int(row["gate_nudge_after_seconds"])
            if row["gate_nudge_after_seconds"] is not None
            else None
        ),
        # GOAL-20261012-060 EC-02：混合式（两列**成对**；任一 NULL ⇒ 未声明）。
        human_gate_hybrid=_decode_hybrid(row),
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
            _PROGRAM_INSERT,
            _insert_values(program),
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
