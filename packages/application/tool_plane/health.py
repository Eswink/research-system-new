"""ToolHealthMonitor：provider 健康 probe + 熔断状态驱动（MCP_TOOL_PROVIDERS.md §6）。

复用 domain/circuit_breaker.py 的纯状态机：每个 provider 一个
CircuitBreakerState；check_health 成功 apply_success，失败
apply_failure；OPEN 期间 provider 不参与 resolve（resolver 的
provider_health 输入由本模块产出）。

本模块是纯状态层；probe I/O（ToolProvider.check_health）由
record_probe 的调用方执行，保持可确定性测试。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from packages.domain.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerState,
    apply_failure,
    apply_success,
    initial_state,
)
from packages.domain.enums import EndpointHealth
from packages.domain.tools import ToolHealthReport


@dataclass(frozen=True, slots=True)
class ToolHealthSnapshot:
    provider_health: Mapping[str, EndpointHealth] = field(default_factory=dict)
    breaker_states: Mapping[str, CircuitBreakerState] = field(default_factory=dict)

    def is_available(self, provider_id: str) -> bool:
        return self.provider_health.get(provider_id, EndpointHealth.HEALTHY) not in {
            EndpointHealth.OPEN_CIRCUIT,
            EndpointHealth.DISABLED,
        }


def monitor_config() -> CircuitBreakerConfig:
    return CircuitBreakerConfig()


def record_probe(
    snapshot: ToolHealthSnapshot,
    provider_id: str,
    report: ToolHealthReport,
) -> ToolHealthSnapshot:
    """把一次 health probe 结果并入状态（成功闭合/半开闭合，失败计数）。"""
    config = monitor_config()
    state = snapshot.breaker_states.get(provider_id, initial_state())
    if report.status is EndpointHealth.OPEN_CIRCUIT:
        new_state = apply_failure(state, config)
    else:
        new_state = apply_success(state, config)
    breaker_states = dict(snapshot.breaker_states)
    breaker_states[provider_id] = new_state
    health = dict(snapshot.provider_health)
    health[provider_id] = new_state.to_endpoint_health()
    return ToolHealthSnapshot(provider_health=health, breaker_states=breaker_states)


def record_probe_failure(snapshot: ToolHealthSnapshot, provider_id: str) -> ToolHealthSnapshot:
    """probe 抛异常（transport 不可达）的等价失败信号。"""
    return record_probe(
        snapshot,
        provider_id,
        ToolHealthReport(provider_id=provider_id, status=EndpointHealth.OPEN_CIRCUIT),
    )


def mark_disabled(snapshot: ToolHealthSnapshot, provider_id: str) -> ToolHealthSnapshot:
    health = dict(snapshot.provider_health)
    health[provider_id] = EndpointHealth.DISABLED
    return ToolHealthSnapshot(
        provider_health=health,
        breaker_states=snapshot.breaker_states,
    )


def is_circuit_open(snapshot: ToolHealthSnapshot, provider_id: str) -> bool:
    return (
        snapshot.provider_health.get(provider_id, EndpointHealth.HEALTHY)
        is EndpointHealth.OPEN_CIRCUIT
    )


def health_for_resolver(snapshot: ToolHealthSnapshot) -> Mapping[str, EndpointHealth]:
    """resolver ResolutionInput.provider_health 的输入面。"""
    return snapshot.provider_health
