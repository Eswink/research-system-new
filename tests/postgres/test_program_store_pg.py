"""PG 程序面存储（GOAL-20261008-037 EC-01）：程序往返、决策 append-only、run 归属查询。

跑在 live PG 上（`postgres` 标记）；语义与 `SqliteProgramStore` / `SqliteRunStore`
同一份口径（两边都实现同一 Port）。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.program_store import PostgresProgramStore
from adapters.postgres.run_store import PostgresRunStore
from packages.domain.core import ID, Timestamp
from packages.domain.program import (
    ProgramContinueRule,
    ProgramDecision,
    ProgramDecisionKind,
    ResearchProgram,
)
from packages.domain.run import ResearchRun

pytestmark = pytest.mark.postgres


def _dsn() -> str:
    import os

    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )


def _clean() -> None:
    import psycopg

    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE research_programs, program_decisions CASCADE")
    conn.execute("TRUNCATE runs CASCADE")
    conn.commit()
    conn.close()


def test_program_and_decisions_round_trip_on_pg() -> None:
    _clean()
    store = PostgresProgramStore(dsn=_dsn())
    program_id = f"prog-{uuid.uuid4().hex[:8]}"
    store.create(
        ResearchProgram(
            id=program_id,
            project_id="p1",
            protocol_id="proto",
            max_runs=2,
            continue_rule=ProgramContinueRule(verdict_in=("ACCEPT",)),
        )
    )
    loaded = store.get(program_id)
    assert loaded.max_runs == 2
    assert loaded.continue_rule.verdict_in == ("ACCEPT",)

    at = Timestamp(datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc))
    first = ProgramDecision(
        program_id=program_id,
        after_index=1,
        kind=ProgramDecisionKind.CONTINUE,
        reason="verdict ACCEPT 命中规则",
        cited_run_id="run-1",
        cited_facts=("verdict ACCEPT",),
        decided_at=at,
    )
    store.record_decision(first)
    store.record_decision(first)  # 自然键重复 ⇒ 幂等空操作
    decisions = store.decisions_of(program_id)
    assert len(decisions) == 1
    assert decisions[0].cited_facts == ("verdict ACCEPT",)
    store.close()


def test_human_gate_round_trips_and_defaults_to_no_gate_on_pg() -> None:
    """GOAL-20261010-046 EC-02：**PG 侧**的闸门往返 —— 与 SQLite 同一份契约。

    两臂逐条（与 SQLite 那份逐字同形）：声明的 `human_gate_at_index=2` 读回来的就是 2；
    未声明的读回 `None`（`NULL` = **不设闸门**，不是被回填出来的某个序号）。
    """
    _clean()
    store = PostgresProgramStore(dsn=_dsn())
    gated = f"prog-gated-{uuid.uuid4().hex[:8]}"
    ungated = f"prog-ungated-{uuid.uuid4().hex[:8]}"
    store.create(
        ResearchProgram(
            id=gated,
            project_id="p1",
            protocol_id="proto",
            max_runs=3,
            continue_rule=ProgramContinueRule(verdict_in=("ACCEPT",)),
            human_gate_at_index=2,
        )
    )
    store.create(
        ResearchProgram(
            id=ungated,
            project_id="p1",
            protocol_id="proto",
            max_runs=3,
            continue_rule=ProgramContinueRule(verdict_in=("ACCEPT",)),
        )
    )
    assert store.get(gated).human_gate_at_index == 2
    assert store.get(ungated).human_gate_at_index is None
    store.close()


def test_run_program_association_queries_on_pg() -> None:
    _clean()
    store = PostgresRunStore(dsn=_dsn())
    program_id = f"prog-{uuid.uuid4().hex[:8]}"

    def _run(index: int) -> ResearchRun:
        return ResearchRun(
            id=ID(str(uuid.uuid4())),
            project_id="p1",
            protocol_id="proto",
            program_id=program_id,
            program_index=index,
        )

    second, first = _run(2), _run(1)
    store.save_run(second)
    store.save_run(first)
    ordered = store.for_program(program_id)
    assert [r.program_index for r in ordered] == [1, 2]
    assert store.for_program("prog-missing") == ()
    store.close()
