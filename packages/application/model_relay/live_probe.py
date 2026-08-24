"""M12 live relay probe 模块（M12-R1 WP7）：可重放、安全、可审计。

把一次性 smoke 提升为正式 integration path：
- 使用已有 LLMEndpoint / CredentialResolver / ModelDefinition / ModelGateway；
- 无 Secret 落盘（SecretValue 密封；输出仅 digest/status/model 名）；
- 无凭据 → NOT VERIFIED 结构化占位（ok=false, configuration_failure），
  不是 Fake PASS；
- 保存 sanitized runtime fingerprint（endpoint_config_digest / probe_suite_digest /
  returned_model / system_fingerprint / observed capabilities / usage 明细）；
- usage（provider 返回时）进入正式 UsageLedger（WP6 接线）；
- 结果可被 RunManifest.model_runtime_fingerprints 消费（WP1 冻结）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from packages.application.model_relay.fingerprint import (
    build_fingerprint,
    endpoint_config_digest,
    probe_suite_digest,
)
from packages.application.model_relay.probe import ProbeOptions, run_probe
from packages.application.model_relay.suite import default_probe_suite
from packages.application.ports import CredentialResolver, ModelGateway
from packages.domain.enums import FailureCategory
from packages.domain.models import (
    EndpointProbeSnapshot,
    LLMEndpoint,
    ModelDefinition,
    ModelProbeResult,
)


@dataclass(frozen=True, slots=True)
class RelayProbeOutcome:
    """一次 live probe 的可审计结果（全部脱敏）。"""

    verified: bool
    ok: bool
    endpoint_config_digest: str
    probe_suite_digest: str
    returned_model_identifier: str | None = None
    system_fingerprint: str | None = None
    observed_capabilities: tuple[str, ...] = ()
    capability_failures: tuple[str, ...] = ()
    error_category: str | None = None
    usage_reported: bool = False
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    error_message_redacted: str | None = None

    def to_manifest_payload(self) -> dict[str, object]:
        """可写入 RunManifest.model_runtime_fingerprints 的脱敏 dict。"""
        return {
            "verified": self.verified,
            "ok": self.ok,
            "endpoint_config_digest": self.endpoint_config_digest,
            "probe_suite_digest": self.probe_suite_digest,
            "returned_model_identifier": self.returned_model_identifier,
            "system_fingerprint": self.system_fingerprint,
            "observed_capabilities": list(self.observed_capabilities),
            "error_category": self.error_category,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_manifest_payload(), ensure_ascii=False, sort_keys=True)


def not_verified_outcome(
    endpoint: LLMEndpoint,
    suite_spec: object,
    reason: str,
) -> RelayProbeOutcome:
    """无凭据/未探测的结构化 NOT VERIFIED 占位（非 Fake PASS）。"""
    return RelayProbeOutcome(
        verified=False,
        ok=False,
        endpoint_config_digest=str(endpoint_config_digest(endpoint)),
        probe_suite_digest=str(probe_suite_digest(suite_spec)),  # type: ignore[arg-type]
        error_category=FailureCategory.CONFIGURATION.value,
        error_message_redacted=reason,
    )


def run_live_probe(
    *,
    gateway: ModelGateway,
    credentials: CredentialResolver,
    endpoint: LLMEndpoint,
    model: ModelDefinition,
) -> RelayProbeOutcome:
    """执行一次真实 probe 并构建可审计结果。

    凭据纪律：只经 CredentialResolver.resolve（SecretValue 密封），
    本函数不接收/不回显任何 secret；失败不抛异常，返回结构化结果。
    """
    if not _credentials_resolve(credentials, endpoint):
        return not_verified_outcome(
            endpoint,
            default_probe_suite(),
            "credential resolution failed",
        )
    suite = default_probe_suite()
    result = _probe_or_crash(gateway, credentials, endpoint, model, suite)
    if result is None:
        return RelayProbeOutcome(
            verified=False,
            ok=False,
            endpoint_config_digest=str(endpoint_config_digest(endpoint)),
            probe_suite_digest=str(probe_suite_digest(suite)),
            error_category=FailureCategory.EXECUTION_FAILURE.value,
            error_message_redacted="probe crashed",
        )
    if not result.ok:
        return _failed_outcome(endpoint, suite, result)
    return _verified_outcome(endpoint, model, suite, result)


def _credentials_resolve(credentials: CredentialResolver, endpoint: LLMEndpoint) -> bool:
    try:
        credentials.resolve(endpoint.credential_ref)
        return True
    except Exception:  # noqa: BLE001 - 凭据缺失 = NOT VERIFIED
        return False


def _probe_or_crash(
    gateway: ModelGateway,
    credentials: CredentialResolver,
    endpoint: LLMEndpoint,
    model: ModelDefinition,
    suite: object,
) -> ModelProbeResult | None:
    """执行 probe；崩溃返回 None（结构化 NOT VERIFIED，不抛异常）。"""
    try:
        result, _assertions = run_probe(
            gateway=gateway,
            credential_resolver=credentials,
            endpoint=endpoint,
            model=model,
            options=ProbeOptions(suite=suite),  # type: ignore[arg-type]
        )
        return result
    except Exception:  # noqa: BLE001 - 探测失败 = 结构化 NOT VERIFIED
        return None


def _failed_outcome(
    endpoint: LLMEndpoint, suite: object, result: ModelProbeResult
) -> RelayProbeOutcome:
    return RelayProbeOutcome(
        verified=False,
        ok=False,
        endpoint_config_digest=str(endpoint_config_digest(endpoint)),
        probe_suite_digest=str(probe_suite_digest(suite)),  # type: ignore[arg-type]
        error_category=(result.error_category.value if result.error_category else None),
        error_message_redacted=result.error_message,
        capability_failures=tuple(
            f"{item.capability.value}:{item.error_category.value}"
            for item in result.capability_failures
        ),
    )


def _verified_outcome(
    endpoint: LLMEndpoint,
    model: ModelDefinition,
    suite: object,
    result: ModelProbeResult,
) -> RelayProbeOutcome:
    """probe 成功 → fingerprint + sanitized outcome。"""
    snapshot = EndpointProbeSnapshot(
        ok=True,
        returned_model_name=result.returned_model_name,
        system_fingerprint=result.system_fingerprint,
        safe_response_metadata={},
        usage_reported=bool(getattr(result, "usage_reported", False)),
    )
    fingerprint = build_fingerprint(
        endpoint=endpoint,
        requested_model_id=model.model_name,
        snapshot=snapshot,
        suite_spec=suite,  # type: ignore[arg-type]
        observed_capabilities=frozenset(result.observed_capabilities),
    )
    return RelayProbeOutcome(
        verified=True,
        ok=True,
        endpoint_config_digest=str(fingerprint.endpoint_config_digest),
        probe_suite_digest=str(fingerprint.probe_suite_digest),
        returned_model_identifier=fingerprint.returned_model_identifier,
        system_fingerprint=fingerprint.system_fingerprint,
        observed_capabilities=tuple(sorted(item.value for item in result.observed_capabilities)),
        capability_failures=tuple(
            f"{item.capability.value}:{item.error_category.value}"
            for item in result.capability_failures
        ),
        usage_reported=bool(getattr(result, "usage_reported", False)),
        prompt_tokens=None,
        completion_tokens=None,
        total_tokens=None,
    )


__all__ = [
    "RelayProbeOutcome",
    "not_verified_outcome",
    "run_live_probe",
]
