"""程序推进驱动的行为判据（GOAL-20261008-037 EC-02）。

六条判定逐条可判（全部用**真实** SQLite 存储，不写假存储）：

1. `START`：程序内没有 run ⇒ 起第 1 轮；
2. `WAIT`：上一轮未终止 ⇒ 不推进、**不**起第二个 run（幂等的第一形态）；
3. `STOP_RULE`：上一轮落库判词**不**命中规则 ⇒ 按结论停（`cited_facts` 是逐字判词）；
4. `CONTINUE`：判词命中 ⇒ 起下一轮；
5. `STOP_GUARDRAIL`：判词命中但已到 `max_runs` ⇒ 按上界停（**与 `STOP_RULE` 可区分**）；
6. `DEDUP`：上一条 `CONTINUE` 认领的 run 未落库（崩溃窗口）⇒ **不产生第二个 run**，点名；
7. `WAIT`（无启动面）：装配没有提供启动面 ⇒ 点名，而不是假装已启动。
"""

from __future__ import annotations

import sqlite3
import uuid

from adapters.sqlite.db import RUNS_SCHEMA_SQL, connect
from adapters.sqlite.program_store import SqliteProgramStore
from adapters.sqlite.run_store import SqliteRunStore
from packages.application.run_orchestration.program_runner import advance_program
from packages.domain.core import ID, Timestamp
from packages.domain.evidence import ReviewFinding
from packages.domain.program import (
    ProgramContinueRule,
    ProgramDecisionKind,
    ResearchProgram,
)
from packages.domain.run import ResearchRun

ACCEPT = "ACCEPT"
REVISE = "REVISE"


class _FindingReader:
    """极小的评审结论读取面（只实现驱动用到的 `for_run`）。"""

    def __init__(self, verdicts: dict[str, str]) -> None:
        self._verdicts = verdicts

    def for_run(self, run_id: str) -> tuple[object, ...]:
        verdict = self._verdicts.get(run_id)
        if verdict is None:
            return ()
        finding = ReviewFinding(
            id=f"finding-{run_id}",
            review_type="ACCEPTANCE",
            verdict=verdict,
            findings=[f"逐字判词：{verdict}"],
            reviewed_by="gate:reviewer_a",
            reviewed_at=Timestamp.now(),
        )
        return (type("Scoped", (), {"finding": finding})(),)


class _Harness:
    def __init__(self, *, max_runs: int = 3, rule: tuple[str, ...] = (ACCEPT,)) -> None:
        self.conn: sqlite3.Connection = connect(":memory:")
        self.conn.executescript(RUNS_SCHEMA_SQL)
        self.runs = SqliteRunStore(connection=self.conn)
        self.programs = SqliteProgramStore()
        self.program = ResearchProgram(
            id=f"prog-{uuid.uuid4().hex[:8]}",
            project_id="p1",
            protocol_id="proto",
            max_runs=max_runs,
            continue_rule=ProgramContinueRule(verdict_in=rule),
        )
        self.programs.create(self.program)
        self.started: list[str] = []

    def start_run(self, index: int) -> str:
        run = ResearchRun(
            id=ID(str(uuid.uuid4())),
            project_id="p1",
            protocol_id="proto",
            program_id=self.program.id,
            program_index=index,
        )
        self.runs.save_run(run)
        self.started.append(run.id.value)
        return run.id.value

    def seed_run(self, index: int, *, state: str = "SUCCEEDED") -> str:
        run = ResearchRun(
            id=ID(str(uuid.uuid4())),
            project_id="p1",
            protocol_id="proto",
            state=state,
            program_id=self.program.id,
            program_index=index,
        )
        self.runs.save_run(run)
        return run.id.value

    def verdicts(self, mapping: dict[str, str]) -> _FindingReader:
        return _FindingReader(mapping)


def test_start_when_program_is_empty() -> None:
    h = _Harness()
    result = advance_program(h.program, runs=h.runs, programs=h.programs, start_run=h.start_run)
    assert result.decision.kind is ProgramDecisionKind.START
    assert result.started_run_id == h.started[0]
    assert result.run_count == 1
    assert h.runs.for_program(h.program.id)[0].program_index == 1


def test_wait_while_last_run_is_not_terminal() -> None:
    h = _Harness()
    h.seed_run(1, state="RUNNING")
    result = advance_program(h.program, runs=h.runs, programs=h.programs, start_run=h.start_run)
    assert result.decision.kind is ProgramDecisionKind.WAIT
    assert result.started_run_id is None
    assert len(h.runs.for_program(h.program.id)) == 1  # 没有产生第二个 run
    assert "state=RUNNING" in result.decision.cited_facts


def test_stop_rule_cites_the_verbatim_verdict() -> None:
    h = _Harness()
    run_id = h.seed_run(1)
    result = advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        findings=h.verdicts({run_id: REVISE}),
        start_run=h.start_run,
    )
    assert result.decision.kind is ProgramDecisionKind.STOP_RULE
    assert result.started_run_id is None
    assert result.decision.cited_facts == ("verdict REVISE",)
    assert REVISE in result.decision.reason
    assert h.started == []


def test_continue_starts_the_next_round() -> None:
    h = _Harness()
    run_id = h.seed_run(1)
    result = advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        findings=h.verdicts({run_id: ACCEPT}),
        start_run=h.start_run,
    )
    assert result.decision.kind is ProgramDecisionKind.CONTINUE
    assert result.decision.cited_facts == ("verdict ACCEPT",)
    assert result.started_run_id == h.started[0]
    assert h.runs.for_program(h.program.id)[-1].program_index == 2


def test_guardrail_is_distinguishable_from_the_conclusion_stop() -> None:
    h = _Harness(max_runs=1)
    run_id = h.seed_run(1)
    result = advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        findings=h.verdicts({run_id: ACCEPT}),
        start_run=h.start_run,
    )
    assert result.decision.kind is ProgramDecisionKind.STOP_GUARDRAIL
    assert "max_runs=1" in result.decision.reason
    # 与结论面判停**可区分**：种类不同是判据面的事实（不是措辞）。
    assert result.decision.kind.value != ProgramDecisionKind.STOP_RULE.value
    assert h.started == []


def test_replay_does_not_start_a_second_run_at_the_same_index() -> None:
    """崩溃窗口：上一条 `CONTINUE` 认领的 run 没落库 ⇒ `DEDUP`，不产生第二个 run。"""
    h = _Harness()
    first = h.seed_run(1)
    claimed = str(uuid.uuid4())
    # 第一次推进：结论面判「续」，启动面**返回了 id 但 run 没落库**（等价于返回后进程崩了）。
    first_advance = advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        findings=h.verdicts({first: ACCEPT}),
        start_run=lambda index: claimed,
    )
    assert first_advance.decision.kind is ProgramDecisionKind.CONTINUE
    assert h.runs.for_program(h.program.id)[-1].program_index == 1  # 序号 2 没落库
    result = advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        findings=h.verdicts({first: ACCEPT}),
        start_run=h.start_run,
    )
    assert result.decision.kind is ProgramDecisionKind.DEDUP
    assert result.decision.cited_run_id == claimed
    assert result.started_run_id is None
    assert h.started == []
    assert len(h.runs.for_program(h.program.id)) == 1


def test_missing_start_face_is_named_not_faked() -> None:
    h = _Harness()
    result = advance_program(h.program, runs=h.runs, programs=h.programs, start_run=None)
    assert result.decision.kind is ProgramDecisionKind.WAIT
    assert "未提供启动面" in result.decision.reason
    assert result.started_run_id is None
    assert h.runs.for_program(h.program.id) == ()
