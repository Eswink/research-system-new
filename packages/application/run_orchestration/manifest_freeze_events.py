"""拒冻（`ManifestFreezeError`）的**可读事件**（GOAL-20261119-115 EC-03 ③）。

**它补哪一格**（建档实测）：24 次 `dual_model_review` FAILED 里有 **5 次** `outbox_events`
**为空** —— 任务从未派发，读面表现为「秒失败、无原因」。根因是
`start_run` 里 `freeze_manifest(...)` 抛出 `ManifestFreezeError` 时**没有捕获**：
preflight FAIL 走的是 `_fail_run` → `publish_failed_run`（有 `run.failed`），
而拒冻是**裸抛** ⇒ 事件面什么都没有。

**本模块的边界**：只负责「把拒冻变成一条可读事件 + 一个失败结局」，不判该不该拒
（那是 `evaluate_freeze_acceptance` 的职责），也不改 `report.passed` 的语义。

**为什么单独一个文件**：`service.py` 已在 440/450 行硬上限上，往里加 15 行会越界；
本的函数被 `start_run` 调用，不是把逻辑藏起来。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from packages.application.preflight.preflight import ManifestFreezeError

if TYPE_CHECKING:  # pragma: no cover - 只用于注解，运行期不导入
    from packages.application.run_orchestration.outcomes import RunOutcome

#: 拒冻事件的 payload 键（读面按它取清单）。
MISSING_KEY = "missing"
REASON_KEY = "reason"


def freeze_refusal_payload(run_id: str, error: BaseException) -> dict[str, Any]:
    """拒冻错误 → `run.failed` 的 payload（**带可读原因**，不只是异常字符串）。

    清单从错误的**结构化字段**取（`missing` 若存在）；没有结构化字段时退化成
    一句脱敏后的原因 —— **两者都写进 payload**，读面永远有东西可读。
    """
    raw_missing = getattr(error, "missing", None)
    missing = [str(item) for item in raw_missing] if raw_missing else []
    reason = str(error) or type(error).__name__
    return {
        "run_id": run_id,
        REASON_KEY: "manifest_freeze_refused",
        MISSING_KEY: missing,
        "message": reason,
    }


def publish_freeze_refusal(publish: Any, run_id: str, error: BaseException) -> RunOutcome:
    """把拒冻写成**一条** `run.failed` 并返回失败结局。

    **只发一次**（实测教训）：最初写成「先 `publish_freeze_refusal`、再
    `_fail_run`」时，本机实测发布了**两条** `run.failed`（`_fail_run` 内部还会调
    `publish_failed_run`）—— 读面会把一次拒冻读成两次失败。这里直接返回
    `RunOutcome`，调用方**不再**走 `_fail_run`。

    复用 `EventType.RUN_FAILED`（**不扩事件词表**）：读面已经在订阅它，
    新增类型会让「失败但读面看不见」的缺口换个形式回来。
    """
    from packages.application.run_orchestration.outcomes import RunOutcome as _Outcome
    from packages.domain.events import EventType
    from packages.domain.run_state import ResearchRunState

    payload = freeze_refusal_payload(run_id, error)
    publish(EventType.RUN_FAILED, payload, run_id=run_id, trace_id="")
    return _Outcome(
        run_id=run_id,
        state=ResearchRunState.State.FAILED,
        message=payload["message"],
        system_failure=True,
    )


__all__ = [
    "MISSING_KEY",
    "REASON_KEY",
    "freeze_refusal_payload",
    "is_freeze_refusal",
    "publish_freeze_refusal",
]


def is_freeze_refusal(error: BaseException) -> bool:
    """判据与实现共用同一个类型判定（避免两处各写一份 `isinstance`）。"""
    return isinstance(error, ManifestFreezeError)
