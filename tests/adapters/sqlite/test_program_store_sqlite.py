"""程序面存储的 SQLite 行为判据（GOAL-20261008-037 EC-01）。

四条行为各自可判：

1. **程序 CRUD**：`create` / `get` / `for_project`（声明式规则逐字往返）；
2. **决策 append-only**：同一次推进写两条不同时刻的决策 ⇒ 两条都在（不覆盖）；
   同一条决策重复写是幂等空操作（自然键 `(program_id, after_index, decided_at)`）；
3. **run 的程序归属**：`RunStore.for_program` 按 `program_index` 升序、只挑该程序的 run；
4. **向后兼容**：**旧载荷**（没有 `program_id` / `program_index` 键的 run_json）反序列化
   仍成立且两字段为 `None`（不是报错、也不是伪造默认值）。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from adapters.sqlite.db import RUNS_SCHEMA_SQL, connect
from adapters.sqlite.program_store import SqliteProgramStore
from adapters.sqlite.run_store import SqliteRunStore
from packages.domain.core import ID, Timestamp
from packages.domain.program import (
    ProgramContinueRule,
    ProgramDecision,
    ProgramDecisionKind,
    ResearchProgram,
)
from packages.domain.run import ResearchRun

_UUID = {
    "run-a": "0f6a1f3a-6b1a-4a1e-9c3f-0d5f2b7c9e11",
    "run-b": "1f6a1f3a-6b1a-4a1e-9c3f-0d5f2b7c9e12",
    "run-x": "2f6a1f3a-6b1a-4a1e-9c3f-0d5f2b7c9e13",
    "run-lone": "3f6a1f3a-6b1a-4a1e-9c3f-0d5f2b7c9e14",
    "run-legacy": "4f6a1f3a-6b1a-4a1e-9c3f-0d5f2b7c9e15",
}


def _program(program_id: str = "prog-1", project_id: str = "p1") -> ResearchProgram:
    return ResearchProgram(
        id=program_id,
        project_id=project_id,
        protocol_id="proto",
        max_runs=3,
        continue_rule=ProgramContinueRule(verdict_in=("ACCEPT",)),
    )


def _run(run_id: str, *, program_id: str | None = None, index: int | None = None) -> ResearchRun:
    return ResearchRun(
        id=ID(_UUID[run_id]),
        project_id="p1",
        protocol_id="proto",
        program_id=program_id,
        program_index=index,
    )


def test_program_round_trips_through_sqlite() -> None:
    store = SqliteProgramStore()
    store.create(_program())
    loaded = store.get("prog-1")
    assert loaded.id == "prog-1"
    assert loaded.max_runs == 3
    assert loaded.continue_rule.verdict_in == ("ACCEPT",)
    assert [p.id for p in store.for_project("p1")] == ["prog-1"]
    assert store.for_project("other") == ()


def test_decisions_are_append_only_and_dedup_exact_repeats() -> None:
    store = SqliteProgramStore()
    store.create(_program())
    first = ProgramDecision(
        program_id="prog-1",
        after_index=1,
        kind=ProgramDecisionKind.CONTINUE,
        reason="verdict ACCEPT 命中规则",
        cited_run_id="run-1",
        cited_facts=("verdict ACCEPT",),
        decided_at=Timestamp(datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)),
    )
    later = ProgramDecision(
        program_id="prog-1",
        after_index=1,
        kind=ProgramDecisionKind.DEDUP,
        reason="第 2 轮已存在 ⇒ 幂等命中",
        cited_run_id="run-2",
        decided_at=Timestamp(datetime(2026, 10, 8, 12, 1, 0, tzinfo=timezone.utc)),
    )
    store.record_decision(first)
    store.record_decision(later)
    store.record_decision(first)  # 同一时刻重复写 = 幂等空操作
    decisions = store.decisions_of("prog-1")
    assert [d.kind for d in decisions] == [
        ProgramDecisionKind.CONTINUE,
        ProgramDecisionKind.DEDUP,
    ]
    assert decisions[0].cited_facts == ("verdict ACCEPT",)
    assert decisions[0].cited_run_id == "run-1"


def test_for_program_orders_by_index_and_filters() -> None:
    conn = connect(":memory:")
    conn.executescript(RUNS_SCHEMA_SQL)
    store = SqliteRunStore(connection=conn)
    store.save_run(_run("run-b", program_id="prog-1", index=2))
    store.save_run(_run("run-a", program_id="prog-1", index=1))
    store.save_run(_run("run-x", program_id="prog-2", index=1))
    store.save_run(_run("run-lone"))
    assert [r.id.value for r in store.for_program("prog-1")] == [_UUID["run-a"], _UUID["run-b"]]
    assert [r.id.value for r in store.for_program("prog-2")] == [_UUID["run-x"]]
    assert store.for_program("missing") == ()


def test_program_fields_round_trip_and_legacy_payload_still_decodes() -> None:
    conn = connect(":memory:")
    conn.executescript(RUNS_SCHEMA_SQL)
    store = SqliteRunStore(connection=conn)
    store.save_run(_run("run-a", program_id="prog-1", index=1))
    loaded = store.get_run(_UUID["run-a"])
    assert (loaded.program_id, loaded.program_index) == ("prog-1", 1)

    # 旧载荷：没有 program 键（既有 run 行）⇒ 两字段 None，不报错、不伪造默认值。
    legacy = json.loads(
        json.dumps({
            "id": _UUID["run-legacy"],
            "project_id": "p1",
            "protocol_id": "proto",
            "state": "DRAFT",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        })
    )
    conn.execute(
        "INSERT INTO runs (run_id, project_id, run_json, created_at) VALUES (?, ?, ?, ?)",
        (_UUID["run-legacy"], "p1", json.dumps(legacy), "2026-01-01T00:00:00+00:00"),
    )
    old = store.get_run(_UUID["run-legacy"])
    assert old.program_id is None
    assert old.program_index is None
