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
    # GOAL-20261101-103 EC-02：**改稿链的父指针**读面（域 `Artifact.supersedes` 自
    # GOAL-20261031-102 EC-01 起就有，而读面此前不披露 ⇒ 改稿链在 API 上退化成两个
    # 互不相干的制品）。`None` = 这份制品不是任何制品的下一版（既有全部制品都是这一形态）。
    supersedes: str | None = None


class ArtifactDiffLineDto(BaseModel):
    kind: str
    text: str


class ArtifactDiffStatsDto(BaseModel):
    added: int
    removed: int
    context: int


class ArtifactDiffDto(BaseModel):
    """两制品内容 diff（PLAN-047）：available=False 时 reason 必须在场且 lines 为空。"""

    left_digest: str
    right_digest: str
    comparison: str = "ARTIFACT_CONTENT"
    available: bool
    identical: bool
    reason: str | None = None
    lines: list[ArtifactDiffLineDto] = []
    stats: ArtifactDiffStatsDto
    truncated: bool = False
    note: str = (
        "comparison is artifact content vs artifact content; workspace snapshot file-level "
        "diff is a separate surface (GET /workspace-snapshots/{left}/diff/{right})"
    )
