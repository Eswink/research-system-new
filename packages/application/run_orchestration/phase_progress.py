"""相级进度的**事件发射面**（GOAL-20261101-103 EC-01）。

**它补哪一格**：在加这两个事件之前，一次 run「走到第几相」只能从 `task.created` 的
序列**推断**，而产品读面（`RunDetailDto`）与前端都只能说「这条 run 是 RUNNING」。
GOAL-099/100/102 三轮把十一相科研链做齐之后，这条缺口变得刺眼：**链已在，进度不可见**。

**与 `phase_runner` 的关系（为什么单列）**：`phase_runner.py` 卡在 **450 行硬上限**
（`tests/tooling/test_python_source_limits.py`，实测 450/450、零余量）。本模块只做两件
纯事 —— 构造载荷、按既有 `publish` 回调发事件 —— 调用点因此各只占一行。

**两向语义（判据在 `tests/application/run_orchestration/test_phase_progress_events.py`）**：

1. `phase.started` 在该相**第一个任务开始前**发（⇒ 事件序上先于该组首个 `task.created`）；
2. `phase.completed` 在**该组全部任务终态后**发；
3. 组内**失败 / 停车 / 重排**⇒ **不发** `completed`。这条是本模块最重要的边界：
   若「相结束了」与「相成功了」用同一条事件表达，读面就无法区分「走完」与「走坏」，
   而 `RunOutcome` 已经由别的路径如实收敛 —— 这里只描述**相**这件事。

**payload 只有身份、没有内容**（AGENTS.md §10）：`phase_id` / `strategy` /
`contract_ids` / `outcome` / `artifact_ids`。制品**标识**不是制品内容，与既有
`task.created` 的 `task_id` 同层；不取任何模型输入输出、不留 Prompt 片段。

**`phase_id` 为空的组不发事件**：resume 重建路径（M15）不携带相身份，此时发一条
`phase_id=""` 的事件会让读面多出一个不存在的相 —— 与既有「phase_id 为空则不发 PHASE
correlation」同一条纪律。
"""

from __future__ import annotations

from typing import Any

from packages.domain.events import EventType

#: `phase.completed` 的 outcome 词表（**闭集**）。两值穷举「组跑完了」的两种真实形态：
#: 全部成功，或有任务被契约容忍（`on_task_failure: CONTINUE`）。组内**终局失败**根本
#: 不会走到本函数的 completed 分支（执行循环已返回失败）⇒ 这里没有 `FAILED`。
PHASE_OUTCOME_SUCCEEDED = "SUCCEEDED"
PHASE_OUTCOME_DEGRADED = "DEGRADED"

PHASE_OUTCOMES: frozenset[str] = frozenset({PHASE_OUTCOME_SUCCEEDED, PHASE_OUTCOME_DEGRADED})


def _phase_identity(group: tuple[Any, ...]) -> tuple[str, str]:
    """本组的 `(phase_id, strategy)`（取自组内第一份 spec 的上下文）。"""
    context = group[0][2]
    return context.phase_id, getattr(context, "phase_strategy", "") or ""


def phase_started_payload(group: tuple[Any, ...]) -> dict[str, object]:
    """`phase.started` 载荷：相身份 + 本组的契约集合（确定性顺序）。"""
    phase_id, strategy = _phase_identity(group)
    return {
        "phase_id": phase_id,
        "strategy": strategy,
        "contract_ids": [contract.id for _task, contract, _context in group],
    }


def group_artifact_ids(run: Any, group: tuple[Any, ...]) -> list[str]:
    """本组各任务**真实产出**的制品 id（确定性排序、去重）。

    来源是 `HandoffBundle.artifact_refs` —— 由结果注册处（`registration.artifact_refs()`）
    填的 canonical 事实。**不**从 `chain_outputs` 猜：那是运行链的返回内容，不是制品。
    取不到 handoff 的任务（失败 / 未产出）**跳过**，不补占位。
    """
    task_ids = [task.id.value for task, _contract, _context in group]
    found: set[str] = set()
    handoffs = getattr(run, "handoffs", {})
    for task_id in task_ids:
        bundle = handoffs.get(task_id) if hasattr(handoffs, "get") else None
        found.update(str(item) for item in getattr(bundle, "artifact_refs", ()) or ())
    return sorted(found)


def phase_outcome(outcomes: list[Any], group: tuple[Any, ...]) -> str:
    """本组的收敛结论（`PHASE_OUTCOMES` 闭集内的一值）。

    被契约容忍的失败（`failure_policy is not None`）⇒ `DEGRADED`：工作做完了，但本组
    有任务失败且契约声明容忍 —— 与 `RunOutcome` 的 DEGRADED 口径同源，不另造一套。
    """
    task_ids = {task.id.value for task, _contract, _context in group}
    tolerated = any(
        outcome.failure_policy is not None
        for outcome in outcomes
        if outcome.task.id.value in task_ids
    )
    return PHASE_OUTCOME_DEGRADED if tolerated else PHASE_OUTCOME_SUCCEEDED


def phase_completed_payload(
    group: tuple[Any, ...], run: Any, outcomes: list[Any]
) -> dict[str, object]:
    """`phase.completed` 载荷：相身份 + 收敛结论 + 本组真实制品 id。"""
    phase_id, _strategy = _phase_identity(group)
    return {
        "phase_id": phase_id,
        "outcome": phase_outcome(outcomes, group),
        "artifact_ids": group_artifact_ids(run, group),
    }


def emit_phase_started(deps: Any, ctx: Any, group: tuple[Any, ...]) -> None:
    """发 `phase.started`（`phase_id` 为空 ⇒ **不发**，见模块 docstring）。"""
    phase_id, _strategy = _phase_identity(group)
    if not phase_id:
        return
    deps.emit(
        EventType.PHASE_STARTED,
        phase_started_payload(group),
        ctx.run_id,
        ctx.trace_id,
        None,
    )


def emit_phase_completed(deps: Any, ctx: Any, group: tuple[Any, ...], run: Any) -> None:
    """发 `phase.completed`（**只在组真的跑完时调用**；`phase_id` 为空 ⇒ 不发）。"""
    phase_id, _strategy = _phase_identity(group)
    if not phase_id:
        return
    deps.emit(
        EventType.PHASE_COMPLETED,
        phase_completed_payload(group, run, run.outcomes),
        ctx.run_id,
        ctx.trace_id,
        None,
    )


__all__ = [
    "PHASE_OUTCOMES",
    "PHASE_OUTCOME_DEGRADED",
    "PHASE_OUTCOME_SUCCEEDED",
    "emit_phase_completed",
    "emit_phase_started",
    "group_artifact_ids",
    "phase_completed_payload",
    "phase_outcome",
    "phase_started_payload",
]
