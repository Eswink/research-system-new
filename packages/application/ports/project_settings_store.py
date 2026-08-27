"""ProjectSettingsStore Port：项目设置单条记录存储（M13-R1 引入）。

职责：持久化 wizard 默认项目之后的设置覆盖（team template / default
model profile / budget policy / workspace backend / policy）。
单条记录语义（M13 控制面只有 example-project 一个项目；多项目为 M14/M18 范围）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.application.ports.resource_catalog import ProjectSettings


@runtime_checkable
class ProjectSettingsStore(Protocol):
    """项目设置读取/保存；语义由实现保证。"""

    def get(self) -> ProjectSettings | None: ...

    def save(self, settings: ProjectSettings) -> None: ...
