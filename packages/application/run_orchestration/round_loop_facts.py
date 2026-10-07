"""结论驱动的停止判据：读**本轮结论的可观察事实**（GOAL-20261008-034 EC-02）。

**它与 `max_rounds` 的分工**（MAINLINE 深度轴的核心要求）：

- `max_rounds` 是**护栏**：防止「结论永不收敛」把循环拖成无限（也防预算被烧光）；
- 本模块的判据是**停止规则**：读本轮产出的**可观察事实**（不是轮数、不是墙钟），
  据此决定「还有没有必要再来一轮」。

**为什么判据名是词表而不是 lambda**：lambda 会把判定逻辑搬回调用点，于是「这一轮为什么
停」在记录里就只剩一个匿名函数 —— 而 EC-02 要求**停止理由可读、可区分**。词表 + 一个
读事实的纯函数，让「跑了哪条判据、读到了什么值」都能逐字进事件链。

**判据 `converged_no_new_ids`（本轮射程）**：上一轮的产出里**没有出现任何新标识**
（相对它之前出现过的全部标识）⇒ 再做一轮也拿不到新东西 ⇒ 停。
「新」是**集合差**，不是计数比较：标识集合单调累积，只在**严格更大**时才继续。

边界（如实登记）：本判据只覆盖「标识型」结论的收敛。别的收敛形态（数值平台期、
证据饱和）**未实现** —— 它们需要各自的读事实函数，不在本轮射程（GOAL 的未覆盖节逐条写）。
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from packages.application.run_orchestration.round_loop import (
    CONVERGED_NO_NEW_IDS,
    STOP_BY_CONCLUSION,
    STOP_BY_GUARD,
)


@dataclass(frozen=True, slots=True)
class RoundFact:
    """一轮结束时读到的**可观察事实**（停止判据的输入；进事件链的原始读数）。"""

    round_index: int
    ids: tuple[str, ...]
    seen_before: tuple[str, ...]

    @property
    def new_ids(self) -> tuple[str, ...]:
        """本轮相对**之前全部轮次**新增的标识（集合差；顺序按本轮产出顺序）。"""
        before = set(self.seen_before)
        return tuple(item for item in self.ids if item not in before)


@dataclass(frozen=True, slots=True)
class StopDecision:
    """停止结论：**谁**让循环停（结论 / 护栏）+ 读到的**值**（逐字进事件链）。"""

    stop: bool
    kind: str
    criterion: str
    fact: RoundFact

    def __post_init__(self) -> None:
        if self.stop and self.kind not in (STOP_BY_CONCLUSION, STOP_BY_GUARD):
            raise ValueError(f"unknown stop kind {self.kind!r}")
        if self.stop and not self.criterion:
            raise ValueError("a stop decision must name its criterion")


def evaluate_stop(
    *,
    criterion: str,
    fact: RoundFact,
    round_index: int,
    max_rounds: int,
) -> StopDecision:
    """本轮结束后的停止判定（**顺序固定**：先说结论、再谈护栏）。

    顺序不是装饰：若先判护栏，一个刚好跑到上界的 run 会被读成「护栏停的」，
    而它其实**结论也已经收敛了** —— 那会把「结论驱动生效」谎报成「只是上界到了」。
    本函数因此**永远**先评估结论判据；护栏只在结论没停时才说话。
    """
    conclusion_stop = criterion == CONVERGED_NO_NEW_IDS and not fact.new_ids
    if conclusion_stop:
        return StopDecision(stop=True, kind=STOP_BY_CONCLUSION, criterion=criterion, fact=fact)
    if round_index >= max_rounds:
        return StopDecision(stop=True, kind=STOP_BY_GUARD, criterion="max_rounds", fact=fact)
    return StopDecision(stop=False, kind="", criterion="", fact=fact)


def ids_from_step_outputs(outputs: Iterable[Mapping[str, Any]]) -> tuple[str, ...]:
    """从本轮各步的运行链产出的**内容**里取标识（去重保序）。

    形态与既有派生链一致：`literature.search` / `literature.read` 的返回是
    `{"content": {...}, ...}`，标识在 `content.ids`（点分路径由**声明**给出，
    这里只处理本判据读的那一种事实 —— 别的形态要点名而不是静默当成空）。

    取不到 `content.ids` 的产出**跳过**（它本轮的产出不是标识型）；**整轮都没有**
    标识 ⇒ 返回空元组 ⇒ 判据判「无新标识」⇒ 停（这正是「这一轮没带来新东西」的语义）。
    """
    out: list[str] = []
    for item in outputs:
        content = item.get("content")
        if not isinstance(content, Mapping):
            continue
        raw = content.get("ids")
        if not isinstance(raw, list):
            continue
        for value in raw:
            text = str(value)
            if text and text not in out:
                out.append(text)
    return tuple(out)


__all__ = [
    "RoundFact",
    "StopDecision",
    "evaluate_stop",
    "ids_from_step_outputs",
]
