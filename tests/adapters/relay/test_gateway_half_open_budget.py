"""GOAL-026 EC-03（AC-1）：模型端点断路器的**三态结构化断言** + **半开探针预算**判定。

既有判据（`tests/adapters/relay/test_gateway_circuit.py`）已覆盖「阈值失败 ⇒ OPEN ⇒
快速失败 ⇒ 时钟跳 ⇒ 半开探针成功 ⇒ CLOSED」与读面探针。本判据补两件它没有的事：

1. **三态各有结构化断言**（拿状态串 `/is_open` 断言，不靠异常文本）：
   `CLOSED` **放行**、`OPEN` **拒绝且不触达下游**、`HALF_OPEN` **放行一个探针**；
2. **半开探针预算耗尽**时的行为：声明语义（`half_open_max_probes` 与
   `_consult_circuit` 的注释「探测名额耗尽的再次 consult 视为拒绝」）
   要求**拒绝且不触达下游**。

第 2 条是**候选真缺陷**：本轮实测前的行为是「迁移错误被吞 ⇒ 沿用 HALF_OPEN 状态 ⇒
`is_open` 为假 ⇒ **请求被放行**」。本判据把它钉成判据，并按 GOAL-026 的
「修被新判据证明为真缺陷的问题（只允许收紧）」处置。
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from adapters.relay.gateway import CircuitOpenRelayError, OpenAIChatGateway
from packages.application.ports import CompletionRequest
from packages.domain.circuit_breaker import CircuitBreakerConfig, CircuitBreakerState
from packages.domain.models import LLMEndpoint
from tests.adapters.relay.relay_fakes import CREDENTIAL

_T0 = datetime(2026, 9, 29, 12, 0, 0, tzinfo=timezone.utc)

_PAYLOAD = {
    "id": "chatcmpl-1",
    "model": "relay-model",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}}],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}


class _CountingTransport(httpx.BaseTransport):
    """总是成功，但**数调用**：用来证「拒绝时不触达下游」。"""

    def __init__(self) -> None:
        self.calls = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        return httpx.Response(200, json=_PAYLOAD)


class _FailingTransport(httpx.BaseTransport):
    """总是 500：用来走**真实**的「失败计数 ⇒ 阈值 ⇒ 开路」路径。"""

    def __init__(self) -> None:
        self.calls = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        return httpx.Response(500, json={"error": "boom"})


def _endpoint(*, max_probes: int = 1) -> LLMEndpoint:
    return LLMEndpoint(
        id="main",
        name="Main Relay",
        protocol="OPENAI_COMPATIBLE",
        base_url="https://relay.example.com/api/v1",
        credential_ref="llm_main_key",
        max_retries=0,
        circuit_breaker=CircuitBreakerConfig(
            failure_threshold=1, open_timeout_seconds=60, half_open_max_probes=max_probes
        ),
    )


def _request() -> CompletionRequest:
    return CompletionRequest(model="relay-model", messages=[{"role": "user", "content": "hi"}])


def _gateway(transport: httpx.BaseTransport, now: Callable[[], datetime]) -> OpenAIChatGateway:
    return OpenAIChatGateway(transport=transport, telemetry=None, now=now)


def _seed(gateway: OpenAIChatGateway, endpoint: LLMEndpoint, state: CircuitBreakerState) -> None:
    """直接把断路器置成目标态（并发边界无法从公开 API 确定性构造）。"""
    gateway._store_breaker(endpoint.id, state)


def test_closed_state_admits_the_request() -> None:
    """`CLOSED` ⇒ 放行（受判面非空：下游真的被调到）。"""
    transport = _CountingTransport()
    gateway = _gateway(transport, lambda: _T0)
    endpoint = _endpoint()
    _seed(gateway, endpoint, CircuitBreakerState("CLOSED", 0, None, 0))

    gateway.complete(endpoint, CREDENTIAL, _request())

    assert transport.calls == 1
    assert gateway._breaker_state(endpoint.id).state == "CLOSED"


def test_open_state_denies_without_touching_downstream() -> None:
    """`OPEN`（尚未到冷却）⇒ 拒绝且**不触达下游**（结构化：状态串 + 调用计数）。"""
    transport = _CountingTransport()
    gateway = _gateway(transport, lambda: _T0 + timedelta(seconds=1))
    endpoint = _endpoint()
    _seed(gateway, endpoint, CircuitBreakerState("OPEN", 1, _T0, 0))

    with pytest.raises(CircuitOpenRelayError):
        gateway.complete(endpoint, CREDENTIAL, _request())

    assert transport.calls == 0
    assert gateway._breaker_state(endpoint.id).is_open


def test_half_open_admits_one_probe() -> None:
    """`HALF_OPEN`（名额未用）⇒ **放行**一个探针；成功 ⇒ 闭合（结构化状态串）。"""
    transport = _CountingTransport()
    gateway = _gateway(transport, lambda: _T0)
    endpoint = _endpoint(max_probes=1)
    _seed(gateway, endpoint, CircuitBreakerState("HALF_OPEN", 1, _T0, 0))

    gateway.complete(endpoint, CREDENTIAL, _request())

    assert transport.calls == 1, "半开探针必须真的下发"
    assert gateway._breaker_state(endpoint.id).state == "CLOSED"


def test_failures_reach_the_threshold_and_open_the_circuit() -> None:
    """阈值**驱动**：真实失败达阈值 ⇒ `OPEN`；此后调用**快速失败且不触达下游**。

    （与上面几条「直接置态」的用例互补：这条走产品路径，阈值不可达时它会红。）
    """
    transport = _FailingTransport()
    gateway = _gateway(transport, lambda: _T0)
    endpoint = _endpoint()

    with pytest.raises(Exception):
        gateway.complete(endpoint, CREDENTIAL, _request())

    assert gateway._breaker_state(endpoint.id).is_open, "达阈值必须开路"
    calls_before = transport.calls
    with pytest.raises(CircuitOpenRelayError):
        gateway.complete(endpoint, CREDENTIAL, _request())
    assert transport.calls == calls_before, "开路后不得再触达下游"


def test_exhausted_half_open_probe_budget_denies_without_touching_downstream() -> None:
    """`HALF_OPEN` 且**名额已用完** ⇒ 拒绝且**不触达下游**。

    这一态等价于「一个探针正在飞、后续并发请求到达」。声明语义
    （`half_open_max_probes` + `_consult_circuit` 的注释）要求**拒绝**；
    若放行，则探针上限形同虚设（半开期可以无限并发打下游）。
    """
    transport = _CountingTransport()
    gateway = _gateway(transport, lambda: _T0)
    endpoint = _endpoint(max_probes=1)
    _seed(gateway, endpoint, CircuitBreakerState("HALF_OPEN", 1, _T0, 1))

    with pytest.raises(CircuitOpenRelayError):
        gateway.complete(endpoint, CREDENTIAL, _request())

    assert transport.calls == 0, "名额耗尽必须快速失败、不得触达下游"
