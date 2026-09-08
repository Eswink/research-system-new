"""协议草稿编写应用模块（PLAN-20260908-033）。

职责：草稿读取/校验/保存与修订引用解析；YAML 解析经由
adapters.contracts.protocol_loaders 的同一 Schema 与编译器链。
不把 YAML 解析或存储逻辑堆进现有路由。
"""

from __future__ import annotations

from packages.application.protocol_authoring.memory_store import InMemoryProtocolDraftStore
from packages.application.protocol_authoring.service import (
    DraftService,
    DraftTemplates,
    ProtocolDraftValidationError,
)

__all__ = [
    "DraftService",
    "DraftTemplates",
    "InMemoryProtocolDraftStore",
    "ProtocolDraftValidationError",
]
