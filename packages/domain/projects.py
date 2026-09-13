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

    def renamed(self, name: str, *, at: Timestamp) -> "ProjectDefinition":
        return replace(self, name=name, updated_at=at)

    def with_status(self, status: ProjectStatus, *, at: Timestamp) -> "ProjectDefinition":
        """ACTIVE ⇄ ARCHIVED；同值视为幂等（返回新对象，updated_at 前进）。"""
        return replace(self, status=ProjectStatus(status), updated_at=at)
