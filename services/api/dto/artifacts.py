"""Artifact 控制面 DTO（WP-C：浏览/元数据/下载；无 Domain 类型泄漏）。"""

from __future__ import annotations

from pydantic import BaseModel


class ArtifactDto(BaseModel):
    id: str
    digest: str
    size_bytes: int
    media_type: str
    state: str
    created_by: str | None = None
    source_refs: list[str] = []
    classification: str | None = None
    retention_policy: str | None = None
    created_at: str | None = None
    # 内容级校验仅在单资源查询执行；列表视图恒为 None（不伪装已验证）。
    verified: bool | None = None
