"""run 终态事件的发布（GOAL-004 cycle 3 从 `service.py` 拆出：450 行硬上限）。

两条终态发布共享一个形状：发一个带"为什么"的 run 级事件，再返回对应的 `RunOutcome`。
差别只在语义——`RUN_FAILED`（任务终局失败且契约没有容忍）与 `RUN_DEGRADED`
（跑完了但有被容忍的失败）。预算预留的释放不在这里（`service` 持有 reservation refs）。

GOAL-004 cycle 7（EC-06）加入第三个发布：`compensate_failed_resume` —— 续跑**失败**不是
终态，它把 canonical 放回停车并记录原因，所以它返回改好状态的 run 而不是 `RunOutcome`。

GOAL-006 cycle 6（EC-06 (b)）加入第四个发布：`publish_compensation_failure` —— **补偿本身**
失败（守护线程面 store 不可用时的 `except: pass`）此前只留在遥测/log；这条发布把"这次补偿
没做成"写成 canonical 事实，读面（`GET /runs/{id}/events`）据此可判。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from packages.application.run_orchestration.outcomes import RunOutcome, TaskOutcome
from packages.domain.events import EventType
from packages.domain.failure_policy import OnTaskFailure
from packages.domain.run_state import ResearchRunState

_Publish = Callable[..., None]


def preflight_failure_message(report: Any) -> str:
    """preflight 失败的 run 消息（PA-1 F5；从 `service.py` 搬来守 450 行硬上限）。

    带上失败的 check 代号：未配置的控制面要说得出**哪一条检查**没过，而不是一句
    「preflight failed」。FAILED 的诚实语义不变——这只影响消息的可行动性。
    """
    codes = ", ".join(sorted({finding.code for finding in report.findings}))
    return f"preflight failed: {codes}" if codes else "preflight failed"


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


def publish_compensation_failure(
    publish: _Publish, run_id: str, failure: BaseException, canonical_state: Any
) -> None:
    """补偿失败 ⇒ 在 canonical 事件链留痕（GOAL-006 cycle 6 = EC-06 (b)）。

    守护线程面的补偿失败（store 不可用、发布失败等）此前走 `except: pass`：run 仍停在原
    canonical 状态、下一轮重新评估，但**这件事本身没有 canonical 痕迹**（RECHECK-090 W-4）。
    这条事件把"这次补偿没做成"变成可读的事实——读面 `GET /runs/{id}/events` 据此可判，
    不必去翻遥测/log。

    payload 键（判据按这一行核对）：`run_id` / `failure_type` / `message` / `canonical_state`。
    前三个与 `run.resume_failed` 同形，但 `failure_type` / `message` 描述的是**补偿**这次的
    失败（最初那次续跑失败由 `run.resume_failed` 记录）；`canonical_state` 是补偿失败时 run
    仍停在的状态（**没有**被伪造成 `PAUSED`）。
    """
    publish(
        EventType.RUN_RESUME_COMPENSATION_FAILED,
        {
            "run_id": run_id,
            "failure_type": type(failure).__name__,
            "message": str(failure),
            "canonical_state": canonical_state,
        },
        run_id=run_id,
        trace_id="",
    )
