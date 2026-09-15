"""ToolProviderRegistry Port：用户注册的 tool provider 生命周期（PLAN-20260915-060）。

与 `ToolPackStore`（pinned pack 目录）分开：pack 是供应链产物，注册面是
"用户带来的 provider 规格 + pin + 批准状态"。实现必须做到：

- `get_registration` 未知 id 抛 `KeyError`（路由层翻译成 404）；
- `save_registration` 为 upsert（按 id 覆盖）；
- `delete_registration` 未知 id 抛 `KeyError`；
- 列表**确定性排序**（按 id），调用方不需再排。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.tool_registry import ProviderRegistration


@runtime_checkable
class ToolProviderRegistry(Protocol):
    def list_registrations(self) -> tuple[ProviderRegistration, ...]: ...

    def get_registration(self, provider_id: str) -> ProviderRegistration: ...

    def save_registration(self, registration: ProviderRegistration) -> None: ...

    def delete_registration(self, provider_id: str) -> None: ...
