"""同批评审「先评完再判」的执行面（GOAL-20261018-087 EC-01/EC-02/EC-03）。

**它补哪一格**：`phase_runner._run_group_task` 在 `step.failure` 非空时**立即**返回失败
`RunOutcome` ⇒ 同一 phase 的**后续任务不再执行**。对研究循环里的一批评审者，这意味着
**第一位判负的评审者就把整个 run 打死**，第二位连跑都不跑 ⇒ 阶梯说的「两个模型在同一个
上游产物上给出**不同判词**」在**结构上不可达**（实测：两位评审者都判负 ⇒
`state: FAILED, records: 1, panels: []`）。

**本模块只做三件事**：判定这一组要不要「先评完再判」、把组内失败**记下来**让同组继续、
组末把**全体**票型汇成一条点名每位评审者的失败。

**三条边界**（逐条可判）：

1. **不吞判负**：全体评完后仍有任一位判负 ⇒ run **仍然 `FAILED`**（终态与既有语义一致）。
   被改的只有**时机**与**可见性**。
2. **有条件的**：只有该组**全部**任务都声明了 `review_panel: COMPLETE_THEN_JUDGE` 才生效；
   缺一 ⇒ 逐字回到既有 fail-fast（那条声明是承诺，不是半数生效）。
3. **不复用 `on_task_failure: CONTINUE`**：那是「容忍失败、run 收敛 `DEGRADED`」的既有
   语义（判负成了可带走的瑕疵），与本模块的「先评完、再判负」是两件事。
"""

from __future__ import annotations

from typing import Any

from packages.application.run_orchestration.outcomes import TaskOutcome

#: 声明键的取值（与 `packages/domain/failure_policy.ReviewPanelFailure` 同一个名字）。
COMPLETE_THEN_JUDGE = "COMPLETE_THEN_JUDGE"


def panel_plan(group: tuple[Any, ...]) -> bool:
    """这一组任务是否**全部**声明了「先评完再判」（缺一即不生效）。

    「半数生效」会让同一组里两位评审者**一个评完、一个被短路** —— 那正是本 GOAL 要消灭的
    形态（看起来有面板、其实只有一票）。
    """
    if not group:
        return False
    return all(_declares(contract) for _task, contract, _spec in group)


def _declares(contract: Any) -> bool:
    view = getattr(contract, "failure_policy_view", None)
    if view is None:
        return False
    return bool(view().panel_completes_before_judging)


def reviewer_target(spec_context: Any) -> str:
    """一位评审者的**解析后目标**（`endpoint/model_name`；与 GOAL-084/085/086 同源）。

    取不到任一半 ⇒ `"unknown"`（**不**拼半个目标、**不**回落到 agent 名）。
    """
    endpoint_id = getattr(getattr(spec_context, "endpoint", None), "id", None)
    model_name = getattr(getattr(spec_context, "model", None), "model_name", None)
    if not endpoint_id or not model_name:
        return "unknown"
    return f"{endpoint_id}/{model_name}"


def record_rejection(run: Any, task: Any, step: Any) -> None:
    """把这一位评审者的**判负**记账（`run.outcomes`），让同组继续跑。

    判负**没被吞掉**：它进 `outcomes`，组末由 `panel_rejection` 取出并变成 run 的失败。
    这里之所以不返回 `RunOutcome`：那会让同组剩下的评审者**不执行**，分歧就永远不会出现。

    `verdict` 取**门上的裁决**（`step.failure` 的来源已丢了载体 —— 失败 `RunOutcome` 只有
    消息）。传 `None` ⇒ 组末按 `"UNKNOWN"` 点名（**不**猜成 PASS/REJECT）。
    """
    run.outcomes.append(
        TaskOutcome(
            task=task,
            outcome="FAILED",
            verdict=_verdict_of(step),
            message=step.failure.message if step.failure is not None else "",
            failure_policy=COMPLETE_THEN_JUDGE,
        )
    )


def _verdict_of(step: Any) -> str | None:
    """这一位评审者的裁决（门上给的；取不到 ⇒ `None`，组末按 `UNKNOWN` 点名，不猜）。"""
    return getattr(step, "verdict", None)


def record_success(run: Any, task: Any, step: Any) -> None:
    """一个任务成功：handoff + outcome 记账。

    放在本模块（而不是执行器里）是为了守住 `phase_runner` 的 **450 行硬上限** ——
    它已经贴着上限，组级记账的三件事（判负 / 成功 / 组末判定）因此收在一处。
    """
    run.handoffs[task.id.value] = step.handoff
    run.outcomes.append(
        TaskOutcome(
            task=task,
            outcome="SUCCEEDED",
            verdict=step.verdict,
            skipped=step.skipped,
            chain_outputs=step.chain_outputs,
            annotations=step.annotations,
        )
    )


def panel_rejection(deps: Any, group: tuple[Any, ...], run: Any, run_id: str) -> Any | None:
    """组末判定：有**未被容忍的**判负 ⇒ 返回一条点名全体票型的失败；否则 `None`。

    判负的**后果没变**（run 仍 `FAILED`）：变的只是「等到全体评完才判」，以及失败消息里
    逐条点名「谁判了什么」—— 只报「一个目标判负」会让「一负一过」与「两负」看起来一样，
    而这两件事的处置完全不同。

    **只认本模块记账的那些**（`failure_policy is COMPLETE_THEN_JUDGE`）：`on_task_failure:
    CONTINUE` 的既有语义是**容忍**（run 收敛 `DEGRADED`），把它一并算成判负会让那条
    策略悄悄失效 —— 两个声明面必须互不越界。
    """
    verdicts = _verdicts(group, run)
    rejected = tuple(item for item in verdicts if item[1] != "PASS")
    if not rejected:
        return None
    return deps.fail(run_id, _message(rejected, verdicts), False)


def _verdicts(group: tuple[Any, ...], run: Any) -> list[tuple[str, str]]:
    """本组每位评审者的 `(目标, verdict)`（按声明顺序）。

    只收**本模块记账的判负**（`failure_policy is COMPLETE_THEN_JUDGE`）与**通过的**任务；
    `on_task_failure: CONTINUE` 记下的被容忍失败**不在此列**（那是另一个声明面）。
    """
    by_task = {outcome.task.id.value: outcome for outcome in run.outcomes}
    pairs: list[tuple[str, str]] = []
    for task, _contract, spec in group:
        outcome = by_task.get(task.id.value)
        if outcome is None:
            continue
        if outcome.outcome == "FAILED" and outcome.failure_policy != COMPLETE_THEN_JUDGE:
            continue
        pairs.append((reviewer_target(spec), str(outcome.verdict or "UNKNOWN")))
    return pairs


def _message(rejected: tuple[tuple[str, str], ...], verdicts: list[tuple[str, str]]) -> str:
    """失败消息（逐条点名 + 全体票型；两个面都必须读得出）。"""
    down = ", ".join(f"{target}={verdict}" for target, verdict in rejected)
    panel = ", ".join(f"{target}={verdict}" for target, verdict in verdicts)
    return (
        f"review panel rejected the artifact after every reviewer finished: "
        f"{len(rejected)} of {len(verdicts)} reviewer(s) rejected ({down}); "
        f"panel verdicts: {panel}"
    )


__all__ = [
    "COMPLETE_THEN_JUDGE",
    "panel_plan",
    "panel_rejection",
    "record_rejection",
    "record_success",
    "reviewer_target",
]
