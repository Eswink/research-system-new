"""OpenAIChatGateway 断路器接线测试(M15 债务清偿,方案 A)。

仅 endpoint.circuit_breaker 配置存在时启用;OPEN 短路不发 HTTP;
成功/失败驱动迁移;half-open 探测与恢复;未配置端点行为不变。
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from adapters.relay.gateway import CircuitOpenRelayError, OpenAIChatGateway
from packages.application.ports import CompletionRequest
from packages.domain.circuit_breaker import CircuitBreakerConfig
from packages.domain.models import LLMEndpoint
from tests.adapters.relay.relay_fakes import CREDENTIAL, json_response

_T0 = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)

_PAYLOAD = {
    "id": "chatcmpl-1",
    "model": "relay-model",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}}],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}


def _endpoint(failure_threshold: int = 5, open_timeout_seconds: int = 60) -> LLMEndpoint:
    return LLMEndpoint(
        id="main",
        name="Main Relay",
        protocol="OPENAI_COMPATIBLE",
        base_url="https://relay.example.com/api/v1",
        credential_ref="llm_main_key",
        max_retries=0,
        circuit_breaker=CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            open_timeout_seconds=open_timeout_seconds,
        ),
    )


def _request() -> CompletionRequest:
    from packages.application.ports import CompletionRequest

    return CompletionRequest(model="relay-model", messages=[{"role": "user", "content": "hi"}])


class _FlakyTransport(httpx.BaseTransport):
    """前 `failures` 次返回 500,之后成功。"""

    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        if self.calls <= self.failures:
            return httpx.Response(500, json={"error": "boom"})
        return httpx.Response(200, json=_PAYLOAD)


def _gateway(transport: httpx.BaseTransport, now: Callable[[], datetime]) -> OpenAIChatGateway:
    return OpenAIChatGateway(transport=transport, telemetry=None, now=now)


def test_endpoint_without_breaker_config_is_unchanged() -> None:
    transport = _FlakyTransport(failures=3)
    gateway = _gateway(transport, lambda: _T0)
    for _ in range(3):
        with pytest.raises(Exception):
            gateway.complete(_endpoint(), CREDENTIAL, _request())
    assert transport.calls >= 3


def test_circuit_opens_after_threshold_and_short_circuits() -> None:
    transport = _FlakyTransport(failures=3)
    clock = {"now": _T0}
    gateway = _gateway(transport, lambda: clock["now"])
    endpoint = _endpoint(failure_threshold=3, open_timeout_seconds=60)

    outcomes = []
    for index in range(3):
        try:
            gateway.complete(endpoint, CREDENTIAL, _request())
        except CircuitOpenRelayError:
            outcomes.append("open")
        except Exception:
            outcomes.append("error")
        clock["now"] = _T0 + timedelta(seconds=index + 1)
    assert outcomes == ["error", "error", "error"]
    assert transport.calls == 3  # 三次真实失败(无内部重试,max_retries=0)

    # 开路:不再触达网络
    calls_before = transport.calls
    with pytest.raises(CircuitOpenRelayError):
        gateway.complete(endpoint, CREDENTIAL, _request())
    assert transport.calls == calls_before

    # 超时后 half-open 探测放行,成功 → 闭合
    clock["now"] = _T0 + timedelta(seconds=120)
    result = gateway.complete(endpoint, CREDENTIAL, _request())
    assert result.total_tokens == 2
    # 闭合后继续正常调用
    gateway.complete(endpoint, CREDENTIAL, _request())
    assert transport.calls == calls_before + 2


def test_half_open_probe_failure_reopens() -> None:
    transport = _FlakyTransport(failures=10)
    clock = {"now": _T0}
    gateway = _gateway(transport, lambda: clock["now"])
    endpoint = _endpoint(failure_threshold=2, open_timeout_seconds=30)
    for index in range(2):
        try:
            gateway.complete(endpoint, CREDENTIAL, _request())
        except Exception:
            pass
        clock["now"] = _T0 + timedelta(seconds=index + 1)
    # 已开路;超时后放行探测,探测失败 → 重新打开(新的 opened_at)
    clock["now"] = _T0 + timedelta(seconds=120)
    with pytest.raises(Exception):
        gateway.complete(endpoint, CREDENTIAL, _request())
    state = gateway._breaker_state(endpoint.id)
    assert state.is_open
    assert state.opened_at is not None and state.opened_at > _T0
    # 新开窗期内仍短路
    with pytest.raises(CircuitOpenRelayError):
        gateway.complete(endpoint, CREDENTIAL, _request())
    # 新超时后再次放行;transport 仍失败 → 再开;但探测名额限制已重置
    clock["now"] = state.opened_at + timedelta(seconds=31) if state.opened_at else _T0
    with pytest.raises(Exception):
        gateway.complete(endpoint, CREDENTIAL, _request())


def test_short_circuit_emits_denied_outcome() -> None:
    from adapters.fakes.telemetry_sink import FakeTelemetrySink
    from packages.application.observability.signals import OperationOutcome

    fake = FakeTelemetrySink()
    transport = _FlakyTransport(failures=1)
    clock = {"now": _T0}
    gateway = OpenAIChatGateway(transport=transport, telemetry=fake, now=lambda: clock["now"])
    endpoint = _endpoint(failure_threshold=1, open_timeout_seconds=60)
    with pytest.raises(Exception):
        gateway.complete(endpoint, CREDENTIAL, _request())
    with pytest.raises(CircuitOpenRelayError):
        gateway.complete(endpoint, CREDENTIAL, _request())
    ends = fake.ends
    assert ends[-1].outcome is OperationOutcome.DENIED
    assert ends[-1].failure_category == "MODEL_RELAY_UNAVAILABLE"
    assert ends[-1].attributes.get("circuit_state") == "OPEN"


def test_probe_success_closes_degraded_circuit() -> None:
    transport = _FlakyTransport(failures=1)
    clock = {"now": _T0}
    gateway = _gateway(transport, lambda: clock["now"])
    endpoint = _endpoint(failure_threshold=1, open_timeout_seconds=60)
    try:
        gateway.list_models(endpoint, CREDENTIAL)
    except Exception:
        pass
    assert gateway._breaker_state(endpoint.id).is_open
    clock["now"] = _T0 + timedelta(seconds=61)
    gateway.list_models(endpoint, CREDENTIAL)  # half-open 探测成功 → 闭合
    assert gateway._breaker_state(endpoint.id).state == "CLOSED"
    assert json_response is not None
