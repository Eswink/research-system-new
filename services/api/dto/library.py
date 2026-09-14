"""Library 库目录 DTO（PLAN-20260914-044 WP-B）。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ResourceKindValue = Literal["prompt", "dataset", "notebook"]
ResourceStatusValue = Literal["ACTIVE", "ARCHIVED"]


class LibraryResourceDto(BaseModel):
    id: str
    project_id: str
    kind: ResourceKindValue
    name: str
    description: str
    content_ref: str | None
    tags: list[str]
    status: ResourceStatusValue
    created_at: str
    updated_at: str


class LibraryResourceCreateDto(BaseModel):
    """创建库条目：id 服务端生成；kind 决定归属页面。"""

    kind: ResourceKindValue
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    content_ref: str | None = Field(default=None, max_length=512)
    tags: list[str] = Field(default_factory=list, max_length=32)


class LibraryResourceUpdateDto(BaseModel):
    """重命名与/或归档（ACTIVE ⇄ ARCHIVED；不提供删除）。"""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: ResourceStatusValue | None = None
