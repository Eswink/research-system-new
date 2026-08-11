"""Model Relay 内层拥有的 Ports。

Port 由 application 拥有；adapter 实现这些接口。本层不依赖 adapter/httpx。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from packages.domain.enums import (
    CapabilitySource,
    CapabilityStatus,
    FailureCategory,
    ModelCapability,
)
from packages.domain.models import (
    CapabilityAssertion,
    EndpointProbeSnapshot,
    LLMEndpoint,
)


@dataclass(frozen=True, slots=True)
class SecretValue:
    """密封的密钥值；repr 永不输出明文。"""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("secret value must not be empty")

    def __repr__(self) -> str:
        return "<SecretValue:redacted>"


@runtime_checkable
class CredentialResolver(Protocol):
    """按 credential_ref 解析密钥；未解析抛 KeyError/ValueError。"""

    def resolve(self, credential_ref: str) -> SecretValue: ...


@runtime_checkable
class EndpointStore(Protocol):
    """LLMEndpoint 存储；CRUD 语义由实现保证。"""

    def list_endpoints(self) -> list[LLMEndpoint]: ...

    def get_endpoint(self, endpoint_id: str) -> LLMEndpoint: ...

    def save_endpoint(self, endpoint: LLMEndpoint) -> None: ...

    def delete_endpoint(self, endpoint_id: str) -> None: ...


@dataclass(frozen=True, slots=True)
class ToolCallDraft:
    id: str
    name: str
    arguments: str


@dataclass(frozen=True, slots=True)
class CompletionRequest:
    model: str
    messages: list[dict[str, object]]
    tools: list[dict[str, object]] | None = None
    response_format: dict[str, object] | None = None
    stream: bool = False


@dataclass(frozen=True, slots=True)
class CompletionResult:
    content: str | None = None
    tool_calls: tuple[ToolCallDraft, ...] = ()
    returned_model_name: str | None = None
    system_fingerprint: str | None = None
    usage_reported: bool = False
    safe_response_metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ModelsListResult:
    """GET /v1/models 的结果。"""

    model_ids: tuple[str, ...]


@runtime_checkable
class ModelRelayGateway(Protocol):
    """OpenAI-compatible 协议网关（由 adapter 实现）。"""

    def list_models(self, endpoint: LLMEndpoint, credential: SecretValue) -> ModelsListResult: ...

    def complete(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> CompletionResult: ...

    def probe_endpoint(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> EndpointProbeSnapshot: ...

    def probe_connectivity(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
    ) -> EndpointProbeSnapshot: ...


def capability_assertion_probed(
    capability: ModelCapability, probe_version: str
) -> CapabilityAssertion:
    """构建 PROBED 来源的能力断言。"""
    return CapabilityAssertion(
        status=CapabilityStatus.SUPPORTED,
        confidence=1.0,
        source=CapabilitySource.PROBED,
        last_verified_at=datetime.now(timezone.utc),
        probe_version=probe_version,
    )


def failure_category_of_http_status(status_code: int) -> FailureCategory:
    """HTTP 状态码 → FailureCategory 映射。"""
    if status_code in (401, 403):
        return FailureCategory.MODEL_AUTH
    if status_code == 429:
        return FailureCategory.MODEL_RATE_LIMIT
    if 400 <= status_code < 500:
        return FailureCategory.MODEL_INCOMPATIBLE
    return FailureCategory.MODEL_RELAY_UNAVAILABLE
