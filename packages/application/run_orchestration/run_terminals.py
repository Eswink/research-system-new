"""run 终态事件的发布（GOAL-004 cycle 3 从 `service.py` 拆出：450 行硬上限）。

两条终态发布共享一个形状：发一个带"为什么"的 run 级事件，再返回对应的 `RunOutcome`。
差别只在语义——`RUN_FAILED`（任务终局失败且契约没有容忍）与 `RUN_DEGRADED`
（跑完了但有被容忍的失败）。预算预留的释放不在这里（`service` 持有 reservation refs）。

GOAL-004 cycle 7（EC-06）加入第三个发布：`compensate_failed_resume` —— 续跑**失败**不是
终态，它把 canonical 放回停车并记录原因，所以它返回改好状态的 run 而不是 `RunOutcome`。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from packages.application.run_orchestration.outcomes import RunOutcome, TaskOutcome
from packages.domain.events import EventType
from packages.domain.failure_policy import OnTaskFailure
from packages.domain.run_state import ResearchRunState

_Publish = Callable[..., None]


def publish_failed_run(
    publish: _Publish, run_id: str, message: str, system_failure: bool
) -> RunOutcome:
    """`run.failed`（既有语义不变：终局失败，后续工作不再跑）。"""
    publish(
        EventType.RUN_FAILED, {"run_id": run_id, "message": message}, run_id=run_id, trace_id=""
    )
    return RunOutcome(
        run_id=run_id,
        state=ResearchRunState.State.FAILED,
        message=message,
        system_failure=system_failure,
    )


def publish_degraded_run(
    publish: _Publish, ctx: Any, tolerated: tuple[TaskOutcome, ...], message: str
) -> RunOutcome:
    """`run.degraded`：payload 是这条 run 的**策略归属事实**（哪几条失败、哪条策略允许）。"""
    publish(
        EventType.RUN_DEGRADED,
        {
            "run_id": ctx.run_id,
            "message": message,
            "failure_policy": OnTaskFailure.CONTINUE,
            "tolerated_failures": [
                {
                    "task_id": outcome.task.id.value,
                    "message": outcome.message,
                    "failure_policy": outcome.failure_policy,
                }
                for outcome in tolerated
            ],
        },
        run_id=ctx.run_id,
        trace_id=ctx.trace_id or "",
    )
    return RunOutcome(
        run_id=ctx.run_id,
        state=ResearchRunState.State.DEGRADED,
        message=message,
        tasks=tolerated,
        manifest_digest=ctx.frozen_manifest_digest,
        system_failure=False,
    )


def compensate_failed_resume(publish: _Publish, run: Any, failure: BaseException) -> Any:
    """续跑失败 ⇒ canonical 放回 `PAUSED` 并记原因（GOAL-004 cycle 7 = EC-06）。

    失败**不是终态**，所以这里不返回 `RunOutcome`：把 run 迁回停车（既有域迁移
    `PAUSE`，与"重建被拒后回退"`、`POST /pause` 同一条路径）并发 `run.resume_failed`
    ——事件链是这次失败原因的 canonical 记录，读面不新增"停车原因"字段。

    调用方负责把返回的 run 落库（API 面与守护线程面各自的 store），本函数只做
    "迁移 + 发事件"两件事，不假装续跑成功、也不吞掉失败。
    """
    compensated = run.transition(ResearchRunState.Transition.PAUSE)
    publish(
        EventType.RUN_RESUME_FAILED,
        {
            "run_id": run.id.value,
            "failure_type": type(failure).__name__,
            "message": str(failure),
            "compensated_to": ResearchRunState.State.PAUSED,
        },
        run_id=run.id.value,
        trace_id="",
    )
    return compensated
