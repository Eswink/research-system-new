"""probe 层的协议相关请求口径（EC-01）。

判据：Messages 形态把 `max_tokens` 列为必填 ⇒ probe **只对 ANTHROPIC 端点**显式给出
`PROBE_ANTHROPIC_MAX_TOKENS`；OpenAI-compatible 端点保持 `max_tokens is None`
（请求体因此不含该键，与改动前逐字节一致）。

用记录型 gateway（记录每个 `CompletionRequest`）证明，而不是读代码字面量。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from adapters.fakes import FakeCredentialResolver
from packages.application.model_relay.probe import ProbeOptions, run_probe
from packages.application.model_relay.suite import PROBE_ANTHROPIC_MAX_TOKENS, default_probe_suite
from packages.application.ports import (
    CompletionRequest,
    CompletionResult,
    ModelsListResult,
    SecretValue,
)
from packages.domain.models import EndpointProbeSnapshot, LLMEndpoint, ModelDefinition

from .relay_fixtures import ENDPOINT, MODEL


class RecordingGateway:
    """记录每次 complete / probe_endpoint 收到的请求；固定返回成功快照。"""

    def __init__(self) -> None:
        self.requests: list[CompletionRequest] = []

    def list_models(self, endpoint: LLMEndpoint, credential: SecretValue) -> ModelsListResult:
        return ModelsListResult(model_ids=("model-alpha",))

    def complete(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> CompletionResult:
        self.requests.append(request)
        return CompletionResult(
            content="pong",
            returned_model_name="model-alpha",
            system_fingerprint="fp_1",
            usage_reported=True,
        )

    def probe_endpoint(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> EndpointProbeSnapshot:
        self.requests.append(request)
        return EndpointProbeSnapshot(
            ok=True,
            returned_model_name="model-alpha",
            system_fingerprint="fp_1",
            usage_reported=True,
        )

    def probe_connectivity(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
    ) -> EndpointProbeSnapshot:
        return EndpointProbeSnapshot(ok=True)


def _anthropic_endpoint() -> LLMEndpoint:
    return replace(ENDPOINT, id="anthropic-main", protocol="ANTHROPIC")


def _run(gateway: RecordingGateway, endpoint: LLMEndpoint) -> None:
    run_probe(
        gateway=gateway,
        credential_resolver=FakeCredentialResolver({"llm_main_key": "placeholder-token"}),
        endpoint=endpoint,
        model=ModelDefinition(id="model-alpha", endpoint_id=endpoint.id, model_name="model-alpha"),
        options=ProbeOptions(suite=default_probe_suite()),
    )


def test_anthropic_probe_requests_carry_probe_max_tokens() -> None:
    gateway = RecordingGateway()
    _run(gateway, _anthropic_endpoint())
    assert gateway.requests, "probe 未发出任何请求"
    assert {request.max_tokens for request in gateway.requests} == {PROBE_ANTHROPIC_MAX_TOKENS}


def test_openai_compatible_probe_requests_carry_no_max_tokens() -> None:
    gateway = RecordingGateway()
    _run(gateway, ENDPOINT)
    assert gateway.requests, "probe 未发出任何请求"
    assert {request.max_tokens for request in gateway.requests} == {None}


def test_probe_result_shape_is_unchanged_for_openai_compatible() -> None:
    """回归：既有端点的 probe 结论不变（成功 + 记录到的能力集合）。"""
    gateway = RecordingGateway()
    result, _ = run_probe(
        gateway=gateway,
        credential_resolver=FakeCredentialResolver({"llm_main_key": "placeholder-token"}),
        endpoint=ENDPOINT,
        model=MODEL,
        options=ProbeOptions(suite=default_probe_suite()),
    )
    assert result.ok is True
    assert result.probed_at is not None
    assert result.probed_at.tzinfo == timezone.utc
    assert result.system_fingerprint == "fp_1"
    assert result.probed_at <= datetime.now(timezone.utc)
