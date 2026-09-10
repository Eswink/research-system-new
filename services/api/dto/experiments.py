"""实验控制面 DTO（WP-E）：项目级 run 视图 + 预注册计划创建/归档。

诚实语义：计划状态只呈现 DRAFT/PREREGISTERED/ARCHIVED（domain 权威）；
不存在 queued/running 计划状态，创建即预注册，执行归属由 run 证据呈现。
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
