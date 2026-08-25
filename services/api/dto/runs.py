"""Run 生命周期 DTO。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RunStartDto(BaseModel):
    protocol_path: str = Field(min_length=1, max_length=500)
    trace_id: str | None = Field(default=None, max_length=200)


class RunDetailDto(BaseModel):
    id: str
    project_id: str
    protocol_id: str
    state: str
    manifest_digest: str | None = None
    created_at: str
    updated_at: str


class TaskDto(BaseModel):
    task_id: str
    contract_id: str
    agent_id: str | None = None
    status: str
    attempt: int
