"""Project 注册表 DTO（PLAN-041 WP-A）。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProjectDto(BaseModel):
    id: str
    name: str
    status: Literal["ACTIVE", "ARCHIVED"]
    created_at: str
    updated_at: str


class ProjectCreateDto(BaseModel):
    """创建项目：仅命名；id 服务端生成，默认设置自动落行（可随后编辑）。"""

    name: str = Field(min_length=1, max_length=200)


class ProjectUpdateDto(BaseModel):
    """重命名与/或归档（ACTIVE ⇄ ARCHIVED；不提供删除）。"""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: Literal["ACTIVE", "ARCHIVED"] | None = None
