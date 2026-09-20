"""Model DTO：Domain ModelDefinition / probe / fingerprint → API DTO 显式映射。

capabilities 以稳定枚举字符串表达（ModelCapability/CapabilityStatus/
CapabilitySource），前端不接触 Python Domain 类型。
声明参数（context_window_tokens / thinking_intensity）同样是**字符串/整数表达**，
取值与域枚举 `ThinkingIntensity` 的一致性由结构判据钉住
（`tests/architecture/python/test_protocol_vocabulary.py`）。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

#: 与域枚举 `ThinkingIntensity` 同值（结构判据保证不漂移）。
ThinkingIntensityLiteral = Literal["MINIMAL", "LOW", "MEDIUM", "HIGH", "MAX"]


class CapabilityAssertionDto(BaseModel):
    status: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: str
    probe_version: str | None = None


class CapabilityFailureDto(BaseModel):
    capability: str
    error_category: str | None = None
    error_message_redacted: str | None = None


class ModelRuntimeFingerprintDto(BaseModel):
    """AGENTS.md §4 漂移可见性字段（全部脱敏，无 secret）。"""

    endpoint_config_digest: str
    probe_suite_digest: str | None = None
    returned_model_identifier: str | None = None
    system_fingerprint: str | None = None
    observed_capabilities: list[str] = Field(default_factory=list)


class ModelCreateDto(BaseModel):
    endpoint_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1, max_length=500)
    display_name: str | None = Field(default=None, max_length=500)
    enabled: bool = True
    capabilities: dict[str, CapabilityAssertionDto] = Field(default_factory=dict)
    # 声明参数（EC-02）：声明值，本版本不发送给 provider，也不参与 eligibility 判定。
    context_window_tokens: int | None = Field(default=None, ge=1)
    thinking_intensity: ThinkingIntensityLiteral | None = None


class ModelUpdateDto(BaseModel):
    """更新模型：全部可选；capabilities 整体替换（含 PROBED 断言）。"""

    display_name: str | None = Field(default=None, max_length=500)
    enabled: bool | None = None
    capabilities: dict[str, CapabilityAssertionDto] | None = None
    context_window_tokens: int | None = Field(default=None, ge=1)
    thinking_intensity: ThinkingIntensityLiteral | None = None


class ModelReadDto(BaseModel):
    id: str
    endpoint_id: str
    model_name: str
    display_name: str | None
    enabled: bool
    capabilities: dict[str, CapabilityAssertionDto]
    context_window_tokens: int | None
    thinking_intensity: ThinkingIntensityLiteral | None
    version: str = Field(description="resource version（ETag 值，If-Match 用）")


class ProbeResultDto(BaseModel):
    """capability probe 结果：system_fingerprint=None 时前端必须渲染
    'configuration reproducible / provider fingerprint unavailable'，
    禁止美化为一律 fully reproducible。"""

    model_id: str
    ok: bool
    observed_capabilities: list[str] = Field(default_factory=list)
    returned_model_name: str | None = None
    system_fingerprint: str | None = None
    provider_fingerprint_available: bool
    error_category: str | None = None
    error_message_redacted: str | None = None
    capability_failures: list[CapabilityFailureDto] = Field(default_factory=list)
    probed_at: str | None = None
    fingerprint: ModelRuntimeFingerprintDto | None = None


class CompatibilityViewDto(BaseModel):
    """模型兼容性视图：声明能力 + endpoint 摘要（不含未探测的推断）。"""

    model: ModelReadDto
    endpoint_id: str
    endpoint_healthy_hint: bool | None = None
    hard_capability_requirements: list[str] = Field(default_factory=list)
