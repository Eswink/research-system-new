"""ops 调度写面 DTO（GOAL-003 EC-03 / PLAN-066）。

`job` 在请求里是**字符串**：DTO 层不 import domain（架构门禁 `api-dto-purity`），
词表校验因此由服务端 `ScheduleRegistry.create` 做（未知作业 → 422 并点名词表）。
响应里同样是字符串值，便于 console 直接渲染；可选作业由 `SchedulesViewDto.jobs`
给出（读面即词表）。运行事实字段一律可为 null——进程刚起、作业未跑过时不存在
"0 次成功"这种伪造事实。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScheduleEntryDto(BaseModel):
    name: str
    job: str
    interval_seconds: float
    purpose: str
    enabled: bool
    builtin: bool = False
    note: str = ""
    executor_attached: bool = False
    run_count: int = 0
    last_run_at: str | None = None
    last_outcome: str | None = None
    last_error: str | None = None
    next_due_at: str | None = None


class ScheduleJobDto(BaseModel):
    """作业词表项：新增定义只能绑定它，界面据此渲染可选作业。"""

    job: str
    purpose: str


class SchedulesViewDto(BaseModel):
    schedules: list[ScheduleEntryDto] = Field(default_factory=list)
    jobs: list[ScheduleJobDto] = Field(default_factory=list)
    note: str = ""
    management_available: bool = False
    management_reason: str | None = None


class ScheduleCreateDto(BaseModel):
    name: str
    job: str = Field(
        description=(
            "作业词表项（取值域由服务端校验，未知作业 → 422 并点名合法值）；"
            "可选值见 GET /ops/schedules 的 `jobs` 字段——那是词表的权威读面。"
        )
    )
    interval_seconds: float
    enabled: bool = True
    note: str = ""


class ScheduleUpdateDto(BaseModel):
    """启停 / 改 interval；作业类型不可变（换作业等于换执行体绑定）。"""

    enabled: bool | None = None
    interval_seconds: float | None = None
