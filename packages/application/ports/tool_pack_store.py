"""ToolPackStore Port：ToolPack install/update/revoke 生命周期状态。

职责：保存 ToolPack 注册状态（ToolPackRecord）；install/update/revoke
状态迁移由 use case（packages/application/tool_plane/lifecycle.py）驱动，
本 Port 只做状态持久化与读取；install 对已存在 pack_id 抛 InvalidInputError，
revoke 对不存在 pack_id 抛 InvalidInputError（防止静默覆盖）。
非职责：不做供应链验证（digest 校验在 use case）；不做 policy 裁决
（PolicyEvaluator）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, runtime_checkable

from packages.domain.core import Timestamp
from packages.domain.enums import ToolPackState
from packages.domain.tools import ToolPackManifest


@dataclass(frozen=True, slots=True)
class ToolPackRecord:
    pack_id: str
    state: ToolPackState
    manifest: ToolPackManifest
    installed_at: Timestamp
    revoked_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.pack_id:
            raise ValueError("pack_id must not be empty")
        if self.pack_id != self.manifest.id:
            raise ValueError("pack_id must match manifest id")
        if self.state is ToolPackState.REVOKED and not self.revoked_reason:
            raise ValueError("revoked tool pack must carry a reason")


@runtime_checkable
class ToolPackStore(Protocol):
    """ToolPack 注册状态存储；写入方法同步语义。"""

    def install(self, record: ToolPackRecord) -> None: ...

    def replace(self, record: ToolPackRecord) -> None: ...

    def revoke(self, pack_id: str, reason: str) -> None: ...

    def get(self, pack_id: str) -> ToolPackRecord | None: ...

    def snapshot(self) -> Mapping[str, ToolPackRecord]: ...

    def close(self) -> None: ...
