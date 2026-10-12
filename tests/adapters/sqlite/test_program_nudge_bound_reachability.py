"""GOAL-20261012-059（序 27）：**时限链在产品面上可达** —— EC-02 / EC-03 的判据。

**为什么单列**：本轮的靶子（界可声明 + 可落库 + 出口可注入）横跨 DTO / 两库 / 组合根三层，
自成一组；与 `test_gate_nudge_on_the_run_path.py`（序 24 的判定语义）**分工不同** ——
那一组判「超期怎么判」，本组判「**产品面上有没有东西能到达它**」。

**判的是什么**：序 24 让等待面**有始点、能判超期**（`gate_nudge_after_seconds`）、
序 25 让那条信号**有可注入的出口**（`NudgeSink`）—— 但**实跑取证**三层全断：
① 两个 DTO **没有该键**；② 两库 round-trip **静默丢弃**（实测进程内 `60` ⇒ 读回 `None`）；
③ `services/` 对 `nudges=` **零命中**（出口从不被注入）。本轮把这**三段接线**补上。

**缺省形态逐字不变**：未声明界 ⇒ 不报超期（与改动前逐字相同）；未注入出口 ⇒ 不送。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from adapters.sqlite.program_store import SqliteProgramStore
from packages.application.ports.nudge_sink import NullNudgeSink
from packages.domain.program import ProgramContinueRule, ResearchProgram
from services.api.dto.programs import ProgramCreateDto, ProgramDetailDto

_ROOT = Path(__file__).resolve().parents[3]
BOUND = 60


def _program(**overrides: object) -> ResearchProgram:
    base: dict[str, object] = {
        "id": "prog-nudge",
        "project_id": "p1",
        "protocol_id": "proto",
        "max_runs": 3,
        "continue_rule": ProgramContinueRule(verdict_in=("ACCEPT",)),
        "human_gate_at_index": 1,
    }
    base.update(overrides)
    return ResearchProgram(**base)  # type: ignore[arg-type]


def test_the_bound_survives_a_sqlite_round_trip() -> None:
    """EC-02：声明的界经 SQLite round-trip **原样读回**（改动前：静默丢弃成 `None`）。"""
    store = SqliteProgramStore(":memory:")
    store.create(_program(gate_nudge_after_seconds=BOUND))
    assert store.get("prog-nudge").gate_nudge_after_seconds == BOUND


def test_the_bound_round_trips_through_for_project_too() -> None:
    """EC-02：`for_project` 走**另一条 SQL**（列清单两处各写一份）⇒ 两处都要带列。"""
    store = SqliteProgramStore(":memory:")
    store.create(_program(gate_nudge_after_seconds=BOUND))
    (only, *rest) = store.for_project("p1")
    assert rest == []
    assert only.gate_nudge_after_seconds == BOUND


def test_the_undeclared_bound_stays_none_not_zero() -> None:
    """EC-02：**未声明**读回 `None`（不是 `0`）—— 域层「必须是正整数」把两者分成两件事。"""
    store = SqliteProgramStore(":memory:")
    store.create(_program())
    assert store.get("prog-nudge").gate_nudge_after_seconds is None


def test_the_create_dto_accepts_the_bound_declaration() -> None:
    """EC-02：建程序面**可声明**界（改动前：该键不在 `model_fields` 里）。"""
    dto = ProgramCreateDto(protocol_path="p.yaml", gate_nudge_after_seconds=BOUND)
    assert dto.gate_nudge_after_seconds == BOUND


def test_the_create_dto_defaults_to_undeclared() -> None:
    """EC-02：不声明 ⇒ `None`（既有请求逐字不变）。"""
    assert ProgramCreateDto(protocol_path="p.yaml").gate_nudge_after_seconds is None


def test_the_detail_dto_carries_the_bound() -> None:
    """EC-02：读面**披露**界（改动前：该键不在 `model_fields` 里）。"""
    assert "gate_nudge_after_seconds" in ProgramDetailDto.model_fields


def test_both_dtos_expose_the_key_now() -> None:
    """EC-02：两个 DTO 都有该键 —— 受判面是**两个**（少一个即「读得出、写不进」或反之）。"""
    for model in (ProgramCreateDto, ProgramDetailDto):
        assert "gate_nudge_after_seconds" in model.model_fields, model.__name__


def test_a_non_positive_bound_is_refused_by_the_schema() -> None:
    """EC-02：坏界**点名拒绝**（`ge=1`）—— 零 / 负不得被静默接受。"""
    with pytest.raises(ValueError):
        ProgramCreateDto(protocol_path="p.yaml", gate_nudge_after_seconds=0)


def test_the_store_still_refuses_a_bad_bound_at_the_domain_layer() -> None:
    """EC-02：域校验**一字不动** —— 绕过 DTO 直构域对象仍被点名拒绝。"""
    with pytest.raises(ValueError, match="positive integer"):
        _program(gate_nudge_after_seconds=0)


def test_the_composition_root_injects_a_nudge_sink_by_default() -> None:
    """EC-03：组合根的依赖面**有**这个可注入字段（改动前：`services/` 零命中）。"""
    source = (_ROOT / "services" / "api" / "composition.py").read_text(encoding="utf-8")
    assert "NudgeSink" in source, "组合根必须**引用**该端口（缺省注入的落点）"
    assert "NullNudgeSink" in source, "缺省实现必须是静默的那个（不注入 ⇒ 逐字不变）"


def test_the_advance_route_hands_the_sink_over() -> None:
    """EC-03：推进路由把出口**交给**既有推进入口（改动前：`nudges=` 零命中）。"""
    source = (_ROOT / "services" / "api" / "routers" / "programs.py").read_text(encoding="utf-8")
    assert "nudges=deps.nudges" in source, "推进路由必须把组合根的出口传下去"


def test_the_declared_bound_reaches_the_judgement_on_the_product_path() -> None:
    """EC-02 的产品面一半：**从库里读回**的界真的参与判定（不是进程内直传的对象）。

    这一条正是**改动前做不到的形态**：此前界不落库 ⇒ 从 store 读回的 `program`
    恒为「未声明界」⇒ 判词里**永远**不会出现界。受判面 = **store 读回的对象**。
    """
    from datetime import datetime, timedelta, timezone

    from packages.application.run_orchestration.program_runner import advance_program
    from packages.application.run_orchestration.program_waiting import GateClock
    from packages.domain.core import Timestamp
    from tests.application.run_orchestration.test_program_waiting_on_the_run_path import (
        _ApprovalRows,
        _Harness,
        _row,
    )

    base = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
    h = _Harness()
    # 用**同一 id** 重声明（harness 预建的行是 `INSERT OR IGNORE` 建的 ⇒ 二次 create 是空操作）
    # 只好直写一行：这正是「界不落库」的现场 —— 建库那一侧此前**没有这一列**。
    declared = replace(h.program, human_gate_at_index=1, gate_nudge_after_seconds=BOUND)
    h.programs._conn.execute(  # noqa: SLF001 - 测试直写：绕开 `create` 的 IGNORE 语义
        "UPDATE research_programs SET human_gate_at_index = ?, gate_nudge_after_seconds = ?"
        " WHERE program_id = ?",
        (1, BOUND, declared.id),
    )
    h.programs._conn.commit()  # noqa: SLF001
    from_store = h.programs.get(declared.id)
    assert from_store.gate_nudge_after_seconds == BOUND, "界必须先真的落库（本 GOAL 的靶子）"
    run_id = h.seed_run(1, state="SUCCEEDED")
    clock = GateClock(
        now=Timestamp(base),
        waited_since=Timestamp(base - timedelta(seconds=BOUND * 2)),
    )
    result = advance_program(
        from_store,
        runs=h.runs,
        programs=h.programs,
        findings=h.verdicts({run_id: "ACCEPT"}),
        approvals=_ApprovalRows([_row("apr-bound")]),
        clock=clock,
    )
    assert f"超过声明的界 {BOUND} 秒" in result.decision.reason, result.decision.reason


def test_the_default_sink_is_silent_and_has_no_calls() -> None:
    """EC-03：缺省出口**静默**（`calls` 恒空 = 静默的可复核证据）。"""
    sink = NullNudgeSink()
    sink.nudge(_notice())  # type: ignore[arg-type]
    assert sink.calls == ()


def _notice() -> object:
    from packages.application.ports.nudge_sink import NudgeNotice

    return NudgeNotice(
        program_id="p",
        run_id="r",
        index=1,
        waited_seconds=1,
        declared_bound_seconds=1,
    )


def test_replace_keeps_the_bound_when_unrelated_fields_change() -> None:
    """EC-02：界与其它字段**正交**（改 `max_runs` 不带掉界 —— 承 `D-1` 的正交口径）。"""
    program = _program(gate_nudge_after_seconds=BOUND)
    assert replace(program, max_runs=5).gate_nudge_after_seconds == BOUND
