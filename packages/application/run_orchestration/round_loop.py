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
    「检索 → 分析」这样的一小段）。展开后第 N 轮的 phase id 形如 `{phase}@{N}`
    —— 任务 idempotency key 由 `{run}:{phase}:{agent}` 派生 ⇒ **每轮是不同的任务**
    （否则第二轮的 submit 会被既有按 key 去重直接吞掉，那是静默停）。
    """

    phases: tuple[str, ...]
    max_rounds: int
    stop_when: str = CONVERGED_NO_NEW_IDS

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

    def round_phase_id(self, phase_id: str, round_index: int) -> str:
        """第 `round_index` 轮（从 1 起）里 `phase_id` 的**展开 id**。

        后缀形态 `@{n}` 与既有 phase id 命名空间不相交（`schemas` 不允许 `@`），
        因此展开不会与协议里真实声明的 phase 撞名。
        """
        if round_index < 1:
            raise ValueError("round index starts at 1")
        return f"{phase_id}@{round_index}"

    def expanded_phases(self) -> tuple[str, ...]:
        """全部轮次的展开序列（第 1 轮的**原始 id** 保持不变 —— 既有单轮语义逐字不动）。"""
        out: list[str] = []
        for index in range(1, self.max_rounds + 1):
            out.extend(
                phase if index == 1 else self.round_phase_id(phase, index) for phase in self.phases
            )
        return tuple(out)


def find_loop(loops: tuple[RoundLoop, ...], phase_id: str) -> tuple[RoundLoop, int] | None:
    """该 phase id 属于哪个循环的第几轮（`phase_id` 可能是展开 id）。

    返回 `(loop, round_index)`；不属于任何循环 ⇒ `None`。第 1 轮用原始 id，
    第 N>1 轮用 `{phase}@{N}` ⇒ 反查必须**先剥后缀再比对**（否则第二轮会认不出来）。
    """
    base, _, suffix = phase_id.partition("@")
    index = int(suffix) if suffix.isdigit() else 1
    for loop in loops:
        if base in loop.phases:
            return loop, index
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
