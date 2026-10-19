"""Project 域：单用户规模的项目注册条目（PLAN-20260912-041 / EC-01）。

ProjectDefinition 是配置面注册事实（项目身份与生命周期），不是租户边界：
多用户/RBAC/成员管理属 M18 deferred，本模块不表达授权语义。注册条目与
ProjectSettings（编译/preflight 消费的项目设置）分离：前者回答"有哪些项目"，
后者回答"项目如何运行"。状态机极简：ACTIVE ⇄ ARCHIVED（归档非删除；
不提供项目 DELETE，运行历史须保留）。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from packages.domain.core import Timestamp

MAX_PROJECT_ID_LENGTH = 128
MAX_PROJECT_NAME_LENGTH = 200
#: GOAL-20261019-089 EC-02：研究方向的长度界（与 name 同量级；空串视为未声明）。
MAX_PROJECT_DIRECTION_LENGTH = 2000


class ProjectStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True)
class ProjectDefinition:
    id: str
    name: str
    status: ProjectStatus
    created_at: Timestamp
    updated_at: Timestamp
    #: GOAL-20261019-089 EC-02：**研究方向**（用户要研究什么）。`None` = 未声明
    #: （缺省 ⇒ 既有行与既有读面**逐字**不变）。
    #:
    #: **为什么不塞进 `name`**：`renamed()` 是改名语义（UIP: 名字是标识给人的标签），
    #: 与「研究什么」是两件事；二者的生命周期与判据都不同（改名可以随时改，方向是
    #: 研究链的输入）。分开之后，读面能分别回答「它叫什么」与「它研究什么」。
    direction: str | None = None

    def __post_init__(self) -> None:
        if not self.id or len(self.id) > MAX_PROJECT_ID_LENGTH:
            raise ValueError(f"project id must be non-empty and <= {MAX_PROJECT_ID_LENGTH} chars")
        name = self.name.strip()
        if not name or len(name) > MAX_PROJECT_NAME_LENGTH:
            raise ValueError(
                f"project name must be non-empty and <= {MAX_PROJECT_NAME_LENGTH} chars",
            )
        if not isinstance(self.status, ProjectStatus):
            raise ValueError(f"unknown project status: {self.status!r}")
        if self.direction is not None:
            direction = self.direction.strip()
            if not direction:
                # 空串不等于「未声明」：两种形态在落库/读面上必须分得开。
                raise ValueError("project direction must not be blank when declared")
            if len(direction) > MAX_PROJECT_DIRECTION_LENGTH:
                raise ValueError(
                    f"project direction must be <= {MAX_PROJECT_DIRECTION_LENGTH} chars",
                )
            object.__setattr__(self, "direction", direction)

    def renamed(self, name: str, *, at: Timestamp) -> "ProjectDefinition":
        return replace(self, name=name, updated_at=at)

    def with_direction(self, direction: str | None, *, at: Timestamp) -> "ProjectDefinition":
        """声明 / 清除研究方向（`None` = 清除；`updated_at` 前进）。

        **与 `renamed()` 分开**：改名不改方向、改方向不改名 —— 一件动作一个方法，
        调用方不会因为「顺手改了名字」而丢掉方向。
        """
        return replace(self, direction=direction, updated_at=at)

    def with_status(self, status: ProjectStatus, *, at: Timestamp) -> "ProjectDefinition":
        """ACTIVE ⇄ ARCHIVED；同值视为幂等（返回新对象，updated_at 前进）。"""
        return replace(self, status=ProjectStatus(status), updated_at=at)
