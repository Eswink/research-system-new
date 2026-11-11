"""`build_review_outcome` 非程序 run 的判据（GOAL-20261111-108 EC-05）。

**它封住的失败形态**：`run` 不属于任何程序时原实现抛 `ValueError`，而那段构造在
`with_review_outcome` 里、后者在**每个**任务前都被调用 ⇒ 任何非程序 run 走 **resume** 时
（那时 run 行已落库，`get_run` 不再 `KeyError`）必然在第一个任务上抛错；叠加当时装配面
**没有异常边界**（EC-04）⇒ 静默停住，与 GOAL-106 `F-17` 同形。

三条臂：① 非程序 run ⇒ 空视图且 `reason` 点名 `NO_PROGRAM`；② **不抛**；
③ 三种「空」互相**分得开**（`NO_PROGRAM` / `NO_PRIOR_RUN` / `NO_RUN_ROW`）。
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from packages.application.run_orchestration.review_outcome import (
    NO_PRIOR_RUN,
    NO_PROGRAM,
    NO_RUN_ROW,
    build_review_outcome,
)


@dataclass(frozen=True)
class _Id:
    value: str


@dataclass(frozen=True)
class _Run:
    id: _Id
    program_id: str | None = None


class _Runs:
    """最小 `RunStore`（只有 `get_run` 与 `for_program` —— `build_review_outcome` 只用这两个）。"""

    def __init__(self, runs: tuple[_Run, ...]) -> None:
        self._runs = runs

    def get_run(self, run_id: str) -> _Run:
        for run in self._runs:
            if run.id.value == run_id:
                return run
        raise KeyError(run_id)

    def for_program(self, program_id: str) -> tuple[_Run, ...]:
        return tuple(run for run in self._runs if run.program_id == program_id)


class _Findings:
    def for_run(self, run_id: str) -> tuple[()]:
        del run_id
        return ()


def _reason(view: object) -> str:
    """空视图的点名理由（字段名以实现为准，两者取非空那个）。"""
    for attribute in ("reason", "unavailable_reason"):
        value = getattr(view, attribute, None)
        if value:
            return str(value)
    return ""


def test_a_run_outside_any_program_gets_an_empty_view_not_an_exception() -> None:
    """①② 非程序 run ⇒ 空视图 + `NO_PROGRAM` 点名，**且不抛**（resume 不再停住）。

    这是本 EC 的核心：原实现抛 `ValueError`，而 resume 时 run 行**已**落库 ⇒ 每个任务
    前都炸 ⇒ 静默停住。
    """
    runs = _Runs((_Run(id=_Id("run-bare"), program_id=None),))
    view = build_review_outcome(runs, _Findings(), run_id="run-bare")
    assert NO_PROGRAM in _reason(view), f"空视图理由里缺 NO_PROGRAM：{_reason(view)!r}"


def test_a_program_run_without_a_prior_round_says_no_prior_run() -> None:
    """③a 有程序但无前序 ⇒ `NO_PRIOR_RUN`。"""
    runs = _Runs((_Run(id=_Id("run-first"), program_id="prog-1"),))
    view = build_review_outcome(runs, _Findings(), run_id="run-first")
    reason = _reason(view)
    assert NO_PRIOR_RUN in reason, reason
    assert NO_PROGRAM not in reason, "两种「空」被混成一种"


def test_a_run_row_that_is_not_persisted_yet_says_no_run_row() -> None:
    """③b 行还没落库 ⇒ `NO_RUN_ROW`（既有语义不回归）。"""
    runs = _Runs(())
    view = build_review_outcome(runs, _Findings(), run_id="run-missing")
    reason = _reason(view)
    assert NO_RUN_ROW in reason, reason
    assert NO_PROGRAM not in reason and NO_PRIOR_RUN not in reason


@pytest.mark.parametrize(
    ("runs", "run_id", "expected"),
    [
        ((), "absent", NO_RUN_ROW),
        ((_Run(id=_Id("bare"), program_id=None),), "bare", NO_PROGRAM),
        ((_Run(id=_Id("first"), program_id="p1"),), "first", NO_PRIOR_RUN),
    ],
)
def test_the_three_kinds_of_empty_stay_distinguishable(
    runs: tuple[_Run, ...], run_id: str, expected: str
) -> None:
    """三种「空」**互不覆盖**：任意两者不得互相包含对方的标记。

    这一条是上三条的并集检查 —— 「没有行」/「没有程序」/「没有前序」是三个不同的
    事实，读面必须分得开（否则排查只能猜）。
    """
    view = build_review_outcome(_Runs(runs), _Findings(), run_id=run_id)
    reason = _reason(view)
    assert expected in reason, reason
    others = {NO_RUN_ROW, NO_PROGRAM, NO_PRIOR_RUN} - {expected}
    for other in others:
        assert other not in reason, f"{expected} 的视图里混进了 {other}"
