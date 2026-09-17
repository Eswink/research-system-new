"""统一派发读面（GOAL-004 cycle 6 = EC-05 ②）：这条 run 现在谁在派发它。

两个派发方此前各持一半事实：retry dispatch 守护线程只看 `PAUSED` 的重排到期，worker
plane 的租约**完全不在读面**（一条 `RUNNING` 且任务正被 worker 持租约跑的 run，从控制面
看不出"有人在派发它"）。本模块把 port 的 `dispatch_ownership(run_id)` 直接落成 DTO：
重排数字 + 活租约持有者，`kind` 由 port 组合（`NONE`/`RETRY_DISPATCH`/`WORKER_CLAIM`/
`BOTH`），这里只补一个诚实降级——没有 workflow 读面或读面读不到（`PortError`）⇒
`UNKNOWN`，不猜 `NONE`。

本模块不拿墙钟比、不写任何状态、不缓存；"活"由 adapter 用权威时钟判定（生产：DB 时钟；
测试：注入时钟），是回收租约判据的补集。`lease_id` 有意不出现在读面（作业面凭据不复制）。
"""

from __future__ import annotations

from packages.application.ports.errors import PortError
from packages.application.ports.workflow_engine import DispatchOwnership, WorkflowEngine
from services.api.dto.runs import DispatchOwnershipDto, DispatchRetryDto, LeaseHolderDto

UNKNOWN = "UNKNOWN"


def dispatch_ownership_read(
    workflow: WorkflowEngine | None, run_id: str
) -> DispatchOwnership | None:
    """port 读的唯一入口：读不到返回 None（调用方据此给 UNKNOWN，而不是"没有"）。"""
    if workflow is None:
        return None
    try:
        return workflow.dispatch_ownership(run_id)
    except PortError:
        return None


def dispatch_ownership_view(workflow: WorkflowEngine | None, run_id: str) -> DispatchOwnershipDto:
    """统一派发读面的 HTTP 形状；读不到的诚实回答是 `UNKNOWN`。"""
    return dispatch_ownership_dto(dispatch_ownership_read(workflow, run_id))


def dispatch_ownership_dto(ownership: DispatchOwnership | None) -> DispatchOwnershipDto:
    """`DispatchOwnership`（或读不到时的 None）→ DTO（不重新分类，只映射）。"""
    if ownership is None:
        return DispatchOwnershipDto(kind=UNKNOWN)
    retry = ownership.retry
    return DispatchOwnershipDto(
        kind=ownership.kind,
        retry=DispatchRetryDto(
            scheduled=retry.scheduled,
            due=retry.due,
            next_retry_at=(retry.next_retry_at.value.isoformat() if retry.next_retry_at else None),
        ),
        holders=[
            LeaseHolderDto(
                task_id=holder.task_id,
                worker_id=holder.worker_id,
                fence=holder.fence,
                expires_at=(holder.expires_at.value.isoformat() if holder.expires_at else None),
            )
            for holder in ownership.leases
        ],
    )
