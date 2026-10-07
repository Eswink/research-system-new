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
from dataclasses import dataclass, field, replace
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
from packages.domain.core import ID

if TYPE_CHECKING:
    from packages.application.run_orchestration.outcomes import RunOutcome

    # 只为类型：避免与 phase_runner 形成导入环
    pass


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
        """把一轮的产出读成事实（标识按 `loop.ids_path` 声明路径取；`new_ids` 用集合差）。"""
        before = self.seen_ids
        self.facts.append(
            RoundFact(
                round_index=round_index,
                ids=ids_from_step_outputs(outputs, self.loop.ids_path),
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
    """装配期校验（**三条点名拒绝**，都不静默）：

    1. 循环声明的 phase 必须在编译计划里；
    2. **两条循环不得共用 phase** —— 否则「这条 phase 属于哪个循环」有歧义，
       而 `find_loop` 只能返回第一条（静默取一条正是本仓禁止的形态）；
    3. 循环必须**覆盖全部** phase（v1 的适用范围）。循环控制包在既有单遍执行之外，
       若循环只覆盖一部分 phase，就得决定「循环外的 phase 与轮次的先后关系」——
       那是一条新语义，本轮**不做**；不满足即**点名拒绝**，而不是悄悄选一种排法。
    """
    known = set(phase_ids)
    seen: dict[str, int] = {}
    for index, loop in enumerate(loops):
        missing = [phase for phase in loop.phases if phase not in known]
        if missing:
            raise ValueError(f"round loop references unknown phases: {missing}")
        for phase in loop.phases:
            if phase in seen:
                raise ValueError(
                    f"phase {phase!r} appears in two round loops "
                    f"(#{seen[phase]} and #{index}); the owning loop would be ambiguous"
                )
            seen[phase] = index
        if not loop.owns_every_phase(tuple(phase_ids)):
            outside = sorted(set(phase_ids) - set(loop.phases))
            raise ValueError(
                "a round loop must cover every phase in this version; phases outside it: "
                f"{outside} (ordering between looped and non-looped phases is not defined)"
            )


def loop_for_phase(loops: tuple[RoundLoop, ...], phase_id: str) -> RoundLoop | None:
    """（转发 `find_loop`；执行面与声明面共用同一反查口径，不各写一份。）"""
    return find_loop(loops, phase_id)


def conclusion_stop_kind() -> str:
    """结论类停止的类别名（判据里逐字比对用；避免在测试里硬编码字符串）。"""
    return STOP_BY_CONCLUSION


__all__ = [
    "RoundLoopState",
    "conclusion_stop_kind",
    "execute_rounds",
    "loop_for_phase",
    "round_loop_fields",
    "round_specs",
    "validate_loops",
]


def execute_rounds(deps: Any, ctx: Any) -> "RunOutcome":
    """按轮重复执行**既有单遍执行**，直到停止判据或上界护栏说停（EC-01 的执行面）。

    **懒展开**：每轮**开始时**才经 `deps.resolve_round(index)` 解析该轮 specs ——
    解析期就把 N 轮全展开会让停止判据变成装饰（任务都已提交，轮次照跑）。

    **失败就退出循环**（不是继续下一轮）：非 `SUCCEEDED` 的结局（FAILED / PAUSED /
    WAITING_FOR_APPROVAL）由既有语义接管，循环不越过它。

    **停止事实骑既有事件**：走 `run.completed`（词表零扩张，承 GOAL-031 EC-03 的
    `skipped` 手法），`rounds` 键只在真的跑过循环时出现 ⇒ 单遍载荷逐字节不变。
    """
    from dataclasses import replace as _replace

    from packages.application.run_orchestration.phase_runner import _execute_one_pass
    from packages.domain.events import EventType
    from packages.domain.run_state import ResearchRunState

    driver = deps.round_driver
    while True:
        round_index = driver.next_round()
        outcome = _execute_one_pass(deps, ctx, deps.resolve_round(round_index))
        if outcome.state != ResearchRunState.State.SUCCEEDED:
            return outcome
        decision = driver.record(
            RoundPass(
                round_index=round_index,
                outputs=outcome.chain_outputs,
                task_ids=tuple(t.task.id.value for t in outcome.tasks),
            )
        )
        if not decision.stop:
            continue
        payload = driver.state.stop_payload()
        # **把单遍载荷原样带上**（含声明式跳过的 `skipped`）再追加 `rounds` ——
        # 否则跑循环的 run 会**丢掉**跳过事实（那正是 EC-03 禁止的「静默」形态）；
        # 单遍路径不受影响（它自己那条 `run.completed` 逐字节不变）。
        carried: dict[str, object] = {"run_id": ctx.run_id}
        if outcome.rounds is None:
            carried = _single_pass_payload(deps, ctx, outcome)
        carried["rounds"] = payload
        deps.emit(EventType.RUN_COMPLETED, carried, ctx.run_id, ctx.trace_id, None)
        return _replace(outcome, rounds=payload)


def _single_pass_payload(deps: Any, ctx: Any, outcome: Any) -> dict[str, object]:
    """单遍执行那条 `run.completed` 的载荷（**逐字重建**，与既有构造同形）。

    为什么要重建而不是从事件里读：那条事件是本轮循环**上一轮**发出的，而本函数在
    循环收尾时执行 —— 从事件流回读会依赖「上一轮确实发过」这一时序（实测脆弱）。
    重建的口径与 `_execute_one_pass` 里那把构造**同一份**字段清单（`run_id` + 有跳过
    才带的 `skipped`）。
    """
    payload: dict[str, object] = {"run_id": ctx.run_id}
    skips = [
        {"task_id": task_outcome.task.id.value, "reasons": list(task_outcome.skipped)}
        for task_outcome in outcome.tasks
        if task_outcome.skipped
    ]
    if skips:
        payload["skipped"] = skips
    return payload


def round_loop_fields(
    loops: Any,
    specs: Sequence[Any],
) -> dict[str, Any]:
    """`PhaseRunnerDeps` 的**多轮循环两个字段**（未声明循环 ⇒ 空 dict ⇒ 单遍不变）。

    单独成函数的理由：`service.py` 恰在 450 行硬上限，这两个字段的构造（含闭包）
    放进去就越界；放这里既守住规模门，也让「循环怎么驱动」只有一处解释点。
    """
    declared = tuple(loops or ())
    if not declared:
        return {}
    loop = declared[0]
    driver = RoundDriver.start(loop)
    return {
        "round_driver": driver,
        # 闭包读 `driver` 的当前值 ⇒ 每轮拿到的都是**上一轮**记下的前缀（懒展开）。
        "resolve_round": lambda index: round_specs(
            loop, index, specs, previous_prefixes=driver.previous_prefixes
        ),
    }


def round_specs(
    loop: RoundLoop,
    round_index: int,
    specs: Sequence[Any],
    *,
    previous_prefixes: tuple[str, ...] = (),
) -> tuple[Any, ...]:
    """第 `round_index` 轮的 specs（**懒展开**的展开点）。

    phase id **不变**（运行链的 phase 级过滤拿它查表，带后缀就查不到）。

    两处按轮替换（**实测各对应一个真缺口**）：

    1. **任务 id 与幂等键**：每轮必须是**不同的任务**。幂等键同 ⇒ 第二轮的 submit 被既有
       按 key 去重**静默吞掉**（安静地不跑，不报错）；任务 **id** 同 ⇒ 同一条任务上重复
       跑运行链会以**不同 digest** 重登记同一 `source_ref`（origin 含 task id 与操作键）
       ⇒ 撞 `conflicting source registration`（实测：第一轮成功、第二轮 FAILED）。
       两条都是「静默或半静默地做错事」，所以两处都必须按轮区分。
    2. **本轮的运行链声明**（`loop.calls_for`）—— 轮次差异的声明面。

    第 1 轮**逐字保留**任务 id 与幂等键（既有单轮语义与「续跑按 key 对齐」逐字不动）。
    """
    calls = loop.calls_for(round_index)
    out: list[Any] = []
    for task, contract, spec_context in specs:
        keyed = replace(
            task,
            idempotency_key=loop.round_key(task.idempotency_key or "", round_index),
        )
        if round_index > 1:
            keyed = replace(keyed, id=ID.generate())
        if calls is not None:
            # 该轮的运行链声明（每轮差异的**声明面**）：只换这一项，其余逐字不动。
            spec_context = replace(spec_context, round_calls=calls)
        if previous_prefixes:
            spec_context = replace(spec_context, previous_round_task_prefixes=previous_prefixes)
        out.append((keyed, contract, spec_context))
    return tuple(out)


#: 轮次解析回调：给定轮次，产出该轮的 specs（**懒展开**：判「停」后就不再解析下一轮）。
RoundResolver = Callable[[int], "tuple[Any, ...]"]


@dataclass(frozen=True, slots=True)
class RoundPass:
    """一轮的结论：该轮**全部任务**的运行链产出（停止判据的输入）与它们的任务 id。

    `task_ids` 是**下一轮**收窄「上一轮产出」的依据（制品 id 形如
    `tool-result:{task_id}:{op}:{tool}` ⇒ 前缀 `tool-result:{task_id}:`）。
    """

    round_index: int
    outputs: tuple[Any, ...]
    task_ids: tuple[str, ...] = ()


@dataclass(slots=True)
class RoundDriver:
    """把 `RoundLoop` 声明变成**真的重复执行**（GOAL-20261008-034 EC-01 的执行面）。

    **懒展开**（关键设计）：调用方每轮**开始时**才经 `resolve` 解析该轮 specs ——
    解析期就把 N 轮全展开会让停止判据变成装饰（任务都已提交，轮次照跑）。

    **不复制执行逻辑**：本类只决定「还有没有下一轮」，每轮怎么跑由调用方给的
    `run_round` 完成（生产路径里它就是既有的 `execute_phases` 单遍执行）。
    """

    loop: RoundLoop
    state: RoundLoopState
    rounds: list[int] = field(default_factory=list)
    #: 上一轮各任务的制品前缀（`tool-result:{task_id}:`）—— 下一轮的
    #: `artifact_from_previous_round` 用它收窄到**上一轮**的产出（执行期才知道）。
    previous_prefixes: tuple[str, ...] = ()

    @classmethod
    def start(cls, loop: RoundLoop) -> "RoundDriver":
        return cls(loop=loop, state=RoundLoopState(loop=loop))

    @property
    def stopped(self) -> bool:
        return bool(self.state.stopped_by)

    def record(self, pass_: RoundPass) -> Any:
        """记一轮的产出并判定（返回 `StopDecision`；调用方据此决定要不要再来一轮）。"""
        self.state.record_round(pass_.round_index, _mappings(pass_.outputs))
        self.rounds.append(pass_.round_index)
        self.previous_prefixes = tuple(f"tool-result:{task_id}:" for task_id in pass_.task_ids)
        return self.state.decide()

    def next_round(self) -> int:
        """下一轮的序号（**未停**时才有意义；停了再问是调用方的错 ⇒ 断言）。"""
        assert not self.stopped, "next_round() after the loop stopped"
        return len(self.rounds) + 1


def _mappings(outputs: tuple[Any, ...]) -> tuple[Mapping[str, Any], ...]:
    """过滤出 mapping 形态的产出（非 mapping 的产出不是判据能读的事实）。"""
    return tuple(item for item in outputs if isinstance(item, Mapping))


__all__ = [
    "RoundDriver",
    "RoundLoopState",
    "RoundPass",
    "RoundResolver",
    "conclusion_stop_kind",
    "loop_for_phase",
    "validate_loops",
]
