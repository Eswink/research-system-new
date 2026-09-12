"""CatalogOverrideStore Port：用户自定义 Role/TeamTemplate 目录覆盖（PLAN-040 WP-B）。

职责：持久化 `{kind: {id: document}}` 形式的用户契约（document 为与
`examples/config/roles.yaml` / `team_templates.yaml` 子项同形的映射），供
`catalog_merge` 在合并视图里覆盖 examples 基底（与 EndpointStore/ModelStore/
AgentStore 同一配置面语义；SQLite 配置存储，两组成同侧）。
非职责：不做契约 schema 校验（调用方经 `adapters.contracts.base.validate_instance`
+ domain 构造完成）；不定义 kind 词表（调用方封闭集合）。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CatalogOverrideStore(Protocol):
    """kind/id 两级键的契约覆盖存储；upsert 语义，list 按 id 确定性排序。"""

    def upsert(self, kind: str, entity_id: str, document: dict[str, Any]) -> None: ...

    def get(self, kind: str, entity_id: str) -> dict[str, Any] | None: ...

    def list(self, kind: str) -> list[dict[str, Any]]: ...

    def delete(self, kind: str, entity_id: str) -> bool: ...

    def close(self) -> None: ...
