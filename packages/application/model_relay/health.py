"""Endpoint health 记录构建。

将 domain 熔断状态机（CircuitBreakerState）映射为可持久化的
EndpointHealthRecord（schemas/endpoint-health.schema.json）。
本层负责编排；状态迁移由 domain 纯函数执行。
"""

from __future__ import annotations

from datetime import datetime, timezone

from packages.domain.circuit_breaker import CircuitBreakerState
from packages.domain.enums import FailureCategory
from packages.domain.models import EndpointHealthRecord, LLMEndpoint


def evaluate_endpoint_health(
    *,
    endpoint: LLMEndpoint,
    circuit_state: CircuitBreakerState,
    last_error_category: FailureCategory | None = None,
    recorded_at: datetime | None = None,
) -> EndpointHealthRecord:
    """按端点启用状态与熔断状态生成健康记录。"""
    return EndpointHealthRecord(
        endpoint_id=endpoint.id,
        state=circuit_state.to_endpoint_health(endpoint.enabled),
        recorded_at=recorded_at or datetime.now(timezone.utc),
        circuit_state=circuit_state.state,
        consecutive_failures=circuit_state.consecutive_failures,
        last_error_category=last_error_category,
        opened_at=circuit_state.opened_at,
    )
