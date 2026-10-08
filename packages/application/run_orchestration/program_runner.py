"""研究程序推进驱动（GOAL-20261008-037 EC-02）。

一次 `advance_program` = **读 canonical 事实 → 判定 → 落一条决策 → （必要时）起下一轮 run**。

判定的输入**全部是落库事实**（先结论后护栏，承 GOAL-034 的纪律）：

1. 程序内已有的 run（`RunStore.for_program`，按序号升序）—— 没有 ⇒ `START`；
2. 上一轮的**终态**（`ResearchRun.is_terminal`）—— 未终止 ⇒ `WAIT`（**不**重复起 run）；
3. 上一轮**落库的评审判词**（`ReviewFindingStore.for_run`）与声明式规则匹配 ⇒ `CONTINUE`，
   不匹配 ⇒ `STOP_RULE`（结论面判停）；
4. 结论面判「续」但下一序号超过 `max_runs` ⇒ `STOP_GUARDRAIL`（**可区分**于结论面）；
5. **幂等**：若上一条 `CONTINUE` 已认领序号 N+1（决策里记着 run id）而该 run **没落库**
   （崩溃窗口）⇒ `DEDUP`：**不产生第二个 run**，点名人工/重试（at-least-once + dedup 的口径）。

**启动面是注入的**：`start_run(index) -> run_id` 由组合根提供（应用层不 import `services/api`）。
缺省 `None` ⇒ 需要启动时**点名**「本装配未提供启动面」，绝不静默当作已启动。

**决策的 `cited_facts` 是原文**：判词逐字、状态逐字 —— 读面据此回答「为何继续 / 为何停」。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from packages.application.ports.program_store import ProgramStore
from packages.application.ports.run_store import RunStore
from packages.domain.program import ProgramDecision, ProgramDecisionKind, ResearchProgram
from packages.domain.run import ResearchRun

#: 启动面：给序号、返回新 run 的 id（组合根注入；应用层不 import 服务层）。
StartRun = Callable[[int], str]
#: 评审结论读取面（`ReviewFindingStore` 的形状；只用到 `for_run`）。
FindingReader = Any


@dataclass(frozen=True, slots=True)
class ProgramAdvance:
    """一次推进的结果（决策 + 是否起了新 run + 程序内 run 数）。"""

    program_id: str
    decision: ProgramDecision
    started_run_id: str | None
    run_count: int


def _verdicts(findings: FindingReader | None, run_id: str) -> tuple[str, ...]:
    """上一轮落库的评审判词（逐字）——读不到时给空元组（由调用方判来源可用性）。"""
    if findings is None:
        return ()
    return tuple(str(item.finding.verdict) for item in findings.for_run(run_id))


def _record(programs: ProgramStore, decision: ProgramDecision) -> ProgramDecision:
    programs.record_decision(decision)
    return decision


def _claimed_but_missing(
    programs: ProgramStore, program_id: str, after_index: int, known: set[str]
) -> str | None:
    """上一条 `CONTINUE` 认领的 run id（若它**没有**落库 ⇒ 返回它，供 DEDUP 点名）。"""
    for decision in reversed(programs.decisions_of(program_id)):
        if decision.after_index != after_index:
            continue
        if decision.kind is ProgramDecisionKind.CONTINUE and decision.cited_run_id:
            return None if str(decision.cited_run_id) in known else str(decision.cited_run_id)
        return None
    return None


def _evaluate(
    program: ResearchProgram,
    existing: tuple[ResearchRun, ...],
    findings: FindingReader | None,
    programs: ProgramStore,
) -> _Evaluation:
    """读落库事实并判定（**先结论后护栏**；返回的 `start_index` 非 None 才需要起 run）。"""
    if not existing:
        return _Evaluation(
            kind=ProgramDecisionKind.START,
            reason=f"程序内还没有 run ⇒ 起第 1 轮（max_runs={program.max_runs}）",
            start_index=1,
        )

    last = existing[-1]
    last_index = last.program_index or 0
    if not last.is_terminal:
        return _Evaluation(
            kind=ProgramDecisionKind.WAIT,
            reason=f"第 {last_index} 轮尚未终止（state={last.state}）⇒ 本轮不推进",
            cited_run_id=last.id.value,
            cited_facts=(f"state={last.state}",),
        )

    verdicts = _verdicts(findings, last.id.value)
    hit = [item for item in verdicts if item in program.continue_rule.verdict_in]
    if not hit:
        return _Evaluation(
            kind=ProgramDecisionKind.STOP_RULE,
            reason=(
                "上一轮落库结论不命中续跑规则 "
                f"(verdicts={list(verdicts)}, want={list(program.continue_rule.verdict_in)})"
                " ⇒ 按结论停"
            ),
            cited_run_id=last.id.value,
            cited_facts=tuple(f"verdict {item}" for item in verdicts),
        )

    return _after_hit(program, existing, last, hit, programs)


def _after_hit(
    program: ResearchProgram,
    existing: tuple[ResearchRun, ...],
    last: ResearchRun,
    hit: list[str],
    programs: ProgramStore,
) -> _Evaluation:
    """结论面已判「续」之后：先上界护栏、再去重窗口、最后才是 `CONTINUE`。"""
    last_index = last.program_index or 0
    cited = tuple(f"verdict {item}" for item in hit)
    if last_index >= program.max_runs:
        return _Evaluation(
            kind=ProgramDecisionKind.STOP_GUARDRAIL,
            reason=(
                f"结论面判「续」（verdict {hit[0]}）但已到上界 max_runs={program.max_runs}"
                " ⇒ 按上界护栏停"
            ),
            cited_run_id=last.id.value,
            cited_facts=cited,
        )

    claimed = _claimed_but_missing(
        programs, program.id, last_index, {run.id.value for run in existing}
    )
    if claimed is not None:
        return _Evaluation(
            kind=ProgramDecisionKind.DEDUP,
            reason=(
                f"上一条 CONTINUE 已认领序号 {last_index + 1}（run={claimed}）但该 run 未落库"
                " ⇒ 不产生第二个 run（点名人工/重试）"
            ),
            cited_run_id=claimed,
            cited_facts=(f"claimed run {claimed}",),
        )

    return _Evaluation(
        kind=ProgramDecisionKind.CONTINUE,
        reason=f"结论面判「续」（verdict {hit[0]}）⇒ 起第 {last_index + 1} 轮",
        cited_run_id=last.id.value,
        cited_facts=cited,
        start_index=last_index + 1,
    )


def advance_program(
    program: ResearchProgram,
    *,
    runs: RunStore,
    programs: ProgramStore,
    findings: FindingReader | None = None,
    start_run: StartRun | None = None,
) -> ProgramAdvance:
    """推进一次：读事实 → 判定 → 落决策 →（必要时）起下一轮 run。"""
    existing = runs.for_program(program.id)
    evaluation = _evaluate(program, existing, findings, programs)
    after_index = (existing[-1].program_index or 0) if existing else 0
    if evaluation.start_index is not None:
        return _start(
            program,
            programs,
            start_run,
            _StartIntent(
                index=evaluation.start_index,
                after_index=after_index,
                kind=evaluation.kind,
                reason=evaluation.reason,
                cited_facts=evaluation.cited_facts,
            ),
        )
    decision = _record(
        programs,
        ProgramDecision(
            program_id=program.id,
            after_index=after_index,
            kind=evaluation.kind,
            reason=evaluation.reason,
            cited_run_id=evaluation.cited_run_id,
            cited_facts=evaluation.cited_facts,
        ),
    )
    return ProgramAdvance(program.id, decision, None, len(existing))


@dataclass(frozen=True, slots=True)
class _Evaluation:
    """一次判定的结果（`start_index` 非 None ⇒ 需要起这一轮）。"""

    kind: ProgramDecisionKind
    reason: str
    cited_run_id: str | None = None
    cited_facts: tuple[str, ...] = ()
    start_index: int | None = None


@dataclass(frozen=True, slots=True)
class _StartIntent:
    """起一轮的意图（把参数收成一个值对象，避免超参数阈值的函数签名）。"""

    index: int
    after_index: int
    kind: ProgramDecisionKind
    reason: str
    cited_facts: tuple[str, ...] = ()


def _start(
    program: ResearchProgram,
    programs: ProgramStore,
    start_run: StartRun | None,
    intent: _StartIntent,
) -> ProgramAdvance:
    """起一轮（或点名「没有启动面」）并落决策。"""
    if start_run is None:
        decision = _record(
            programs,
            ProgramDecision(
                program_id=program.id,
                after_index=intent.after_index,
                kind=ProgramDecisionKind.WAIT,
                reason=f"本装配未提供启动面（点名）⇒ 第 {intent.index} 轮未起",
                cited_facts=intent.cited_facts,
            ),
        )
        return ProgramAdvance(program.id, decision, None, intent.after_index)
    started = str(start_run(intent.index))
    decision = _record(
        programs,
        ProgramDecision(
            program_id=program.id,
            after_index=intent.after_index,
            kind=intent.kind,
            reason=f"{intent.reason} ⇒ run={started}",
            cited_run_id=started,
            cited_facts=intent.cited_facts,
        ),
    )
    return ProgramAdvance(program.id, decision, started, intent.after_index + 1)
