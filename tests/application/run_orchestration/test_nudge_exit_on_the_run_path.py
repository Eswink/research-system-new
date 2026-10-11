"""GOAL-20261011-057（`Z-3` 出口侧）：**超期信号有出口** —— EC-02 / EC-03 的判据。

**为什么单列**：本轮的靶子（可注入出口 + 静默缺省 + 只读纪律）自成一组。

**判的是什么**：序 24 让等待面**能判超期**（判词点名「等太久了」），但那条信号
**只能在被拉取时读**（`NudgeSink` / `notify(` / `dispatch_notification` / `escalate`
三根全零命中）⇒ 人不去问就永远不知道。本轮把它接一个**可注入的出口**：
**缺省不送**（未注入 ⇒ 逐字不变）；**超期才送**；**送失败点名**（不吞异常、不改变判定）。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any

from packages.application.ports.nudge_sink import NudgeNotice, NullNudgeSink
from packages.application.run_orchestration.program_waiting import GateClock
from packages.domain.core import Timestamp
from tests.application.run_orchestration.test_program_waiting_on_the_run_path import (
    _ApprovalRows,
    _Harness,
    _row,
)

_BASE = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)


class _RecordingSink:
    """**记录型出口**（测试夹具）：把收到的通知收集起来。"""

    def __init__(self) -> None:
        self.seen: list[NudgeNotice] = []

    def nudge(self, notice: NudgeNotice) -> None:
        self.seen.append(notice)


class _BrokenSink:
    """**故障出口**：每次调用都抛（用来验「点名而非静默」）。"""

    def nudge(self, notice: NudgeNotice) -> None:
        raise RuntimeError("exit is down")


def _clock(*, waited_seconds: int) -> GateClock:
    return GateClock(
        now=Timestamp(_BASE),
        waited_since=Timestamp(_BASE - timedelta(seconds=waited_seconds)),
    )


def _gated(*, bound: int | None, gate: int = 1, max_runs: int = 3) -> Any:
    h = _Harness(max_runs=max_runs)
    h.program = replace(h.program, human_gate_at_index=gate, gate_nudge_after_seconds=bound)
    h.programs.create(h.program)
    run_id = h.seed_run(gate, state="SUCCEEDED")
    h._run_id = run_id  # type: ignore[attr-defined]
    return h


def _advance(h: Any, *, clock: GateClock | None, nudges: Any) -> Any:
    """带时钟与出口推进一次（其余读入与既有 harness 同形）。"""
    from packages.application.run_orchestration.program_runner import advance_program

    return advance_program(
        h.program,
        runs=h.runs,
        programs=h.programs,
        findings=h.verdicts({h._run_id: "ACCEPT"}),
        approvals=_ApprovalRows([_row("apr-nudge")]),
        clock=clock,
        nudges=nudges,
    )


def test_an_overdue_wait_is_handed_to_the_injected_sink() -> None:
    """EC-03：**超期 + 注入出口** ⇒ 信号**被交给出口**（含标识 / 序号 / 秒数 / 界）。"""
    h = _gated(bound=600)
    sink = _RecordingSink()
    result = _advance(h, clock=_clock(waited_seconds=900), nudges=sink)
    assert len(sink.seen) == 1, sink.seen
    notice = sink.seen[0]
    assert notice.index == h.program.human_gate_at_index, notice
    assert notice.waited_seconds == 900, notice
    assert notice.declared_bound_seconds == 600, notice
    assert result.decision.kind.value == "WAIT_FOR_APPROVAL", result.decision
    assert any("nudge delivered" in item for item in result.decision.cited_facts), (
        result.decision.cited_facts
    )


def test_a_wait_within_the_bound_is_not_handed_out() -> None:
    """EC-02 + 反证臂：**未超期** ⇒ **不送**（受判面**必须可区分**：与上条只差秒数）。"""
    h = _gated(bound=600)
    sink = _RecordingSink()
    _advance(h, clock=_clock(waited_seconds=90), nudges=sink)
    assert sink.seen == [], ("未超期不得送", sink.seen)


def test_without_an_injected_sink_the_overdue_wait_is_silently_dropped() -> None:
    """EC-02：**未注入** ⇒ **缺省不送**（**不是故障** —— 没注入就是没人接）。"""
    h = _gated(bound=600)
    result = _advance(h, clock=_clock(waited_seconds=900), nudges=None)
    assert result.decision.kind.value == "WAIT_FOR_APPROVAL", result.decision
    assert not any("nudge" in item for item in result.decision.cited_facts), (
        "未注入时不得出现任何交付事实",
        result.decision.cited_facts,
    )


def test_an_undeclared_bound_is_never_handed_out() -> None:
    """EC-02 + 反证臂：**未声明界** ⇒ 即使等了很久也**不送**（既有行为逐字不变）。"""
    h = _gated(bound=None)
    sink = _RecordingSink()
    _advance(h, clock=_clock(waited_seconds=999_999), nudges=sink)
    assert sink.seen == [], ("未声明界不得送", sink.seen)


def test_a_missing_clock_is_never_handed_out() -> None:
    """EC-02：**未给时点** ⇒ 算不出时长 ⇒ **也不送**（**不猜**）。"""
    h = _gated(bound=600)
    sink = _RecordingSink()
    _advance(h, clock=None, nudges=sink)
    assert sink.seen == [], ("不给时点不得送（不猜时长）", sink.seen)


def test_a_broken_sink_is_named_not_swallowed() -> None:
    """EC-03：**送失败被点名**（**不吞异常**），且**不改变判定**（闸门照样拦）。

    与 `TelemetrySink` 的 fail-open 的**关键差别**：观测面丢失可接受，
    而「该让人知道的事没送出去」**必须能被读出来** ⇒ 否则就是静默降级。
    """
    h = _gated(bound=600)
    result = _advance(h, clock=_clock(waited_seconds=900), nudges=_BrokenSink())
    assert result.decision.kind.value == "WAIT_FOR_APPROVAL", ("判定不受影响", result.decision)
    assert any("nudge not delivered" in item for item in result.decision.cited_facts), (
        "送失败必须被点名",
        result.decision.cited_facts,
    )
    assert any("exit is down" in item for item in result.decision.cited_facts), (
        "点名要带上原因",
        result.decision.cited_facts,
    )


def test_the_null_sink_is_silent_and_its_call_log_is_empty() -> None:
    """EC-02：**静默缺省**的形状 —— `NullNudgeSink` 无副作用且 `calls` 恒空。"""
    sink = NullNudgeSink()
    sink.nudge(NudgeNotice("p", "r", 1, 900, 600))
    assert sink.calls == (), ("Null 的调用日志必须为空（静默的可复核证据）", sink.calls)


def test_the_judgment_face_stays_read_only() -> None:
    """EC-03 + `T-4` 的受判面：**只读判定面**（`program_waiting`）**不得**出现端口调用。

    端口调用必须留在**调用方那侧**（桥模块）—— 序 12/14 起的既有判据钉住这条纪律。
    """
    from pathlib import Path

    waiting = Path("packages/application/run_orchestration/program_waiting.py").read_text(
        encoding="utf-8"
    )
    assert "nudge(" not in waiting, ("判定面不得调端口", "nudge(" in waiting)
    assert "NudgeSink" not in waiting, "判定面不得 import 端口"
