"""停车语义读面（GOAL-004 cycle 2 = EC-02）：这条停车会不会自己走。

`PAUSED` 有三种来源（重排到期续跑、用户暂停、重建被拒后放回停车），读面只读两件
canonical 事实——run 行状态与任务行的 `RETRY_SCHEDULED`/`retry_at`——所以只给三个回答：

- `RETRY_SCHEDULED`：任务面有重排在等时钟（`due_now=false`）或已经到期（`due_now=true`）
  ⇒ 派发守护会（或马上会）自己把它续起来；**重建被拒后放回的停车也落在这里**：读面
  如实回答"有重排且已到期"，但拒绝原因不在读面（只在本进程遥测/日志，见
  `docs/api/CONTROL_PLANE_API.md`）。
- `USER_PAUSED`：停着且任务面没有任何重排 ⇒ 只有人工 resume/cancel 会动它。
- `UNKNOWN`：控制面没有 workflow 读面，或读面自己读不到（adapter 边界错误）⇒ 不猜。

分类不在这里做：`WorkflowEngine.dispatch_ownership` 在 adapter 内用**权威时钟**完成
（生产：DB 时钟；测试：注入时钟），与调度器判断到期与否同一处。本模块不拿墙钟比、
不写任何状态、不缓存。

GOAL-004 cycle 6：本视图改为消费**同一次读**的结果（`DispatchOwnershipDto`，由
`run_dispatch_view` 从 `dispatch_ownership` 映射而来）——`GET /runs/{id}` 的
`paused_dispatch` 与 `dispatch` 因此出自一个调用、一个时钟，不会各说各话。
取值与判据逐字不变（`UNKNOWN` 仍是"读不到"，不是"没有"）。
"""

from __future__ import annotations

from packages.domain.run_state import ResearchRunState
from services.api.dto.runs import DispatchOwnershipDto, PausedDispatchDto

RETRY_SCHEDULED = "RETRY_SCHEDULED"
USER_PAUSED = "USER_PAUSED"
UNKNOWN = "UNKNOWN"


def paused_dispatch_view(state: str, dispatch: DispatchOwnershipDto) -> PausedDispatchDto | None:
    """`PAUSED` 的派发语义；非 `PAUSED` 返回 None（不适用，而不是 "false"）。

    `dispatch` 是同一次 `dispatch_ownership` 读的 DTO：`kind=UNKNOWN` 表示读面读不到
    （没有 workflow 读面，或 adapter 边界错误）⇒ 这里同样回答 UNKNOWN，绝不因此
    退回 `USER_PAUSED`（"读不到"≠"不会自己走"）。
    """
    if state != ResearchRunState.State.PAUSED:
        return None
    if dispatch.kind == UNKNOWN:
        return PausedDispatchDto(kind=UNKNOWN)
    if dispatch.retry.scheduled or dispatch.retry.due:
        return PausedDispatchDto(
            kind=RETRY_SCHEDULED,
            next_retry_at=dispatch.retry.next_retry_at,
            due_now=dispatch.retry.due > 0,
        )
    return PausedDispatchDto(kind=USER_PAUSED)
