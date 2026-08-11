"""ModelProbeResult 失败结果构造助手（消息一律 redacted）。"""

from __future__ import annotations

from datetime import datetime, timezone

from packages.domain.enums import FailureCategory
from packages.domain.models import EndpointProbeSnapshot, ModelProbeResult
from packages.domain.redaction import redact_exception_message


def configuration_failure(model_id: str, message: str) -> ModelProbeResult:
    return ModelProbeResult(
        model_id=model_id,
        ok=False,
        error_category=FailureCategory.CONFIGURATION,
        error_message=redact_exception_message(message),
        probed_at=datetime.now(timezone.utc),
    )


def crash_result(model_id: str, exc: Exception) -> ModelProbeResult:
    return ModelProbeResult(
        model_id=model_id,
        ok=False,
        error_category=FailureCategory.EXECUTION_FAILURE,
        error_message=redact_exception_message(str(exc)),
        probed_at=datetime.now(timezone.utc),
    )


def connectivity_error_result(
    model_id: str,
    snapshot: EndpointProbeSnapshot,
) -> ModelProbeResult:
    return ModelProbeResult(
        model_id=model_id,
        ok=False,
        error_category=snapshot.error_category,
        error_message=snapshot.error_message_redacted,
        probed_at=datetime.now(timezone.utc),
    )
