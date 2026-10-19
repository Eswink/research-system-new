"""Project 注册表 DTO（PLAN-041 WP-A）。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from services.api.dto.common import StrictRequestDto


class ProjectDto(BaseModel):
    id: str
    name: str
    status: Literal["ACTIVE", "ARCHIVED"]
    created_at: str
    updated_at: str
    #: GOAL-20261019-089 EC-02：研究方向（`None` = 未声明）。与 `name` **分开**：
    #: 名字是标识，方向是研究链的输入。
    direction: str | None = None


class ProjectCreateDto(StrictRequestDto):
    """创建项目：命名 + 可选研究方向；id 服务端生成，默认设置自动落行。"""

    name: str = Field(min_length=1, max_length=200)
    direction: str | None = Field(default=None, max_length=2000)


class ProjectUpdateDto(StrictRequestDto):
    """重命名 / 归档 / **声明或清除方向**（ACTIVE ⇄ ARCHIVED；不提供删除）。

    `direction` 的三种形态**分得开**：缺省（不出现）= 不动；`null` = 清除；
    字符串 = 声明。这把「没提到」与「清掉」分开 —— 与既有 `name` / `status` 的口径一致。
    """

    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: Literal["ACTIVE", "ARCHIVED"] | None = None
    direction: str | None = Field(default=None, max_length=2000)


class ProjectDirectionUpdateDto(StrictRequestDto):
    """方向字段的**专用**写面（与 `PATCH /projects/{id}` 的 direction 同一条落库路径）。

    单独一条路由是为了让「只改方向」不必与「改名 / 归档」共用一个请求体：
    调用方（尤其是程序推进链）可以只声明方向而**不可能**顺手改名。
    """

    direction: str | None = Field(default=None, max_length=2000)
