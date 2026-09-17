"""Run 生命周期 DTO。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RunStartDto(BaseModel):
    """启动运行：旧 `protocol_path` 与新草稿修订引用二选一。

    草稿修订引用（PLAN-20260908-033）：服务端加载不可变修订正文后走
    与 path 完全相同的 Compile → Preflight → Freeze 链；草稿后续变化
    不改写已冻结运行。
    """

    protocol_path: str | None = Field(default=None, min_length=1, max_length=500)
    draft_id: str | None = Field(default=None, min_length=1, max_length=120)
    draft_revision: int | None = Field(default=None, ge=1)
    trace_id: str | None = Field(default=None, max_length=200)


class PausedDispatchDto(BaseModel):
    """`PAUSED` 的派发语义（GOAL-004 cycle 2 = EC-02）。

    只由 canonical 事实推出（run 行状态 + 任务行 `RETRY_SCHEDULED`/`retry_at`），
    不是"停车原因"字段：没有第二个会被别的状态变更写脏的标志位。

    - `kind=RETRY_SCHEDULED`：任务面有重排 ⇒ 守护线程会在到期后自己续跑；
      `due_now=true` 表示**现在**就已经到期（含"重建被拒后放回停车"这一种，
      拒绝原因不在读面）。
    - `kind=USER_PAUSED`：任务面没有任何重排 ⇒ 只有人工 resume/cancel 会动它。
    - `kind=UNKNOWN`：没有 workflow 读面（或读面读不到）⇒ 不猜。
    """

    kind: str
    next_retry_at: str | None = None
    due_now: bool = False


class DispatchRetryDto(BaseModel):
    """重排读面（与 `PausedDispatchDto` 同一判据、同一次读出的数字）。"""

    scheduled: int = 0
    due: int = 0
    next_retry_at: str | None = None


class LeaseHolderDto(BaseModel):
    """一个**活着**的租约持有者（读面不复制作业面凭据 `lease_id`）。

    `worker_id` 为空 = 租约由控制面自己持有（agent session 投递），非空 = worker plane
    的 claim；`expires_at` 是 canonical 租约行上的到期时刻。
    """

    task_id: str
    worker_id: str | None = None
    fence: int = 0
    expires_at: str | None = None


class DispatchOwnershipDto(BaseModel):
    """统一派发读面（GOAL-004 cycle 6 = EC-05 ②）：这条 run 现在谁在派发它。

    与 `PausedDispatchDto` 的区别：那一个只回答 `PAUSED` 的**停车语义**（会不会自己走），
    这一个对**任何状态**回答"有没有活的派发方、是哪一个"。两者由**同一次** port 读
    （`WorkflowEngine.dispatch_ownership`）分解而来，不会各说各话。

    - `kind=WORKER_CLAIM`：有**活着**的租约持有者（工人 claim 或控制面自身的投递）；
    - `kind=RETRY_DISPATCH`：任务面有重排（等时钟或已到期）⇒ 派发守护会（或马上会）续跑；
    - `kind=BOTH`：两件事实同时存在；
    - `kind=NONE`：都没有（停车等人工介入的 run 通常落在这里）；
    - `kind=UNKNOWN`：没有 workflow 读面（或读面读不到）⇒ 不猜。

    "活"由 adapter 用权威时钟判定（回收判据的补集）；读面只读 canonical 事实，不回答
    执行健康度（心跳新鲜度、进度、卡死与否都不在这里）。
    """

    kind: str
    retry: DispatchRetryDto = Field(default_factory=DispatchRetryDto)
    holders: list[LeaseHolderDto] = Field(default_factory=list)


class RunDetailDto(BaseModel):
    id: str
    project_id: str
    protocol_id: str
    state: str
    manifest_digest: str | None = None
    # GOAL-004 cycle 4：冻结的**语义 digest**（排除 frozen_at，resume 漂移校验的输入）。
    # 非空 = 这条 run 冻结过 manifest 且事件里带这项；执行期失败收敛的 run 同样带
    # （此前只带 manifest_digest）。None = 未冻结或事件早于本轮，不保证可重建。
    manifest_semantic_digest: str | None = None
    # GOAL-004 cycle 1：冻结协议正文的 digest。None = 旧 run 没有冻结正文
    # （重启续跑仍依赖那份外部来源可解析），非 None = 这条 run 自足可重建。
    protocol_body_digest: str | None = None
    # GOAL-004 cycle 2：仅当 state == PAUSED 时非 None（其余状态"不适用"）。
    paused_dispatch: PausedDispatchDto | None = None
    # GOAL-004 cycle 6：统一派发读面（任何状态都给；与 paused_dispatch 同一次读分解而来）。
    dispatch: DispatchOwnershipDto | None = None
    created_at: str
    updated_at: str


class TaskDto(BaseModel):
    task_id: str
    contract_id: str
    agent_id: str | None = None
    status: str
    attempt: int
