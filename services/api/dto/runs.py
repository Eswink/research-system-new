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


class RunDetailDto(BaseModel):
    id: str
    project_id: str
    protocol_id: str
    state: str
    manifest_digest: str | None = None
    # GOAL-004 cycle 1：冻结协议正文的 digest。None = 旧 run 没有冻结正文
    # （重启续跑仍依赖那份外部来源可解析），非 None = 这条 run 自足可重建。
    protocol_body_digest: str | None = None
    # GOAL-004 cycle 2：仅当 state == PAUSED 时非 None（其余状态"不适用"）。
    paused_dispatch: PausedDispatchDto | None = None
    created_at: str
    updated_at: str


class TaskDto(BaseModel):
    task_id: str
    contract_id: str
    agent_id: str | None = None
    status: str
    attempt: int
