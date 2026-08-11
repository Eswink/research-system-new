"""Endpoint health 记录构建测试（application 层接线 domain 状态机）。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.application.model_relay.health import evaluate_endpoint_health
from packages.domain.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerState,
    apply_failure,
    initial_state,
)
from packages.domain.enums import EndpointHealth, FailureCategory
from packages.domain.models import LLMEndpoint

T0 = datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)

CB_CONFIG = CircuitBreakerConfig(failure_threshold=2)

ENDPOINT = LLMEndpoint(
    id="main",
    name="Main Relay",
    protocol="OPENAI_COMPATIBLE",
    base_url="https://relay.example.com/api/v1",
    credential_ref="llm_main_key",
    circuit_breaker=CB_CONFIG,
)

DISABLED = LLMEndpoint(
    id="main",
    name="Main Relay",
    protocol="OPENAI_COMPATIBLE",
    base_url="https://relay.example.com/api/v1",
    credential_ref="llm_main_key",
    enabled=False,
)


class TestEvaluateEndpointHealth:
    def test_healthy(self) -> None:
        record = evaluate_endpoint_health(
            endpoint=ENDPOINT, circuit_state=initial_state(), recorded_at=T0
        )
        assert record.state is EndpointHealth.HEALTHY
        assert record.circuit_state == "CLOSED"
        assert record.consecutive_failures == 0
        assert record.last_error_category is None

    def test_degraded_after_failure(self) -> None:
        state = apply_failure(initial_state(), CB_CONFIG)
        record = evaluate_endpoint_health(
            endpoint=ENDPOINT,
            circuit_state=state,
            last_error_category=FailureCategory.MODEL_RATE_LIMIT,
            recorded_at=T0,
        )
        assert record.state is EndpointHealth.DEGRADED
        assert record.consecutive_failures == 1
        assert record.last_error_category is FailureCategory.MODEL_RATE_LIMIT

    def test_open_circuit_after_threshold(self) -> None:
        state = apply_failure(apply_failure(initial_state(), CB_CONFIG), CB_CONFIG)
        record = evaluate_endpoint_health(
            endpoint=ENDPOINT,
            circuit_state=state,
            last_error_category=FailureCategory.MODEL_RELAY_UNAVAILABLE,
            recorded_at=T0,
        )
        assert record.state is EndpointHealth.OPEN_CIRCUIT
        assert record.circuit_state == "OPEN"

    def test_disabled_endpoint(self) -> None:
        record = evaluate_endpoint_health(
            endpoint=DISABLED, circuit_state=initial_state(), recorded_at=T0
        )
        assert record.state is EndpointHealth.DISABLED

    def test_naive_recorded_at_rejected(self) -> None:
        with pytest.raises(ValueError):
            evaluate_endpoint_health(
                endpoint=ENDPOINT,
                circuit_state=CircuitBreakerState(
                    state="CLOSED", consecutive_failures=0, opened_at=None, probes_in_half_open=0
                ),
                recorded_at=datetime(2026, 8, 11, 12, 0, 0),
            )
