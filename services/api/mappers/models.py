"""Control Plane API 映射层：Model Domain → DTO 显式转换。"""

from __future__ import annotations

from packages.domain.models import (
    CapabilityAssertion,
    CapabilityProbeFailure,
    ModelDefinition,
    ModelRuntimeFingerprint,
)
from packages.domain.serialization import digest_of
from services.api.dto.models import (
    CapabilityAssertionDto,
    CapabilityFailureDto,
    ModelReadDto,
    ModelRuntimeFingerprintDto,
)


def model_version(model: ModelDefinition) -> str:
    """模型资源版本：确定性 canonical dict（float confidence 转字符串）。"""
    canonical: dict[str, object] = {
        "id": model.id,
        "endpoint_id": model.endpoint_id,
        "model_name": model.model_name,
        "display_name": model.display_name,
        "enabled": model.enabled,
        "capabilities": {
            capability.value: {
                "status": assertion.status.value,
                "source": assertion.source.value,
                "probe_version": assertion.probe_version,
                "confidence": f"{assertion.confidence:.6f}",
            }
            for capability, assertion in model.capabilities.items()
        },
    }
    return str(digest_of(canonical))


def assertion_dto(assertion: CapabilityAssertion) -> CapabilityAssertionDto:
    return CapabilityAssertionDto(
        status=assertion.status.value,
        confidence=assertion.confidence,
        source=assertion.source.value,
        probe_version=assertion.probe_version,
    )


def model_read_dto(model: ModelDefinition) -> ModelReadDto:
    return ModelReadDto(
        id=model.id,
        endpoint_id=model.endpoint_id,
        model_name=model.model_name,
        display_name=model.display_name,
        enabled=model.enabled,
        capabilities={
            capability.value: assertion_dto(assertion)
            for capability, assertion in model.capabilities.items()
        },
        version=model_version(model),
    )


def capability_failures_dto(
    failures: tuple[CapabilityProbeFailure, ...],
) -> list[CapabilityFailureDto]:
    return [
        CapabilityFailureDto(
            capability=failure.capability.value,
            error_category=failure.error_category.value,
            error_message_redacted=failure.error_message_redacted,
        )
        for failure in failures
    ]


def fingerprint_dto(fingerprint: ModelRuntimeFingerprint) -> ModelRuntimeFingerprintDto:
    return ModelRuntimeFingerprintDto(
        endpoint_config_digest=str(fingerprint.endpoint_config_digest),
        probe_suite_digest=str(fingerprint.probe_suite_digest or ""),
        returned_model_identifier=fingerprint.returned_model_identifier,
        system_fingerprint=fingerprint.system_fingerprint,
        observed_capabilities=sorted(item.value for item in fingerprint.observed_capabilities),
    )
