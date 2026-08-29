"""Endpoint 熔断器纯函数状态机。

状态集合与迁移表见 `docs/reliability/CIRCUIT_BREAKER.md`；
`EndpointHealth` 映射保持该文档表格。domain 零第三方依赖。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from packages.domain.enums import EndpointHealth

# 迁移事件名称（与文档迁移表一致）
SUCCESS = "SUCCESS"
FAIL = "FAIL"
TICK = "TICK"


@dataclass(frozen=True, slots=True)
class CircuitBreakerConfig:
    """熔断配置（对应 llm-endpoint.schema.json circuit_breaker 对象）。"""

    failure_threshold: int = 5
    open_timeout_seconds: int = 60
    half_open_max_probes: int = 1

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if self.open_timeout_seconds < 1:
            raise ValueError("open_timeout_seconds must be >= 1")
        if self.half_open_max_probes < 1:
            raise ValueError("half_open_max_probes must be >= 1")


@dataclass(frozen=True, slots=True)
class CircuitBreakerState:
    """不可变熔断状态；每次事件返回新状态，不原地修改。"""

    state: str  # CLOSED | OPEN | HALF_OPEN
    consecutive_failures: int
    opened_at: datetime | None
    probes_in_half_open: int

    @property
    def is_open(self) -> bool:
        return self.state == "OPEN"

    @property
    def is_half_open(self) -> bool:
        return self.state == "HALF_OPEN"

    def to_endpoint_health(self, endpoint_enabled: bool = True) -> EndpointHealth:
        if not endpoint_enabled:
            return EndpointHealth.DISABLED
        if self.state == "OPEN":
            return EndpointHealth.OPEN_CIRCUIT
        if self.state == "HALF_OPEN" or self.consecutive_failures > 0:
            return EndpointHealth.DEGRADED
        return EndpointHealth.HEALTHY


@dataclass(frozen=True, slots=True)
class CircuitBreakerTransitionError(ValueError):
    """非法熔断迁移。"""

    current: str
    event: str

    def __str__(self) -> str:
        return (
            f"invalid circuit breaker transition: event={self.event!r} from state={self.current!r}"
        )


def initial_state() -> CircuitBreakerState:
    return CircuitBreakerState(
        state="CLOSED", consecutive_failures=0, opened_at=None, probes_in_half_open=0
    )


def apply_success(state: CircuitBreakerState, config: CircuitBreakerConfig) -> CircuitBreakerState:
    if state.state == "HALF_OPEN":
        return initial_state()
    if state.state == "CLOSED":
        return CircuitBreakerState(
            state="CLOSED", consecutive_failures=0, opened_at=None, probes_in_half_open=0
        )
    raise CircuitBreakerTransitionError(state.state, SUCCESS)


def apply_failure(
    state: CircuitBreakerState,
    config: CircuitBreakerConfig,
    now: datetime | None = None,
) -> CircuitBreakerState:
    """失败迁移;`now` 用于打开发断路器的 opened_at(缺失则继承旧值,保持
    既有行为——调用方不传 now 时 OPEN 无 opened_at,apply_tick 不会半开)。"""
    if state.state == "HALF_OPEN":
        return CircuitBreakerState(
            state="OPEN",
            consecutive_failures=state.consecutive_failures + 1,
            opened_at=now if now is not None else state.opened_at,
            probes_in_half_open=0,
        )
    if state.state == "CLOSED":
        failures = state.consecutive_failures + 1
        if failures >= config.failure_threshold:
            return CircuitBreakerState(
                state="OPEN",
                consecutive_failures=failures,
                opened_at=now if now is not None else state.opened_at,
                probes_in_half_open=0,
            )
        return CircuitBreakerState(
            state="CLOSED",
            consecutive_failures=failures,
            opened_at=None,
            probes_in_half_open=0,
        )
    raise CircuitBreakerTransitionError(state.state, FAIL)


def apply_tick(
    state: CircuitBreakerState, config: CircuitBreakerConfig, now: datetime
) -> CircuitBreakerState:
    if state.state == "OPEN":
        if state.opened_at is not None:
            elapsed = (now - state.opened_at).total_seconds()
            if elapsed >= config.open_timeout_seconds:
                return CircuitBreakerState(
                    state="HALF_OPEN",
                    consecutive_failures=state.consecutive_failures,
                    opened_at=state.opened_at,
                    probes_in_half_open=0,
                )
        return state
    if state.state == "HALF_OPEN":
        if state.probes_in_half_open >= config.half_open_max_probes:
            raise CircuitBreakerTransitionError(state.state, TICK)
        return CircuitBreakerState(
            state="HALF_OPEN",
            consecutive_failures=state.consecutive_failures,
            opened_at=state.opened_at,
            probes_in_half_open=state.probes_in_half_open + 1,
        )
    if state.state == "CLOSED":
        return state
    raise CircuitBreakerTransitionError(state.state, TICK)
