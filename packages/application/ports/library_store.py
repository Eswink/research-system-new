"""LibraryStore Port：库目录条目的持久化契约（PLAN-20260914-044 WP-A）。

list 支持按 project 与可选 kind 过滤；未知 id 的 get 抛 KeyError（与
ProjectStore/AgentStore 同语义）；save 为 upsert。
"""

from __future__ import annotations

from typing import Protocol

from packages.domain.library import LibraryResource, ResourceKind


class LibraryStore(Protocol):
    def list_resources(
        self, project_id: str, kind: ResourceKind | None = None
    ) -> list[LibraryResource]: ...

    def get_resource(self, resource_id: str) -> LibraryResource: ...

    def save_resource(self, resource: LibraryResource) -> None: ...

    def close(self) -> None: ...
