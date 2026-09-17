"""run 终态事件的发布（GOAL-004 cycle 3 从 `service.py` 拆出：450 行硬上限）。

两条终态发布共享一个形状：发一个带"为什么"的 run 级事件，再返回对应的 `RunOutcome`。
差别只在语义——`RUN_FAILED`（任务终局失败且契约没有容忍）与 `RUN_DEGRADED`
（跑完了但有被容忍的失败）。预算预留的释放不在这里（`service` 持有 reservation refs）。
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
