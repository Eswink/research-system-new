"""熔断器状态机迁移表测试。

覆盖 `docs/reliability/CIRCUIT_BREAKER.md` 迁移表全部行：
合法迁移、非法迁移、EndpointHealth 映射、配置不变量。
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.domain.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerState,
    CircuitBreakerTransitionError,
    apply_failure,
    apply_success,
    apply_tick,
    initial_state,
)
from packages.domain.enums import EndpointHealth

T0 = datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)


def _open_state(failures: int = 5, opened: datetime | None = T0) -> CircuitBreakerState:
    return CircuitBreakerState(
        state="OPEN", consecutive_failures=failures, opened_at=opened, probes_in_half_open=0
    )


def _half_open(failures: int = 5, probes: int = 0) -> CircuitBreakerState:
    return CircuitBreakerState(
        state="HALF_OPEN", consecutive_failures=failures, opened_at=T0, probes_in_half_open=probes
    )


class TestCircuitBreakerConfig:
    def test_invalid_failure_threshold(self) -> None:
        with pytest.raises(ValueError):
            CircuitBreakerConfig(failure_threshold=0)

    def test_invalid_open_timeout(self) -> None:
        with pytest.raises(ValueError):
            CircuitBreakerConfig(open_timeout_seconds=0)

    def test_invalid_half_open_probes(self) -> None:
        with pytest.raises(ValueError):
            CircuitBreakerConfig(half_open_max_probes=0)


class TestTransitionTable:
    def test_closed_success_stays_closed(self) -> None:
        assert apply_success(initial_state(), CircuitBreakerConfig()) == initial_state()

    def test_closed_failure_below_threshold_stays_closed(self) -> None:
        config = CircuitBreakerConfig(failure_threshold=3)
        state = apply_failure(initial_state(), config)
        assert state.state == "CLOSED"
        assert state.consecutive_failures == 1
        assert state.to_endpoint_health() is EndpointHealth.DEGRADED

    def test_closed_failure_reaches_threshold_opens(self) -> None:
        config = CircuitBreakerConfig(failure_threshold=2)
        state = apply_failure(apply_failure(initial_state(), config), config)
        assert state.state == "OPEN"
        assert state.to_endpoint_health() is EndpointHealth.OPEN_CIRCUIT

    def test_open_tick_before_timeout_stays_open(self) -> None:
        config = CircuitBreakerConfig(open_timeout_seconds=60)
        state = _open_state(opened=T0)
        later = datetime(2026, 8, 11, 12, 0, 30, tzinfo=timezone.utc)
        assert apply_tick(state, config, later).state == "OPEN"

    def test_open_tick_after_timeout_half_open(self) -> None:
        config = CircuitBreakerConfig(open_timeout_seconds=60)
        state = _open_state(opened=T0)
        later = datetime(2026, 8, 11, 12, 1, 0, tzinfo=timezone.utc)
        assert apply_tick(state, config, later).state == "HALF_OPEN"

    def test_half_open_success_closes(self) -> None:
        assert apply_success(_half_open(), CircuitBreakerConfig()) == initial_state()

    def test_half_open_failure_reopens(self) -> None:
        reopened = apply_failure(_half_open(), CircuitBreakerConfig())
        assert reopened.state == "OPEN"

    def test_half_open_probe_limit_exceeded(self) -> None:
        config = CircuitBreakerConfig(half_open_max_probes=1)
        state = _half_open(probes=1)
        with pytest.raises(CircuitBreakerTransitionError):
            apply_tick(state, config, T0)


class TestIllegalTransitions:
    def test_open_success_is_illegal(self) -> None:
        with pytest.raises(CircuitBreakerTransitionError):
            apply_success(_open_state(), CircuitBreakerConfig())

    def test_open_failure_is_illegal(self) -> None:
        with pytest.raises(CircuitBreakerTransitionError):
            apply_failure(_open_state(), CircuitBreakerConfig())

    def test_half_open_tick_before_success_or_failure_is_illegal_without_probe_budget(self) -> None:
        config = CircuitBreakerConfig(half_open_max_probes=1)
        state = _half_open(probes=0)
        consumed = apply_tick(state, config, T0)
        with pytest.raises(CircuitBreakerTransitionError):
            apply_tick(consumed, config, T0)


class TestEndpointHealthMapping:
    @pytest.mark.parametrize(
        ("state", "enabled", "expected"),
        [
            (initial_state(), True, EndpointHealth.HEALTHY),
            (
                CircuitBreakerState(
                    state="CLOSED", consecutive_failures=2, opened_at=None, probes_in_half_open=0
                ),
                True,
                EndpointHealth.DEGRADED,
            ),
            (_open_state(), True, EndpointHealth.OPEN_CIRCUIT),
            (_half_open(), True, EndpointHealth.DEGRADED),
            (initial_state(), False, EndpointHealth.DISABLED),
        ],
    )
    def test_mapping(
        self,
        state: CircuitBreakerState,
        enabled: bool,
        expected: EndpointHealth,
    ) -> None:
        assert state.to_endpoint_health(enabled) is expected
