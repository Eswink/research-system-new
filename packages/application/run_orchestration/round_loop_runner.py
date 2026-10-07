"""多轮循环的**执行面**：把 `RoundLoop` 声明变成真的重复执行（GOAL-20261008-034 EC-01）。

**为什么单列**：`phase_runner.py` 已 409 行、`service.py` 恰在 450 行硬上限 ⇒ 循环控制
不能塞进任何一处。本模块只做循环控制，相位/任务的执行仍**全部复用**既有件
（`_execute_phase_group` / `_run_group_task` / `stop` 判定）；它**不复制**任何执行逻辑。

**懒展开（关键设计）**：没有在解析期就把 N 轮全展开 —— 那会让「停止判据」变成装饰
（任务已全部提交，轮次照跑）。本模块的做法是：每轮**开始时**才解析该轮的 specs，跑完该轮
后**读本轮产出**判定是否继续；判「停」就**不再解析**下一轮。

三条**点名失败**（不静默）：

- `RoundLoop.phases` 声明的 phase 在编译计划里不存在 ⇒ 点名；
- 某个 phase 的展开 id 在同一轮里重复 ⇒ 点名（那会让同轮两个任务撞 idempotency key）；
- 判据名不在词表 ⇒ 由 `RoundLoop.__post_init__` 在装配期就拒（不等到执行）。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from packages.application.run_orchestration.round_loop import (
    STOP_BY_CONCLUSION,
    RoundLoop,
    find_loop,
)
from packages.application.run_orchestration.round_loop_facts import (
    RoundFact,
    evaluate_stop,
    ids_from_step_outputs,
)

if TYPE_CHECKING:  # 只为类型：避免与 phase_runner 形成导入环
    from packages.application.run_orchestration.outcomes import RunOutcome


@dataclass(slots=True)
class RoundLoopState:
    """一条循环的**运行事实**（进事件链的原始读数；不是内部计数器）。

    `facts` 每轮一条（含该轮读到的标识与截至该轮前的全部标识）⇒ 停止判定与
    「这一轮为什么停」都可逐条复读，而不是只有一个最终结论。
    """

    loop: RoundLoop
    facts: list[RoundFact] = field(default_factory=list)
    rounds_run: int = 0
    stopped_by: str = ""
    stop_criterion: str = ""

    @property
    def seen_ids(self) -> tuple[str, ...]:
        """截至当前轮**累计**出现过的全部标识（停止判据的比较基准）。"""
        seen: list[str] = []
        for fact in self.facts:
            for item in fact.ids:
                if item not in seen:
                    seen.append(item)
        return tuple(seen)

    def record_round(self, round_index: int, outputs: Sequence[Mapping[str, Any]]) -> None:
        """把一轮的产出读成事实（`new_ids` 由已记录的 `seen_before` 推出）。"""
        before = self.seen_ids
        self.facts.append(
            RoundFact(
                round_index=round_index,
                ids=ids_from_step_outputs(outputs),
                seen_before=before,
            )
        )
        self.rounds_run = round_index

    def decide(self) -> Any:
        """本轮结束后的停止判定（读**最后一条事实**；顺序由 `evaluate_stop` 固定）。"""
        assert self.facts, "decide() requires a recorded round"
        fact = self.facts[-1]
        decision = evaluate_stop(
            criterion=self.loop.stop_when,
            fact=fact,
            round_index=fact.round_index,
            max_rounds=self.loop.max_rounds,
        )
        if decision.stop:
            self.stopped_by = decision.kind
            self.stop_criterion = decision.criterion
        return decision

    def stop_payload(self) -> dict[str, Any]:
        """停止事实的读面载荷（**只在真的停过之后**取；点名判据与读数）。"""
        assert self.stopped_by, "stop_payload() before the loop actually stopped"
        last = self.facts[-1]
        return {
            "phases": list(self.loop.phases),
            "rounds_run": self.rounds_run,
            "stopped_by": self.stopped_by,
            "criterion": self.stop_criterion,
            "max_rounds": self.loop.max_rounds,
            # 结论类停止时，读数是「本轮新标识为空」这件事本身（进事件链可复读）
            "new_ids_this_round": list(last.new_ids),
            "ids_seen": list(self.seen_ids),
        }


def validate_loops(loops: tuple[RoundLoop, ...], phase_ids: Sequence[str]) -> None:
    """装配期校验：循环声明的 phase 必须都在编译计划里（点名，不静默跳过）。"""
    known = set(phase_ids)
    for loop in loops:
        missing = [phase for phase in loop.phases if phase not in known]
        if missing:
            raise ValueError(f"round loop references unknown phases: {missing}")
        expanded = [loop.round_phase_id(phase, 2) for phase in loop.phases]
        if len(set(expanded)) != len(expanded):  # pragma: no cover - 由 unique 保证
            raise ValueError(f"round loop {loop.phases!r} expands to duplicate ids")


def loop_for_phase(loops: tuple[RoundLoop, ...], phase_id: str) -> tuple[RoundLoop, int] | None:
    """（转发 `find_loop`；执行面与声明面共用同一反查口径，不各写一份。）"""
    return find_loop(loops, phase_id)


def conclusion_stop_kind() -> str:
    """结论类停止的类别名（判据里逐字比对用；避免在测试里硬编码字符串）。"""
    return STOP_BY_CONCLUSION


__all__ = [
    "RoundLoopState",
    "conclusion_stop_kind",
    "loop_for_phase",
    "validate_loops",
]

#: 类型别名（`execute_phases` 的循环控制回调签名；只为可读性）。
RunRound = Callable[[int], "RunOutcome | None"]
