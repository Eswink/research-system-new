"""ProjectStore Port：ProjectDefinition 注册条目存储（PLAN-041 EC-01）。

配置面语义与 EndpointStore/ModelStore/AgentStore/CatalogOverrideStore 同族
（SQLite 实现，PG canonical 迁移属配置面 follow-up）。默认 example-project
由控制面在读取时合成（examples/config/project.yaml），store 行为用户项目与
override 条目；本 Port 不隐式播种。未知 id 读取抛 KeyError（AgentStore 同约定）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.projects import ProjectDefinition


@runtime_checkable
class ProjectStore(Protocol):
    """项目注册 CRUD；list 按 created_at, id 确定性排序。"""

    def list_projects(self) -> list[ProjectDefinition]: ...

    def get_project(self, project_id: str) -> ProjectDefinition: ...

    def save_project(self, project: ProjectDefinition) -> None: ...

    def close(self) -> None: ...
