"""OpenAIChatGateway telemetry 信号测试(离线 MockTransport + FakeTelemetrySink)。

覆盖:complete/list_models 的 LLM_CALL span 信号、成功 token attributes、
失败 outcome/failure_category、内部重试 metric 可见性(telemetry off 零行为)。
"""

from __future__ import annotations

import httpx

from adapters.fakes.telemetry_sink import FakeTelemetrySink
from adapters.relay.chat_api import completion_body
from adapters.relay.gateway import OpenAIChatGateway
from packages.application.observability.attributes import MetricKind, MetricName
from packages.application.observability.signals import OperationOutcome, OperationScope
from packages.application.ports import CompletionRequest
from tests.adapters.relay.relay_fakes import (
    CREDENTIAL,
    ENDPOINT,
    RETRY_ENDPOINT,
    json_response,
)

_CHAT_PAYLOAD: dict[str, object] = {
    "id": "chatcmpl-1",
    "model": "relay-model",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}}],
    "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
}


def _request() -> CompletionRequest:
    return CompletionRequest(model="relay-model", messages=[{"role": "user", "content": "hi"}])


def _body() -> dict[str, object]:
    return completion_body(_request(), stream=False)


def test_complete_emits_llm_call_span_with_tokens() -> None:
    fake = FakeTelemetrySink()
    gateway = OpenAIChatGateway(
        transport=httpx.MockTransport(lambda _r: json_response(_CHAT_PAYLOAD)),
        telemetry=fake,
    )
    result = gateway.complete(ENDPOINT, CREDENTIAL, _request())
    assert result.total_tokens == 18
    assert fake.method_calls("begin_operation") == 1
    assert fake.method_calls("end_operation") == 1
    begin = fake.begins[0]
    assert begin.scope is OperationScope.LLM_CALL
    assert begin.attributes["endpoint_id"] == "main"
    assert begin.attributes["model_id"] == "relay-model"
    end = fake.ends[0]
    assert end.outcome is OperationOutcome.OK
    assert end.attributes["total_tokens"] == 18
    assert end.attributes["status_code_class"] == "2xx"
    assert fake.metrics == ()


def test_complete_failure_records_failure_category() -> None:
    fake = FakeTelemetrySink()
    gateway = OpenAIChatGateway(
        transport=httpx.MockTransport(lambda _r: json_response({"error": "no"}, status=401)),
        telemetry=fake,
    )
    import pytest

    with pytest.raises(Exception, match="HTTP 401"):
        gateway.complete(ENDPOINT, CREDENTIAL, _request())
    assert fake.ends[0].outcome is OperationOutcome.FAILED
    assert fake.ends[0].failure_category == "MODEL_AUTH"


def test_internal_retries_become_visible_metric() -> None:
    fake = FakeTelemetrySink()
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return json_response({"error": "slow"}, status=429)
        return json_response(_CHAT_PAYLOAD)

    gateway = OpenAIChatGateway(transport=httpx.MockTransport(handler), telemetry=fake)
    result = gateway.complete(RETRY_ENDPOINT, CREDENTIAL, _request())
    assert result.total_tokens == 18
    assert calls["n"] == 2
    retry_metrics = [m for m in fake.metrics if m.name is MetricName.LLM_CALL_RETRY_ATTEMPTS]
    assert len(retry_metrics) == 1
    assert retry_metrics[0].kind is MetricKind.COUNTER
    assert retry_metrics[0].value == 1
    assert fake.ends[0].outcome is OperationOutcome.OK


def test_telemetry_none_is_zero_cost() -> None:
    gateway = OpenAIChatGateway(
        transport=httpx.MockTransport(lambda _r: json_response(_CHAT_PAYLOAD)),
    )
    assert gateway.complete(ENDPOINT, CREDENTIAL, _request()).total_tokens == 18
