"""ToolPack 写面 DTO（GOAL-003 / EC-02）。

请求体只声明"manifest 文档 + 说明"：manifest 的形状由域（`manifest_from_document`）
唯一定义，控制面不复制第二份 schema——形状错误统一 422，错误信息来自域的校验器。
响应体把**生效版本**与**待批准更新**分开呈现（`pending`），避免把"已提交"读成"已生效"。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolPackSubmitDto(BaseModel):
    """install / update 请求：manifest 文档（含内容与 digest）。"""

    manifest: dict[str, Any] = Field(
        description="ToolPack manifest 文档；服务端重算内容 digest 并要求与 digest 字段相等"
    )
    note: str = Field(default="", max_length=280, description="审批说明（可选，随事件留痕）")


class ToolPackRevokeDto(BaseModel):
    reason: str = Field(min_length=1, max_length=280)


class ToolPackPermissionDiffDto(BaseModel):
    added_capabilities: list[str] = Field(default_factory=list)
    added_network_domains: list[str] = Field(default_factory=list)
    added_credentials: list[str] = Field(default_factory=list)


class ToolPackPendingDto(BaseModel):
    """待批准的更新：未生效，只有 approve-update 之后才成为生效版本。"""

    digest: str
    version: str
    capabilities: list[str] = Field(default_factory=list)
    diff: ToolPackPermissionDiffDto
    note: str = ""


class ToolPackDto(BaseModel):
    id: str
    state: str
    digest: str = Field(description="当前生效版本的 manifest digest（pin 与内容自洽）")
    version: str
    source: str
    resolved_revision: str
    license: str
    capabilities: list[str] = Field(default_factory=list)
    network_domains: list[str] = Field(default_factory=list)
    credential_names: list[str] = Field(default_factory=list)
    tool_ids: list[str] = Field(default_factory=list)
    installed_at: str | None = None
    revoked_reason: str | None = None
    pending: ToolPackPendingDto | None = None
    catalog_digest_active: bool = Field(
        default=False, description="该 pack 的 digest 是否已进入目录（供 preflight 供应链检查消费）"
    )


class ToolPackListDto(BaseModel):
    packs: list[ToolPackDto] = Field(default_factory=list)
    note: str
    unavailable_reason: str | None = None


class ToolPackSubmitResultDto(BaseModel):
    """install 的结果：installed / updated / pending_approval / unchanged。"""

    status: str
    pack: ToolPackDto
    diff: ToolPackPermissionDiffDto | None = None
    note: str
