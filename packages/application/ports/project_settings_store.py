"""ProjectSettingsStore Port：项目设置记录存储（M13-R1 引入，PLAN-041 项目化）。

职责：持久化各项目（wizard 默认项目 + 注册表项目）的运行设置
（team template / default model profile / budget policy / workspace backend /
policy / 参考协议）。get 按 project_id 精确读取；未配置返回 None，examples
回退只属于控制面合并层（catalog_merge），不伪装 store 数据。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.application.ports.resource_catalog import ProjectSettings


@runtime_checkable
class ProjectSettingsStore(Protocol):
    """项目设置读取/保存；语义由实现保证。

    `delete` 幂等（行不存在时静默返回）：设置行与项目注册同生，项目删除时随之
    清理；单独缺行只说明该项目的设置从未落库，不构成错误。
    """

    def get(self, project_id: str) -> ProjectSettings | None: ...

    def save(self, settings: ProjectSettings) -> None: ...

    def delete(self, project_id: str) -> None: ...
