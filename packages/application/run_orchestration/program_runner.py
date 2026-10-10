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
from dataclasses import dataclass, replace
from datetime import timedelta
from typing import Any

from packages.application.ports.program_store import ProgramStore
from packages.application.ports.run_store import RunStore
from packages.application.run_orchestration.program_retry import retry_face_state
from packages.application.run_orchestration.program_waiting import (
    ApprovalReader,
    declared_gate_verdict,
    waiting_round_decision,
)
from packages.domain.core import Timestamp
from packages.domain.program import ProgramDecision, ProgramDecisionKind, ResearchProgram
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState

#: 启动面：给序号、返回新 run 的 id（组合根注入；应用层不 import 服务层）。
StartRun = Callable[[int], str]
#: 评审结论读取面（只用到 `for_run`）。
FindingReader = Any


@dataclass(frozen=True, slots=True)
class ProgramAdvance:
    """一次推进的结果（决策 + 是否起了新 run + 程序内 run 数）。"""

    program_id: str
    decision: ProgramDecision
    started_run_id: str | None
    run_count: int


def _verdicts(findings: FindingReader | None, run_id: str) -> tuple[str, ...]:
    """上一轮落库的评审判词（逐字、**去重保序**）。

    「这一轮的结论是什么」是**取值集合**：同一 run 的多个 phase 可能都落库判词
    （实测：`produce` 与 `consume` 各一条），重复值不携带新信息 ⇒ 去重后进决策，
    避免 `cited_facts` 出现同一条原文两遍。
    """
    if findings is None:
        return ()
    seen: dict[str, None] = {}
    for item in findings.for_run(run_id):
        seen.setdefault(str(item.finding.verdict), None)
    return tuple(seen)


def _record(programs: ProgramStore, program_id: str, decision: ProgramDecision) -> ProgramDecision:
    """落一条决策；`decided_at` 归一为**该程序内严格递增**的时点。

    **为什么必须归一**（GOAL-20261009-041 EC-02 实测）：存储的决策自然键是
    `(program_id, after_index, decided_at)`，而 `Timestamp.now()` 在**同一时钟刻度**
    内会给出**相同**的微秒值 ⇒ 同一序号上的多条决策**互相顶掉**（`INSERT OR IGNORE` /
    `ON CONFLICT DO NOTHING` 是**静默**的）。实测：紧循环连录 10 条 ⇒ 只留存 **1** 条。
    计数面依赖「每次推进都留下一条决策」⇒ 被静默丢弃时**声明的上界不成立**。

    归一的口径（**逻辑时钟**）：取该程序已落决策的**最大时点**；`now` 不大于它时
    只推进 1 微秒（其余情形原样用挂钟）⇒ 既保住「决策各自带时间」的语义，
    又让自然键**不再碰撞**。
    """
    latest = max(
        (item.decided_at.value for item in programs.decisions_of(program_id)),
        default=None,
    )
    now = decision.decided_at.value
    if latest is not None and now <= latest:
        now = latest + timedelta(microseconds=1)
    stamped = replace(decision, decided_at=Timestamp(now))
    programs.record_decision(stamped)
    return stamped


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
    approvals: ApprovalReader | None,
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
        kind, reason, facts = waiting_round_decision(last, last_index, approvals)
        return _Evaluation(kind=kind, reason=reason, cited_run_id=last.id.value, cited_facts=facts)

    # GOAL-20261010-046 EC-03：**声明的人工闸门**在结论面之前（判定面在 program_waiting）。
    gate = declared_gate_verdict(program, last, approvals)
    if gate is not None:
        return _gate_evaluation(last, gate)

    # GOAL-20261008-040 EC-03：**按终态分派** —— 失败面 / 取消面在结论面**之前**
    # （只有 `SUCCEEDED` 的轮才有「结论」可言；把「没有结论」读成「结论说停」是范畴错误）。
    if str(last.state) != ResearchRunState.State.SUCCEEDED:
        return _non_success_terminal(program, existing, last, programs)

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


def _gate_evaluation(last: ResearchRun, gate: tuple[str, str, tuple[str, ...]]) -> _Evaluation:
    """把 `declared_gate_verdict` 的判定值包成 `_Evaluation`（闸门拦住本次推进）。"""
    gate_kind, gate_reason, gate_facts = gate
    return _Evaluation(
        kind=ProgramDecisionKind(gate_kind),
        reason=gate_reason,
        cited_run_id=last.id.value,
        cited_facts=gate_facts,
    )


def _non_success_terminal(
    program: ResearchProgram,
    existing: tuple[ResearchRun, ...],
    last: ResearchRun,
    programs: ProgramStore,
) -> _Evaluation:
    """`FAILED` / `CANCELLED` 两个终态的判定（失败面 / 取消面；**不**与结论面混用）。

    - `CANCELLED` ⇒ `STOP_CANCELLED`（人的决定，**不**自动重试）；
    - `FAILED` ⇒ 见 `_failed_round`（重试未用尽 ⇒ 重试同序号；否则失败停并点名）。
    """
    last_index = last.program_index or 0
    state = str(last.state)
    if state == ResearchRunState.State.CANCELLED:
        return _Evaluation(
            kind=ProgramDecisionKind.STOP_CANCELLED,
            reason=(
                f"第 {last_index} 轮被取消（state=CANCELLED）⇒ 按取消停"
                "（取消是人的决定，**不**自动重试）"
            ),
            cited_run_id=last.id.value,
            cited_facts=(f"state={state}",),
        )
    return _failed_round(program, existing, last, last_index, programs)


