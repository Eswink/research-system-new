"""实验控制面 DTO（WP-E）：项目级 run 视图 + 预注册计划创建/归档 + G14 队列。

诚实语义：计划状态只呈现 DRAFT/PREREGISTERED/ARCHIVED（domain 权威）；
队列条目状态只呈现域状态机取值（QUEUED/DISPATCHING/DISPATCHED/FAILED/CANCELLED），
不发明"进度百分比"之类域内不存在的字段。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExperimentRunRowDto(BaseModel):
    """项目级 experiment run 行（evidence 聚合 + run 归属）。"""

    run_id: str
    experiment_run_id: str
    artifact_ids: list[str] = Field(default_factory=list)
    image_digest: str | None = None
    environment_digest: str | None = None
    metrics: dict[str, object] = Field(default_factory=dict)
    reproduction_available: bool = False


class ProjectExperimentsViewDto(BaseModel):
    experiments: list[ExperimentRunRowDto] = Field(default_factory=list)
    reproduction_note: str = ""


class ExperimentPlanCreateDto(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    hypothesis: str | None = Field(default=None, max_length=2000)
    task_contract_ref: str | None = Field(default=None, max_length=200)


class ExperimentPlanDto(BaseModel):
    id: str
    name: str
    hypothesis: str | None = None
    task_contract_ref: str | None = None
    input_spec_digest: str | None = None
    state: str
    created_at: str
    updated_at: str


class ExperimentQueueEnqueueDto(BaseModel):
    """入队请求：协议来源二选一（path 或 draft 修订）+ 可选排期。"""

    protocol_path: str | None = Field(default=None, max_length=500)
    draft_id: str | None = Field(default=None, max_length=200)
    draft_revision: int | None = Field(default=None, ge=1)
    not_before: str | None = Field(default=None, max_length=40)


class ExperimentQueueRescheduleDto(BaseModel):
    """改期请求：null 表示清除排期（立即到期）。"""

    not_before: str | None = Field(default=None, max_length=40)


class ExperimentQueueEntryDto(BaseModel):
    id: str
    project_id: str
    plan_id: str
    plan_name: str | None = None
    protocol_path: str | None = None
    draft_id: str | None = None
    draft_revision: int | None = None
    state: str
    not_before: str | None = None
    claimed_at: str | None = None
    run_id: str | None = None
    failure_reason: str | None = None
    created_at: str
    updated_at: str


class ExperimentQueueViewDto(BaseModel):
    entries: list[ExperimentQueueEntryDto] = Field(default_factory=list)
    dispatch_note: str = ""
