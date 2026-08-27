"""LLM Endpoint DTO：Domain LLMEndpoint / probe 结果 → API DTO 显式映射。

明文 API Key 只在创建/更新入口（LlmEndpointCreateDto.api_key）出现，
任何 Read/List 响应永不包含密钥；前端只消费本模块 DTO。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CredentialState = Literal["configured", "missing"]


class DiscoveryConfigDto(BaseModel):
    enabled: bool = False
    allow_models: list[str] = Field(default_factory=list)


class LlmEndpointCreateDto(BaseModel):
    """创建端点：api_key 仅在入口接收，绝不回显。"""

    name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=1, max_length=2000)
    protocol: Literal["OPENAI_COMPATIBLE", "ANTHROPIC"] = "OPENAI_COMPATIBLE"
    api_style: Literal["chat_completions", "responses"] = "chat_completions"
    api_key: str | None = Field(default=None, min_length=1, max_length=4000)
    enabled: bool = True
    request_timeout_seconds: int = Field(default=60, ge=1, le=3600)
    max_retries: int = Field(default=3, ge=0, le=10)
    concurrency_limit: int = Field(default=4, ge=1)
    discovery: DiscoveryConfigDto | None = None


class LlmEndpointUpdateDto(BaseModel):
    """更新端点：全部可选；api_key 更新时重新注册（不返回）。"""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    base_url: str | None = Field(default=None, min_length=1, max_length=2000)
    api_style: Literal["chat_completions", "responses"] | None = None
    api_key: str | None = Field(default=None, min_length=1, max_length=4000)
    enabled: bool | None = None
    request_timeout_seconds: int | None = Field(default=None, ge=1, le=3600)
    max_retries: int | None = Field(default=None, ge=0, le=10)
    concurrency_limit: int | None = Field(default=None, ge=1)


class LlmEndpointReadDto(BaseModel):
    """读取/列表视图：无密钥，仅凭据状态。"""

    id: str
    name: str
    protocol: str
    base_url: str
    api_style: str
    enabled: bool
    credential: CredentialState
    request_timeout_seconds: int
    max_retries: int
    concurrency_limit: int
    version: str = Field(description="resource version（ETag 值，If-Match 用）")


class EndpointTestRequestDto(BaseModel):
    """端点测试：需要引用一个已配置模型（真实模型 ID 探测）。"""

    model_id: str = Field(min_length=1)


class EndpointTestResultDto(BaseModel):
    """endpoint test 结果（消息已脱敏）。"""

    ok: bool
    returned_model_name: str | None = None
    system_fingerprint: str | None = None
    error_category: str | None = None
    error_message_redacted: str | None = None
    probed_at: str | None = None


class DiscoverModelsResultDto(BaseModel):
    model_ids: list[str] = Field(default_factory=list)


class EndpointHealthDto(BaseModel):
    """实时连通性探测视图（GET /models 探测，不缓存伪造）。"""

    ok: bool
    error_category: str | None = None
    error_message_redacted: str | None = None
    checked_at: str
