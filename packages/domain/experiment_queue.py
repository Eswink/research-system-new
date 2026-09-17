"""ExperimentQueueEntry 域实体（G14 实验队列与调度）。

队列条目把"某项目下某个预注册计划，用哪个协议来源、在什么时间之后启动"落为
类型化实体：

- `QueueProtocolSource`：入队时冻结的协议来源（受控模板路径 **或** 草稿不可变
  修订，二者互斥）。冻结来源而不是冻结协议正文：派发时按来源重新解析，与
  `POST /runs` 同一条装配链（单一协议解析权威，不建第二份协议副本）。
- `ExperimentQueueEntry`：状态机权威在 `ExperimentQueueState`；每次迁移构造新
  实例（与 ExperimentPlan/Run 同一模式），`updated_at` 随之推进。

非职责：不派发（`services.api.experiment_queue`）、不执行 run（应用层编排链）、
不做持久化决策（`ExperimentStore` Port）。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from packages.domain.core import ID, Timestamp
from packages.domain.experiment_state import ExperimentQueueState
from packages.domain.protocol_source import ProtocolSource
from packages.domain.state_base import InvalidTransitionError

# 改期不是状态迁移（状态不变、排期事实变），但同样只对 QUEUED 合法；
# 非法时复用同一异常类型，动作用事件名表达，避免第二套错误词汇。
RESCHEDULE = "RESCHEDULE"

# 协议来源值对象由 `packages.domain.protocol_source` 拥有（run 与队列共用同一个
# 事实）；本模块保留入队语境下的历史名字，避免调用点与持久化行做无意义改名。
QueueProtocolSource = ProtocolSource


@dataclass(frozen=True, slots=True)
class ExperimentQueueEntry:
    """排队中的实验启动请求；状态迁移构造新实例，旧实例保留历史。"""

    id: ID
    project_id: str
    plan_id: ID
    source: QueueProtocolSource
    not_before: Timestamp | None = None
    state: str = ExperimentQueueState.State.QUEUED
    run_id: str | None = None
    failure_reason: str | None = None
    claimed_at: Timestamp | None = None
    created_at: Timestamp = field(default_factory=Timestamp.now)
    updated_at: Timestamp = field(default_factory=Timestamp.now)

    def __post_init__(self) -> None:
        if not self.project_id:
            raise ValueError("queue entry project_id must not be empty")

    @property
    def is_terminal(self) -> bool:
        return self.state in ExperimentQueueState.terminal()

    def is_due(self, now: Timestamp) -> bool:
        """到期判定：QUEUED 且未设排期或排期已到。"""
        if self.state != ExperimentQueueState.State.QUEUED:
            return False
        return self.not_before is None or self.not_before.value <= now.value

    # 迁移方法：状态由 ExperimentQueueState 判定，updated_at 随每次迁移推进。

    def claim(self, now: Timestamp) -> ExperimentQueueEntry:
        state = ExperimentQueueState.transition(self.state, ExperimentQueueState.Transition.CLAIM)
        return replace(self, state=state, claimed_at=now, updated_at=now)

    def requeue(self, now: Timestamp) -> ExperimentQueueEntry:
        """认领过期：回到 QUEUED，清空认领时间与上次失败原因。"""
        state = ExperimentQueueState.transition(
            self.state, ExperimentQueueState.Transition.CLAIM_EXPIRED
        )
        return replace(self, state=state, claimed_at=None, failure_reason=None, updated_at=now)

    def mark_dispatched(self, run_id: str) -> ExperimentQueueEntry:
        if not run_id:
            raise ValueError("dispatched entry requires a run id")
        state = ExperimentQueueState.transition(
            self.state, ExperimentQueueState.Transition.COMPLETE_DISPATCH
        )
        return replace(self, state=state, run_id=run_id, updated_at=Timestamp.now())

    def mark_failed(self, reason: str) -> ExperimentQueueEntry:
        if not reason:
            raise ValueError("failed entry requires a reason")
        state = ExperimentQueueState.transition(
            self.state, ExperimentQueueState.Transition.COMPLETE_FAILURE
        )
        return replace(self, state=state, failure_reason=reason, updated_at=Timestamp.now())

    def cancel(self, now: Timestamp) -> ExperimentQueueEntry:
        state = ExperimentQueueState.transition(self.state, ExperimentQueueState.Transition.CANCEL)
        return replace(self, state=state, updated_at=now)

    def reschedule(self, not_before: Timestamp | None, now: Timestamp) -> ExperimentQueueEntry:
        """改期：只对 QUEUED 合法；状态不变，改的是排期事实。"""
        if self.state != ExperimentQueueState.State.QUEUED:
            raise InvalidTransitionError(self.state, RESCHEDULE)
        return replace(self, not_before=not_before, updated_at=now)


__all__ = ["ExperimentQueueEntry", "QueueProtocolSource"]
