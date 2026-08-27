"""AgentStore Port：AgentSpec 配置存储（M13-R1 引入）。

职责：Team/Agent 配置面持久化（wizard 后用户对 Agent 实例的绑定修改、
新增 Agent）。与 ModelStore/EndpointStore 同族（SQLite 配置存储，
M14 PostgreSQL canonical state 落地后替换实现，Port 不变）。
非职责：不做角色/模型选择、eligibility / preflight 编排（application use case）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.roles import AgentSpec


@runtime_checkable
class AgentStore(Protocol):
    """AgentSpec 存储；CRUD 语义由实现保证。"""

    def list_agents(self) -> list[AgentSpec]: ...

    def get_agent(self, agent_id: str) -> AgentSpec: ...

    def save_agent(self, agent: AgentSpec) -> None: ...

    def delete_agent(self, agent_id: str) -> None: ...
