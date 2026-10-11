"""GOAL-20261011-056（`Z-3`）：**等待面有始点、可催办（有界）** —— EC-02 / EC-03 的判据。

**为什么单列**：`tests/application/run_orchestration/test_program_waiting_on_the_run_path.py`
已 420+ 行；本轮的靶子（时间侧）自成一组。

**判的是什么**：等待面此前**在时间维度上不可判定** —— 声明的闸门可以永远挂着而**没有信号**。
本轮加：**始点**（时长）与**有界的超期点名**（**只点名**，**不**自动放行 / 拒绝）。
**不读挂钟**：两个时点都由调用方给 ⇒ 同一份记录 + 同一对时点 ⇒ 判词**必相同**。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from packages.application.run_orchestration.program_waiting import (
    GateClock,
    GateInputs,
    declared_gate_pending,
)
from packages.domain.core import Timestamp
from tests.application.run_orchestration.test_program_waiting_on_the_run_path import (
    _ApprovalRows,
    _Harness,
    _row,
)

_BASE = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)


def _clock(*, waited_seconds: int) -> GateClock:
    """一对时点：`now` 比 `waited_since` 晚这么多秒。"""
    return GateClock(
        now=Timestamp(_BASE),
        waited_since=Timestamp(_BASE - timedelta(seconds=waited_seconds)),
    )


def _gated(*, bound: int | None, gate: int = 1, max_runs: int = 3) -> Any:
    """一个声明了闸门（可选声明时限界）的程序 + 一条停在等待态的 run。"""
    h = _Harness(max_runs=max_runs)
    h.program = replace(h.program, human_gate_at_index=gate, gate_nudge_after_seconds=bound)
    h.programs.create(h.program)
    run_id = h.seed_run(gate, state="AWAITING_HUMAN")
    h._run_id = run_id  # type: ignore[attr-defined]
    return h


def _pending(h: Any, inputs: GateInputs | None = None) -> str | None:
    return declared_gate_pending(
        h.program,
        h.program.human_gate_at_index or 1,
        _ApprovalRows([_row("apr-1")]),
        h._run_id,
        inputs,
    )


def test_the_waiting_face_reports_how_long_it_has_waited() -> None:
    """EC-02：给了时点 ⇒ 判词里**报出已等待的秒数**（始点可读）。"""
    h = _gated(bound=None)
    note = _pending(h, GateInputs(clock=_clock(waited_seconds=90)))
    assert note is not None, "闸门触发时必须返回点名句"
    assert "已等待 90 秒" in note, note


def test_the_same_clock_gives_the_same_verdict() -> None:
    """EC-02：**同一对时点 ⇒ 判词逐字相同**（不读挂钟 ⇒ 可复现）。"""
    h = _gated(bound=None)
    first = _pending(h, GateInputs(clock=_clock(waited_seconds=90)))
    second = _pending(h, GateInputs(clock=_clock(waited_seconds=90)))
    assert first == second, (first, second)


def test_without_a_clock_nothing_about_duration_is_reported() -> None:
    """EC-02 + 反证臂：**不给时点** ⇒ **逐字不含**任何时长（**不猜**）。

    受判面**必须可区分**：本条与上一条的唯一差别是**给不给时点** ——
    两条放在一起才证明「报了时长」是**因为**调用方给了时点，而不是凭空读的。
    """
    h = _gated(bound=None)
    note = _pending(h, None)
    assert note is not None
    assert "已等待" not in note, ("不给时点不得报时长", note)
    assert "秒" not in note, ("不给时点不得出现任何秒数", note)


def test_before_the_bound_only_the_duration_is_reported() -> None:
    """EC-03：**未超过声明的界** ⇒ 只报时长 + 「未超过」（**不**说「等太久」）。"""
    h = _gated(bound=600)
    note = _pending(h, GateInputs(clock=_clock(waited_seconds=90)))
    assert note is not None
    assert "已等待 90 秒" in note, note
    assert "未超过声明的界 600 秒" in note, note
    assert "等太久了" not in note, ("未超期不得说「等太久」", note)


def test_at_or_beyond_the_bound_is_named_as_nudging() -> None:
    """EC-03：**达到/超过界** ⇒ **点名**「等太久了」，并写明**决定权仍在人**。"""
    h = _gated(bound=600)
    note = _pending(h, GateInputs(clock=_clock(waited_seconds=600)))
    assert note is not None
    assert "等太久了" in note, note
    assert "决定权仍在人" in note, ("必须写明不自动放行", note)
    assert "不自动放行" in note, note


def test_an_undeclared_bound_never_names_overdue() -> None:
    """EC-03 + 反证臂：**未声明界** ⇒ 即使等了很久**也**不报超期（既有行为逐字不变）。"""
    h = _gated(bound=None)
    note = _pending(h, GateInputs(clock=_clock(waited_seconds=999_999)))
    assert note is not None
    assert "等太久了" not in note, ("未声明界不得报超期", note)
    assert "已等待 999999 秒" in note, ("时长仍要报（那是无界的）", note)


@pytest.mark.parametrize("bad_bound", [0, -1])
def test_a_non_positive_bound_is_rejected_by_name(bad_bound: int) -> None:
    """EC-03：界必须是**正整数**（零 / 负 ⇒ **点名拒绝** —— 不静默当成「不催」）。"""
    with pytest.raises(ValueError, match="must be a positive integer"):
        _gated(bound=bad_bound)
    # 受判面**可区分**：合法界**不**报错（证明上一行判的是**界本身**而非「有没有声明」）。
    assert _gated(bound=1).program.gate_nudge_after_seconds == 1
