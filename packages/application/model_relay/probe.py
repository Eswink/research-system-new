"""Model Relay probe use cases。

编排 gateway 与 domain 值对象；所有错误在 use case 内转换为
机器可读 ModelProbeResult（错误消息 redacted）。

能力探测语义（docs/integration/MODEL_PROBE.md）：
- connectivity/auth 通过 GET /models（probe_connectivity）验证；
- 单项能力失败记录 CapabilityProbeFailure（携带 FailureCategory），
  “模型不支持”与“网络/认证/限流/超时/中转站故障”可区分；
- 运行类失败（429/5xx/timeout/网络）不写入能力断言，避免把
  瞬时故障误判为永久能力变化。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from packages.application.model_relay.endpoint_policy import (
    EndpointUrlPolicy,
    validate_endpoint_url,
)
from packages.application.model_relay.ports import (
    CredentialResolver,
    ModelRelayGateway,
    SecretValue,
    capability_assertion_probed,
)
from packages.application.model_relay.results import (
    configuration_failure,
    connectivity_error_result,
    crash_result,
)
from packages.application.model_relay.suite import (
    basic_request,
    default_probe_suite,
    extended_capability_steps,
)
from packages.domain.enums import FailureCategory, ModelCapability
from packages.domain.models import (
    CapabilityAssertion,
    CapabilityProbeFailure,
    EndpointProbeSnapshot,
    LLMEndpoint,
    ModelDefinition,
    ModelProbeResult,
    ProbeSuiteSpec,
)

_ProbeCollect = tuple[EndpointProbeSnapshot, set[ModelCapability], list[CapabilityProbeFailure]]


@dataclass(frozen=True, slots=True)
class ProbeOptions:
    """run_probe 可选参数对象（控制函数签名 <= 5）。"""

    suite: ProbeSuiteSpec | None = None
    url_policy: EndpointUrlPolicy | None = None


def _resolve_credential(
    credential_resolver: CredentialResolver,
    endpoint: LLMEndpoint,
) -> SecretValue:
    try:
        return credential_resolver.resolve(endpoint.credential_ref)
    except (KeyError, ValueError) as exc:
        raise ValueError(f"credential resolution failed: {exc}") from exc


def _connectivity_gate(
    gateway: ModelRelayGateway,
    credential: SecretValue,
    endpoint: LLMEndpoint,
) -> EndpointProbeSnapshot | None:
    connectivity = gateway.probe_connectivity(endpoint, credential)
    return connectivity if not connectivity.ok else None


def _connectivity_and_chat(
    gateway: ModelRelayGateway,
    credential: SecretValue,
    endpoint: LLMEndpoint,
    model_name: str,
) -> ModelProbeResult:
    gate = _connectivity_gate(gateway, credential, endpoint)
    if gate is not None:
        return connectivity_error_result(model_name, gate)
    snapshot = gateway.probe_endpoint(
        endpoint,
        credential,
        basic_request(model_name, with_tools=False, with_structured=False, stream=False),
    )
    if not snapshot.ok:
        return connectivity_error_result(model_name, snapshot)
    return ModelProbeResult(
        model_id=model_name,
        ok=True,
        returned_model_name=snapshot.returned_model_name,
        system_fingerprint=snapshot.system_fingerprint,
        probed_at=datetime.now(timezone.utc),
    )


def run_endpoint_test(
    *,
    gateway: ModelRelayGateway,
    credential_resolver: CredentialResolver,
    endpoint: LLMEndpoint,
    model_name: str,
    url_policy: EndpointUrlPolicy | None = None,
) -> ModelProbeResult:
    """endpoint test：connectivity/auth + basic chat 探测，返回机器可读结果。

    URL 策略默认拒绝 localhost/private/link-local（LLM_ENDPOINTS.md §3），
    部署策略可通过 url_policy 显式放行。
    """
    effective_policy = url_policy if url_policy is not None else EndpointUrlPolicy()
    try:
        validate_endpoint_url(endpoint.base_url, effective_policy)
    except ValueError as exc:
        return configuration_failure(model_name, str(exc))
    try:
        credential = _resolve_credential(credential_resolver, endpoint)
        return _connectivity_and_chat(gateway, credential, endpoint, model_name)
    except ValueError as exc:
        return configuration_failure(model_name, str(exc))
    except Exception as exc:  # noqa: BLE001
        return crash_result(model_name, exc)


def _chat_abort(
    model: ModelDefinition,
    chat: EndpointProbeSnapshot,
) -> ModelProbeResult:
    return ModelProbeResult(
        model_id=model.id,
        ok=False,
        error_category=chat.error_category,
        error_message=chat.error_message_redacted,
        capability_failures=(_capability_failure(ModelCapability.CHAT, chat),),
        probed_at=datetime.now(timezone.utc),
    )


def _capability_failure(
    capability: ModelCapability,
    snapshot: EndpointProbeSnapshot,
) -> CapabilityProbeFailure:
    return CapabilityProbeFailure(
        capability=capability,
        error_category=snapshot.error_category or FailureCategory.EXECUTION_FAILURE,
        error_message_redacted=snapshot.error_message_redacted,
        probed_at=datetime.now(timezone.utc),
    )


def _extended_steps(
    gateway: ModelRelayGateway,
    endpoint: LLMEndpoint,
    credential: SecretValue,
    model_name: str,
) -> tuple[set[ModelCapability], list[CapabilityProbeFailure]]:
    observed: set[ModelCapability] = set()
    failures: list[CapabilityProbeFailure] = []
    for capability, request in extended_capability_steps(model_name):
        snapshot = gateway.probe_endpoint(endpoint, credential, request)
        if snapshot.ok:
            observed.add(capability)
        else:
            failures.append(_capability_failure(capability, snapshot))
    return observed, failures


def _probe_outcome(
    model: ModelDefinition,
    chat: EndpointProbeSnapshot,
    observed: set[ModelCapability],
    failures: list[CapabilityProbeFailure],
) -> ModelProbeResult:
    return ModelProbeResult(
        model_id=model.id,
        ok=True,
        observed_capabilities=frozenset(observed),
        returned_model_name=chat.returned_model_name,
        system_fingerprint=chat.system_fingerprint,
        capability_failures=tuple(failures),
        probed_at=datetime.now(timezone.utc),
    )


def _assertions_for(
    observed: set[ModelCapability],
    probe_version: str,
) -> dict[ModelCapability, CapabilityAssertion]:
    return {
        capability: capability_assertion_probed(capability, probe_version)
        for capability in observed
    }


def _collect_probe(
    gateway: ModelRelayGateway,
    credential_resolver: CredentialResolver,
    endpoint: LLMEndpoint,
    model: ModelDefinition,
) -> ModelProbeResult | _ProbeCollect:
    credential = _resolve_credential(credential_resolver, endpoint)
    gate = _connectivity_gate(gateway, credential, endpoint)
    if gate is not None:
        return connectivity_error_result(model.id, gate)
    chat = gateway.probe_endpoint(
        endpoint,
        credential,
        basic_request(model.model_name, with_tools=False, with_structured=False, stream=False),
    )
    if not chat.ok:
        return _chat_abort(model, chat)
    observed, failures = _extended_steps(gateway, endpoint, credential, model.model_name)
    if chat.usage_reported:
        observed.add(ModelCapability.USAGE_REPORTING)
    if chat.system_fingerprint:
        observed.add(ModelCapability.SYSTEM_FINGERPRINT)
    observed.add(ModelCapability.CHAT)
    return chat, observed, failures


def run_probe(
    *,
    gateway: ModelRelayGateway,
    credential_resolver: CredentialResolver,
    endpoint: LLMEndpoint,
    model: ModelDefinition,
    options: ProbeOptions | None = None,
) -> tuple[ModelProbeResult, dict[ModelCapability, CapabilityAssertion]]:
    """执行能力 probe，输出结果与 PROBED 断言。

    连接/认证/chat 失败视为硬失败并中止；streaming / tool calling /
    structured output 失败非致命，记录 capability_failures。
    """
    suite = (options.suite if options is not None else None) or default_probe_suite()
    effective_policy = options.url_policy if options is not None else None
    if effective_policy is None:
        effective_policy = EndpointUrlPolicy()
    try:
        validate_endpoint_url(endpoint.base_url, effective_policy)
    except ValueError as exc:
        return configuration_failure(model.id, str(exc)), {}
    try:
        collected = _collect_probe(gateway, credential_resolver, endpoint, model)
    except ValueError as exc:
        return configuration_failure(model.id, str(exc)), {}
    except Exception as exc:  # noqa: BLE001
        return crash_result(model.id, exc), {}
    if isinstance(collected, ModelProbeResult):
        return collected, {}
    chat, observed, failures = collected
    return (
        _probe_outcome(model, chat, observed, failures),
        _assertions_for(observed, suite.version),
    )
