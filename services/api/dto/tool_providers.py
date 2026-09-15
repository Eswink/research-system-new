"""Tool Provider 只读视图 DTO（PLAN-043 WP-A，EC-02）。

PLAN-060（EC-05）在同模块内补注册面 DTO：注册/更新/批准/吊销/健康复核是
供应链治理写面，读面（`GET /tool-providers`）与注册面（`/tool-provider-registrations`）
显式分离——注册过但未批准（PENDING）的 provider 不出现在目录里。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ToolProviderDto(BaseModel):
    id: str
    kind: str
    trust_level: str
    effect_class: str
    capabilities: list[str] = Field(default_factory=list)
    transport: str | None = None
    protocol_version: str | None = None
    network_domains: list[str] = Field(default_factory=list)
    health_check: bool = False
    health: str = "UNKNOWN"


class ToolProviderListDto(BaseModel):
    providers: list[ToolProviderDto] = Field(default_factory=list)
    management_available: bool = False
    management_reason: str | None = None


class ToolProviderRegisterDto(BaseModel):
    """注册请求：pin 必填且必须是 `sha256:<hex>`（不接受可漂移的 tag/分支名）。"""

    id: str = Field(min_length=1, max_length=128)
    kind: str
    capabilities: list[str] = Field(min_length=1)
    pinned_revision: str = Field(min_length=1, max_length=128)
    effect_class: str = "READ_ONLY"
    transport: str | None = None
    protocol_version: str | None = None
    network_domains: list[str] = Field(default_factory=list)
    health_check: bool = False


class ToolProviderUpdateDto(BaseModel):
    """更新可变字段；`id`/`kind`/`state` 不在其中（kind 变更须新注册）。"""

    capabilities: list[str] | None = None
    pinned_revision: str | None = None
    effect_class: str | None = None
    transport: str | None = None
    protocol_version: str | None = None
    network_domains: list[str] | None = None
    health_check: bool | None = None


class ToolProviderRevokeDto(BaseModel):
    reason: str = Field(min_length=1, max_length=1024)


class ToolProviderHealthDto(BaseModel):
    status: str
    detail: str = ""


class ToolProviderRegistrationDto(BaseModel):
    """一次注册的完整事实（含最近一次健康探测与是否已进入目录）。"""

    id: str
    kind: str
    state: str
    trust_level: str
    capabilities: list[str] = Field(default_factory=list)
    effect_class: str
    pinned_revision: str
    transport: str | None = None
    protocol_version: str | None = None
    network_domains: list[str] = Field(default_factory=list)
    health_check: bool = False
    registered_at: str | None = None
    updated_at: str | None = None
    approved_at: str | None = None
    revoked_at: str | None = None
    revoked_reason: str | None = None
    last_health: str | None = None
    health_detail: str | None = None
    health_checked_at: str | None = None
    catalog_active: bool = False


class ToolProviderRegistrationListDto(BaseModel):
    registrations: list[ToolProviderRegistrationDto] = Field(default_factory=list)
    management_available: bool = False
    management_reason: str | None = None
    note: str = ""
