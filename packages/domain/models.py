"""模型域实体定义。

来源：docs/architecture/MODEL_COMPATIBILITY.md、docs/integration/LLM_ENDPOINTS.md、
schemas/llm-endpoint.schema.json、schemas/model-definition.schema.json。
Domain 不写真实模型厂商；每次 Run 记录漂移证据（AGENTS.md §4）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from packages.domain.core import Digest, Timestamp
from packages.domain.enums import (
    CapabilitySource,
    CapabilityStatus,
    ModelBindingMode,
    ModelCapability,
)


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

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("endpoint id must not be empty")
        if self.protocol != "OPENAI_COMPATIBLE":
            raise ValueError("endpoint protocol must be OPENAI_COMPATIBLE")
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

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("model id must not be empty")
        if not self.endpoint_id:
            raise ValueError("model endpoint_id must not be empty")
        if not self.model_name:
            raise ValueError("model_name must not be empty")


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
class ModelProbeResult:
    model_id: str
    ok: bool
    observed_capabilities: frozenset[ModelCapability] = frozenset()
    returned_model_name: str | None = None
    system_fingerprint: str | None = None
    error_category: str | None = None
    probed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("model_id must not be empty")
        if self.probed_at is not None:
            Timestamp(self.probed_at)
