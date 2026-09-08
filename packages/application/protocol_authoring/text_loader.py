"""协议草稿修订 → 编译链入口（PLAN-20260908-033）。

runs 路由的草稿修订引用需要从不可变 YAML 文本构造 ProtocolDefinition；
具体 YAML/Schema 加载属于 adapter 能力，应用层只定义 Protocol 接口，
由 composition root 注入实现（adapters.contracts.protocol_text_loader）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.protocols import ProtocolDefinition


@runtime_checkable
class ProtocolTextLoader(Protocol):
    """内存 YAML 文本 → ProtocolDefinition（同一 Schema 校验链）。"""

    def __call__(self, text: str) -> ProtocolDefinition: ...
