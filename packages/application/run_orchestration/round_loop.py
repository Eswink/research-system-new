"""多轮研究循环的**声明面**（GOAL-20261008-034 EC-01/EC-02）。

**它补的是什么**：建档实测（该 GOAL 的「事实层结论」）—— ① `PhaseStrategy.ITERATIVE_OPTIMIZER`
/ `POPULATION_SEARCH` 是**枚举孤儿**（三个执行面零消费）；② `StopConditions`
（`max_iterations` / `budget_exhausted`）解析、编译、preflight 三段落都有，
**运行期零消费** ⇒ `max_iterations: 4` 是装饰性声明；③ 相位执行链是**单遍**拓扑序
（`execute_phases` 每组只跑一遍）⇒ 今天的「多轮」只能靠在协议里**写死多个 phase**
（两轮协议就是这样）= MAINLINE 明文列出的「固定轮数的流水线加长」的反面形态。

**为什么声明放在装配面而不是协议面**（与 `RunChainCall` 同层，本仓既有手法）：
`RunChainCall` 就是装配方声明的（`OrchestrationDependencies.capabilities`），不经过
协议 schema —— 「哪条工具、按什么参数、从上一轮哪个字段取值」是**装配知识**，
不是研究者写的协议内容。多轮**循环控制**同理：它是执行装配的形状，改协议 schema
会连带 loader / compiler / preflight / 前端表单四处同步，而收益只是把同一件事
换个地方声明。⇒ 本模块是那一层。

**三条诚实边界**（写进声明面，不留给调用方猜）：

1. **轮数与轮次内容无关**：本声明只说「这一组 phase 重复跑，最多 N 轮」——
   每轮的差异只能来自**声明式派生链**（`RunChainCall` 的 `ids_from_previous` 等），
   本模块不做任何内容判断；
2. **`max_rounds` 是护栏不是停止规则**：它是「防失控」的上界；结论驱动的停止是
   `stop_when` 那条（EC-02 的核心：两者必须在读面上**可区分**）；
3. **不新造编排**：轮次由**展开**实现 —— 展开成一串既有 phase 组，交给既有
   `execute_phases` 逐组跑；循环控制只是「下一轮还要不要展开」这一个判定。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: 结论驱动停止的**声明式判据名**（词表；每次判定读一个**本轮结论的可观察事实**）。
#: 新增判据 = 新增一个词 + 一个读事实的纯函数（见 `round_loop_facts`），不得让调用方传 lambda。
CONVERGED_NO_NEW_IDS = "converged_no_new_ids"

STOP_CRITERIA: tuple[str, ...] = (CONVERGED_NO_NEW_IDS,)

#: 停止的两个**类别**（读面据此区分「谁让循环停的」；EC-02 (c) 要求它们可区分）。
STOP_BY_CONCLUSION = "CONCLUSION"
STOP_BY_GUARD = "MAX_ROUNDS"

STOP_KINDS: tuple[str, ...] = (STOP_BY_CONCLUSION, STOP_BY_GUARD)


@dataclass(frozen=True, slots=True)
class RoundLoop:
    """一组 phase 重复执行到「停」为止的装配声明。

    `phases` 是本轮要跑的 phase id 序列（按执行序；通常就是一个 phase，也可以是
    「检索 → 分析」这样的一小段）。

    **轮次只改任务幂等键，不改 phase id**（实测发现的关键约束）：任务幂等键由
    `{run}:{phase}:{agent}` 派生 ⇒ 每轮必须是**不同的任务**（否则第二轮的 submit 会被
    既有按 key 去重**静默吞掉**）。但 phase id **不能**带轮次后缀 —— 运行链的 phase 级
    过滤（`planned_in_this_phase`）拿 spec 的 phase id 去编译计划里查表，带后缀就查不到
    ⇒ 第 2 轮起**所有运行链调用都会被静默跳过**。⇒ 后缀加在幂等键上（见 `round_key`）。
    """

    phases: tuple[str, ...]
    max_rounds: int
    stop_when: str = CONVERGED_NO_NEW_IDS
    #: 结论事实的**声明路径**（本轮产出 JSON 里标识列表的键；默认 `ids`）。
    ids_path: str = "ids"
    #: **每轮的运行链声明**（下标 `round_index - 1`；`None` = 各轮同一批声明）。
    #: 为什么需要：轮次之间的**差异**必须由某个声明面承担 —— 若各轮声明完全相同，
    #: 第 2 轮通常立刻判「无新标识」而停（**判据在正确工作**，但测不到多轮）。
    #: 本字段把「这一轮用哪批调用」写成声明，而不是在代码里按轮「如果就」。
    calls_by_round: tuple[tuple[Any, ...], ...] = ()

    def calls_for(self, round_index: int) -> tuple[Any, ...] | None:
        """该轮的调用声明（未声明 ⇒ `None`，调用方沿用既有那一批）。"""
        if not self.calls_by_round:
            return None
        if round_index <= len(self.calls_by_round):
            return self.calls_by_round[round_index - 1]
        return self.calls_by_round[-1]

    def __post_init__(self) -> None:
        if not self.phases:
            raise ValueError("round loop requires at least one phase")
        if len(set(self.phases)) != len(self.phases):
            raise ValueError("round loop phases must be unique")
        if self.max_rounds < 2:
            raise ValueError(
                "round loop max_rounds must be >= 2 (a loop of one round is not a loop)"
            )
        if self.stop_when not in STOP_CRITERIA:
            raise ValueError(
                f"unknown stop criterion {self.stop_when!r}; known: {sorted(STOP_CRITERIA)}"
            )

    def round_key(self, base_key: str, round_index: int) -> str:
        """第 `round_index` 轮（从 1 起）里任务幂等键的名字。

        **第 1 轮保持基键逐字不变** ⇒ 既有单轮语义（以及「重排 / 续跑按幂等键对齐」）
        逐字不动；N>1 加 `@{n}` 后缀。后缀形态与既有键空间不相交（键里的 phase 段
        由协议声明，`schemas` 不允许 `@`）。
        """
        if round_index < 1:
            raise ValueError("round index starts at 1")
        return base_key if round_index == 1 else f"{base_key}@{round_index}"

    def owns_every_phase(self, phase_ids: tuple[str, ...]) -> bool:
        """本循环是否覆盖了给定的**全部** phase（v1 的适用范围；不是则点名拒绝）。

        为什么要求全覆盖：循环控制包在既有单遍执行之外（约束④「不把单遍改成嵌套循环」），
        若循环只覆盖一部分 phase，就得决定「循环外的 phase 与轮次的先后关系」——
        那是一条**新语义**，本轮不做（如实登记为未覆盖，而不是悄悄选一种）。**
        """
        return set(self.phases) == set(phase_ids)


def find_loop(loops: tuple[RoundLoop, ...], phase_id: str) -> RoundLoop | None:
    """该 phase id 属于哪个循环（phase id **不带**轮次后缀 ⇒ 每轮反查同一结果）。

    多条循环声明同一个 phase ⇒ 装配期即点名拒绝（见 `validate_loops`），
    因此这里的「第一条命中」不会掩盖歧义。
    """
    for loop in loops:
        if phase_id in loop.phases:
            return loop
    return None


__all__ = [
    "CONVERGED_NO_NEW_IDS",
    "STOP_BY_CONCLUSION",
    "STOP_BY_GUARD",
    "STOP_CRITERIA",
    "STOP_KINDS",
    "RoundLoop",
    "find_loop",
]
