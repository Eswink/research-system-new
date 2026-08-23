"""ModelGateway Port：provider-independent 模型网关。

职责：OpenAI-compatible 协议网关的最小调用面
（complete / list_models / probe_endpoint / probe_connectivity）。
非职责：凭据解析（CredentialResolver）、预算记账（BudgetLedger）、
模型选择 / eligibility / fallback 编排（application use case）、
provider 内部实现细节（adapter）。

上游命名不进入 Domain（docs/integration/MODEL_GATEWAY.md §3）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from packages.application.ports.credential_resolver import SecretValue
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
    # M12-R1 WP6：usage 明细（provider 返回时填充；不返回则保持 None，
    # 由调用方记 UNKNOWN，不得伪造数字）
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    usage_unavailable_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ModelsListResult:
    """GET /v1/models 的结果。"""

    model_ids: tuple[str, ...]


@runtime_checkable
class ModelGateway(Protocol):
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