def _retry_facts(
    programs: ProgramStore,
    program_id: str,
    existing: tuple[ResearchRun, ...],
    last_index: int,
) -> tuple[int, str | None]:
    """失败重试面的 `(已用尝试数, 未落库的认领)` —— 落库行数取自 canonical `existing`。"""
    landed_ids = {run.id.value for run in existing if (run.program_index or 0) == last_index}
    return retry_face_state(programs, program_id, last_index, landed_ids)


def _failed_round(
    program: ResearchProgram,
    existing: tuple[ResearchRun, ...],
    last: ResearchRun,
    last_index: int,
    programs: ProgramStore,
) -> _Evaluation:
    """失败轮的判定（**三形态互不混用**；GOAL-20261009-041 EC-02/EC-03）。

    ① **用尽**（`attempts >= allowed`）⇒ `STOP_RUN_FAILED` + 点名上界与已用数；
    ② **已认领但未落库**（上一条重试认领了本序号而该 run 没落库）⇒ `DEDUP_FAILED_RUN`：
       **不**再起第二个同序号 run，点名认领的 run；
    ③ 否则 ⇒ `RETRY_FAILED_RUN`（重试**同序号**）。

    **为什么「用尽」排在「去重」之前**：两条都在失败面，但**处置相反** ——
    上界是**硬**约束（必须收口）；去重是**幂等**约束（同一认领不重复起 run）。
    若把去重排在前面，被阻塞的推进**永远**落去重、**永不**收口 ⇒ 正是本轮要消灭的
    「隐式无限重跑」。已用尝试数把「未落库的认领」与「被阻塞的推进」都计入
    （`program_retry.retry_face_state`）⇒ 步数有界且必然收口。
    """
    state = str(last.state)
    allowed = program.max_attempts_per_index
    attempts, outstanding = _retry_facts(programs, program.id, existing, last_index)
    cited = (f"state={state}", f"attempts={attempts}/{allowed}")
    if attempts >= allowed:
        return _bounded_stop(last, last_index, attempts, allowed, cited)
    if outstanding is not None:
        return _returning_claim_stop(last_index, outstanding, attempts, allowed, cited)
    return _Evaluation(
        kind=ProgramDecisionKind.RETRY_FAILED_RUN,
        reason=(
            f"第 {last_index} 轮执行失败（state=FAILED）但声明允许重试"
            f"（已用 {attempts}/{allowed}）⇒ 重试**同序号**"
        ),
        cited_run_id=last.id.value,
        cited_facts=cited,
        start_index=last_index,
    )


def _bounded_stop(
    last: ResearchRun,
    last_index: int,
    attempts: int,
    allowed: int,
    cited: tuple[str, ...],
) -> _Evaluation:
    """用尽 ⇒ 失败停（点名「未获结论」与上界；与「结论说停」严格区分）。"""
    tail = (
        f"，且重试已用尽（{attempts}/{allowed}）⇒ 按失败停"
        if allowed > 1
        else f"；未声明重试（max_attempts_per_index={allowed}）⇒ 按失败停"
    )
    return _Evaluation(
        kind=ProgramDecisionKind.STOP_RUN_FAILED,
        reason=(
            f"第 {last_index} 轮执行失败（state=FAILED）⇒ **未获结论**（不是「结论说停」）{tail}"
        ),
        cited_run_id=last.id.value,
        cited_facts=cited,
    )


def _returning_claim_stop(
    last_index: int,
    outstanding: str,
    attempts: int,
    allowed: int,
    cited: tuple[str, ...],
) -> _Evaluation:
    """崩溃窗口（认领了本序号却未落库）⇒ 去重：**不**再起第二个同序号 run。"""
    return _Evaluation(
        kind=ProgramDecisionKind.DEDUP_FAILED_RUN,
        reason=(
            f"上一条重试已认领第 {last_index} 轮（run={outstanding}）但该 run **未落库**"
            f" ⇒ 不再起第二个同序号 run（已用 {attempts}/{allowed}，点名人工）"
        ),
        cited_run_id=outstanding,
        cited_facts=(*cited, f"claimed run {outstanding}"),
    )


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


def advance_program(  # noqa: PLR0913 - 推进面的读入就这几件（run/决策/结论/审批/启动）
    program: ResearchProgram,
    *,
    runs: RunStore,
    programs: ProgramStore,
    findings: FindingReader | None = None,
    approvals: ApprovalReader | None = None,
    start_run: StartRun | None = None,
) -> ProgramAdvance:
    """推进一次：读事实 → 判定 → 落决策 →（必要时）起下一轮 run。"""
    existing = runs.for_program(program.id)
    evaluation = _evaluate(program, existing, findings, programs, approvals)
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
        program.id,
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
            program.id,
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
        program.id,
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
