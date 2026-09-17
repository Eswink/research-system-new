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


class RunDetailDto(BaseModel):
    id: str
    project_id: str
    protocol_id: str
    state: str
    manifest_digest: str | None = None
    # GOAL-004 cycle 1：冻结协议正文的 digest。None = 旧 run 没有冻结正文
    # （重启续跑仍依赖那份外部来源可解析），非 None = 这条 run 自足可重建。
    protocol_body_digest: str | None = None
    created_at: str
    updated_at: str


class TaskDto(BaseModel):
    task_id: str
    contract_id: str
    agent_id: str | None = None
    status: str
    attempt: int
