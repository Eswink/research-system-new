"""SqliteProgramStore：研究程序的声明与推进决策的 SQLite 持久化（GOAL-20261008-037 EC-01）。

两张表（`research_programs` / `program_decisions`）见本模块 `_SCHEMA`。
决策表是 **append-only**：主键是 `(program_id, after_index, decided_at)` 的自然键
（每次推进一条事实，不覆盖）；被引 canonical 事实的**原文**以 JSON 数组存
`cited_facts_json`（读面原文，不再加工）。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect
from packages.domain.core import Timestamp
from packages.domain.program import (
    ProgramContinueRule,
    ProgramDecision,
    ProgramDecisionKind,
    ResearchProgram,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS research_programs (
    program_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    protocol_id TEXT NOT NULL,
    max_runs INTEGER NOT NULL,
    -- GOAL-20261008-040 EC-02：每序号尝试上界（缺省 1 = 不重试）。
    max_attempts_per_index INTEGER NOT NULL DEFAULT 1,
    -- GOAL-20261010-046 EC-02：程序级人工闸门序号（NULL = 不设闸门 ⇒ 既有行为逐字不变）。
    human_gate_at_index INTEGER,
    -- GOAL-20261010-048 EC-02：**条件式**人工闸门（NULL = 不设 ⇒ 既有行为逐字不变）。
    human_gate_on_verdicts_json TEXT,
    continue_rule_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_research_programs_project ON research_programs(project_id);

CREATE TABLE IF NOT EXISTS program_decisions (
    program_id TEXT NOT NULL,
    after_index INTEGER NOT NULL,
    decided_at TEXT NOT NULL,
    kind TEXT NOT NULL,
    reason TEXT NOT NULL,
    cited_run_id TEXT,
    cited_facts_json TEXT NOT NULL,
    PRIMARY KEY (program_id, after_index, decided_at)
);
"""


def _encode_rule(rule: ProgramContinueRule) -> str:
    return json.dumps({"verdict_in": list(rule.verdict_in)}, ensure_ascii=False, sort_keys=True)


def _decode_rule(raw: object) -> ProgramContinueRule:
    payload = json.loads(str(raw))
    return ProgramContinueRule(verdict_in=tuple(str(item) for item in payload["verdict_in"]))


def _encode_gate_conditions(conditions: tuple[str, ...] | None) -> str | None:
    """条件的落库形态（`None` = **未声明** ⇒ 存 `NULL`，不是空数组）。

    与结论面的 `_encode_rule` 同形（JSON + `sort_keys`），但**不**复用：`None` 与 `()`
    在这里**语义不同**（未声明 vs 声明了但没有取值 —— 后者在域层已被拒绝），
    存成 `[]` 会让「未声明」与「坏声明」在落库层读起来一样。
    """
    if conditions is None:
        return None
    return json.dumps(list(conditions), ensure_ascii=False, sort_keys=True)


def _decode_gate_conditions(raw: object) -> tuple[str, ...] | None:
    if raw is None:
        return None
    return tuple(str(item) for item in json.loads(str(raw)))


def _encode_program(program: ResearchProgram) -> tuple[object, ...]:
    return (
        program.id,
        program.project_id,
        program.protocol_id,
        program.max_runs,
        program.max_attempts_per_index,
        program.human_gate_at_index,
        _encode_gate_conditions(program.human_gate_on_verdicts),
        _encode_rule(program.continue_rule),
        program.created_at.value.isoformat(),
        program.updated_at.value.isoformat(),
    )


def _decode_program(row: sqlite3.Row | tuple[object, ...]) -> ResearchProgram:
    (
        program_id,
        project_id,
        protocol_id,
        max_runs,
        attempts,
        gate_at,
        conditions,
        rule,
        created_at,
        updated_at,
    ) = row[:10]
    return ResearchProgram(
        id=str(program_id),
        project_id=str(project_id),
        protocol_id=str(protocol_id),
        max_runs=int(str(max_runs)),
        max_attempts_per_index=int(str(attempts)),
        # GOAL-20261010-046 EC-02：NULL = 不设闸门（既有行为逐字不变）。
        human_gate_at_index=int(str(gate_at)) if gate_at is not None else None,
        human_gate_on_verdicts=_decode_gate_conditions(conditions),
        continue_rule=_decode_rule(rule),
        created_at=Timestamp(datetime.fromisoformat(str(created_at))),
        updated_at=Timestamp(datetime.fromisoformat(str(updated_at))),
    )


def _decode_decision(row: sqlite3.Row | tuple[object, ...]) -> ProgramDecision:
    program_id, after_index, decided_at, kind, reason, cited_run_id, cited_facts = row[:7]
    return ProgramDecision(
        program_id=str(program_id),
        after_index=int(str(after_index)),
        kind=ProgramDecisionKind(str(kind)),
        reason=str(reason),
        cited_run_id=None if cited_run_id is None else str(cited_run_id),
        cited_facts=tuple(str(item) for item in json.loads(str(cited_facts))),
        decided_at=Timestamp(datetime.fromisoformat(str(decided_at))),
    )


class SqliteProgramStore(SqliteAdapterBase):
    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("program_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def create(self, program: ResearchProgram) -> None:
        self._ensure_open()
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO research_programs (program_id, project_id,"
                " protocol_id, max_runs, max_attempts_per_index, human_gate_at_index,"
                " human_gate_on_verdicts_json, continue_rule_json, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                _encode_program(program),
            )
        self._record("create", program.id, result="ok")

    def get(self, program_id: str) -> ResearchProgram:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT program_id, project_id, protocol_id, max_runs,"
            " max_attempts_per_index, human_gate_at_index, human_gate_on_verdicts_json,"
            " continue_rule_json, created_at, updated_at FROM research_programs"
            " WHERE program_id = ?",
            (program_id,),
        ).fetchone()
        if row is None:
            self._record("get", program_id, error="KeyError")
            raise KeyError(f"program not found: {program_id!r}")
        self._record("get", program_id, result=program_id)
        return _decode_program(row)

    def for_project(self, project_id: str) -> tuple[ResearchProgram, ...]:
        self._ensure_open()
        rows = self._conn.execute(
            "SELECT program_id, project_id, protocol_id, max_runs,"
            " max_attempts_per_index, human_gate_at_index, human_gate_on_verdicts_json,"
            " continue_rule_json, created_at, updated_at FROM research_programs"
            " WHERE project_id = ? ORDER BY program_id",
            (project_id,),
        ).fetchall()
        self._record("for_project", project_id, result=str(len(rows)))
        return tuple(_decode_program(row) for row in rows)

    def record_decision(self, decision: ProgramDecision) -> None:
        self._ensure_open()
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO program_decisions (program_id, after_index,"
                " decided_at, kind, reason, cited_run_id, cited_facts_json)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    decision.program_id,
                    decision.after_index,
                    decision.decided_at.value.isoformat(),
                    decision.kind.value,
                    decision.reason,
                    decision.cited_run_id,
                    json.dumps(list(decision.cited_facts), ensure_ascii=False),
                ),
            )
        self._record("record_decision", decision.program_id, result=decision.kind.value)

    def decisions_of(self, program_id: str) -> tuple[ProgramDecision, ...]:
        self._ensure_open()
        rows = self._conn.execute(
            "SELECT program_id, after_index, decided_at, kind, reason, cited_run_id,"
            " cited_facts_json FROM program_decisions WHERE program_id = ?"
            " ORDER BY decided_at, after_index",
            (program_id,),
        ).fetchall()
        self._record("decisions_of", program_id, result=str(len(rows)))
        return tuple(_decode_decision(row) for row in rows)
