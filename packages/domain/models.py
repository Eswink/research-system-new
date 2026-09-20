"""模型域实体定义。

来源：docs/architecture/MODEL_COMPATIBILITY.md、docs/integration/LLM_ENDPOINTS.md、
schemas/llm-endpoint.schema.json、schemas/model-definition.schema.json。
Domain 不写真实模型厂商；每次 Run 记录漂移证据（AGENTS.md §4）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from packages.domain.circuit_breaker import CircuitBreakerConfig
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import (
    CapabilitySource,
    CapabilityStatus,
    EndpointHealth,
    FailureCategory,
    LLMProtocol,
    ModelBindingMode,
    ModelCapability,
    ThinkingIntensity,
)

# 协议合法取值的唯一来源（域枚举 LLMProtocol）；执行侧选路必须与本集合同源。
_LEGAL_PROTOCOLS = frozenset(protocol.value for protocol in LLMProtocol)


@dataclass(frozen=True, slots=True)
class EndpointDiscoveryConfig:
    """可选 `/models` discovery 配置；默认不启用（manual ModelDefinition 是唯一强依赖）。"""

    enabled: bool = False
    allow_models: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LLMEndpoint:
    id: str
    name: str
    protocol: str
    base_url: str
    credential_ref: str
    enabled: bool = True
    request_timeout_seconds: int = 60
    max_retries: int = 3
    concurrency_limit: int = 4
    api_style: str = "chat_completions"
    discovery: EndpointDiscoveryConfig | None = None
    circuit_breaker: CircuitBreakerConfig | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("endpoint id must not be empty")
        if self.protocol not in _LEGAL_PROTOCOLS:
            raise ValueError("endpoint protocol must be OPENAI_COMPATIBLE or ANTHROPIC")
        if self.api_style not in ("chat_completions", "responses"):
            raise ValueError("api_style must be 'chat_completions' or 'responses'")
        if not self.base_url.startswith(("https://", "http://")):
            raise ValueError("base_url must be an absolute http(s) URL")
        if not self.credential_ref:
            raise ValueError("credential_ref must not be empty")
        if not 1 <= self.request_timeout_seconds <= 3600:
            raise ValueError("request_timeout_seconds must be in [1, 3600]")
        if not 0 <= self.max_retries <= 10:
            raise ValueError("max_retries must be in [0, 10]")
        if self.concurrency_limit < 1:
            raise ValueError("concurrency_limit must be >= 1")


@dataclass(frozen=True, slots=True)
class CapabilityAssertion:
    status: CapabilityStatus = CapabilityStatus.UNKNOWN
    confidence: float = 0.0
    source: CapabilitySource = CapabilitySource.USER_DECLARED
    last_verified_at: datetime | None = None
    probe_version: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if self.last_verified_at is not None:
            Timestamp(self.last_verified_at)


@dataclass(frozen=True, slots=True)
class ModelDefinition:
    id: str
    endpoint_id: str
    model_name: str
    display_name: str | None = None
    enabled: bool = True
    capabilities: dict[ModelCapability, CapabilityAssertion] = field(default_factory=dict)
    #: 声明值（由用户/运维登记，**不是探测得来**）：上下文窗口与思考强度。
    #: 本版本**不向 provider 发送**这两个值，也不参与 eligibility 判定——
    #: 读面与文档必须如实说明（docs/architecture/MODEL_COMPATIBILITY.md）。
    context_window_tokens: int | None = None
    thinking_intensity: ThinkingIntensity | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("model id must not be empty")
        if not self.endpoint_id:
            raise ValueError("model endpoint_id must not be empty")
        if not self.model_name:
            raise ValueError("model_name must not be empty")
        if self.context_window_tokens is not None and self.context_window_tokens < 1:
            raise ValueError("context_window_tokens must be >= 1 when set")


@dataclass(frozen=True, slots=True)
class ModelProfile:
    id: str
    primary: str
    fallback: list[str] = field(default_factory=list)
    hard_capabilities: list[ModelCapability] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("profile id must not be empty")
        if not self.primary:
            raise ValueError("profile must declare a primary model")


@dataclass(frozen=True, slots=True)
class ModelBinding:
    mode: ModelBindingMode
    model_id: str | None = None
    profile_id: str | None = None

    def __post_init__(self) -> None:
        if self.mode is ModelBindingMode.INHERIT:
            if self.model_id is not None or self.profile_id is not None:
                raise ValueError("INHERIT binding must not reference a model or profile")
            return
        if self.mode is ModelBindingMode.EXPLICIT_MODEL:
            if self.model_id is None:
                raise ValueError("EXPLICIT_MODEL binding requires model_id")
        elif self.profile_id is None:
            raise ValueError("MODEL_PROFILE binding requires profile_id")


@dataclass(frozen=True, slots=True)
class ModelRuntimeFingerprint:
    endpoint_config_digest: Digest
    requested_model_id: str
    returned_model_identifier: str | None = None
    system_fingerprint: str | None = None
    selected_response_metadata: dict[str, str] = field(default_factory=dict)
    probe_suite_digest: Digest | None = None
    calibration_prompt_version: str | None = None
    calibration_result_digest: Digest | None = None
    observed_capabilities: frozenset[ModelCapability] = frozenset()
    captured_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.requested_model_id:
            raise ValueError("requested_model_id must not be empty")
        if self.captured_at is not None:
            Timestamp(self.captured_at)


@dataclass(frozen=True, slots=True)
class CapabilityProbeFailure:
    """单项能力 probe 失败（区分“模型不支持”与网络/认证/限流等运行失败）。"""

    capability: ModelCapability
    error_category: FailureCategory
    error_message_redacted: str | None = None
    probed_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.probed_at is not None:
            Timestamp(self.probed_at)


@dataclass(frozen=True, slots=True)
class ModelProbeResult:
    model_id: str
    ok: bool
    observed_capabilities: frozenset[ModelCapability] = frozenset()
    returned_model_name: str | None = None
    system_fingerprint: str | None = None
    error_category: FailureCategory | None = None
    error_message: str | None = None
    capability_failures: tuple[CapabilityProbeFailure, ...] = field(default_factory=tuple)
    probed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("model_id must not be empty")
        if self.probed_at is not None:
            Timestamp(self.probed_at)


@dataclass(frozen=True, slots=True)
class ProbeSuiteSpec:
    """Probe suite 定义（步骤 + 固定消息 + structured schema）。

    `probe_suite_digest` 用 canonical serialization 对定义计算（见
    docs/integration/MODEL_PROBE.md）。
    """

    version: str
    steps: tuple[str, ...]
    fixture_message: str
    structured_schema: dict[str, object]
    include_vision: bool = False

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("probe suite version must not be empty")
        if not self.steps:
            raise ValueError("probe suite must declare at least one step")
        if not self.fixture_message:
            raise ValueError("fixture_message must not be empty")
        if not self.structured_schema:
            raise ValueError("structured_schema must not be empty")


@dataclass(frozen=True, slots=True)
class FallbackAuditRecord:
    """Fallback 审计记录（对应 schemas/fallback-audit-record.schema.json）。"""

    from_model: str
    to_model: str
    reason: str
    occurred_at: datetime
    task_ref: str | None = None
    manifest_policy: str | None = None
    session_switched: bool = False

    def __post_init__(self) -> None:
        if not self.from_model:
            raise ValueError("from_model must not be empty")
        if not self.to_model:
            raise ValueError("to_model must not be empty")
        if not self.reason:
            raise ValueError("reason must not be empty")
        Timestamp(self.occurred_at)


@dataclass(frozen=True, slots=True)
class EndpointProbeSnapshot:
    """单次 endpoint 探测快照（HTTP 层观察结果）。"""

    ok: bool
    returned_model_name: str | None = None
    system_fingerprint: str | None = None
    safe_response_metadata: dict[str, str] = field(default_factory=dict)
    usage_reported: bool = False
    error_category: FailureCategory | None = None
    error_message_redacted: str | None = None


@dataclass(frozen=True, slots=True)
class EndpointHealthRecord:
    """Endpoint 健康记录（对应 schemas/endpoint-health.schema.json）。"""

    endpoint_id: str
    state: EndpointHealth
    recorded_at: datetime
    circuit_state: str | None = None
    consecutive_failures: int = 0
    last_error_category: FailureCategory | None = None
    opened_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.endpoint_id:
            raise ValueError("endpoint_id must not be empty")
        Timestamp(self.recorded_at)
