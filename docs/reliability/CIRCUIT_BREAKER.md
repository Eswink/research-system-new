# Endpoint Circuit Breaker v0.4.0

Endpoint 熔断器是 v0.4.0 明确规格；实现位于 `packages/domain/circuit_breaker.py`，测试位于 `tests/domain/test_circuit_breaker.py`。状态集合与迁移表是只读可测试契约。

## CircuitBreakerState

```text
CLOSED
OPEN
HALF_OPEN
```

- `CLOSED`：正常处理请求，连续失败计数；达到阈值后打开。
- `OPEN`：拒绝请求（快速失败），等待 `open_timeout_seconds` 后进入半开。
- `HALF_OPEN`：允许有限数量的探测请求（`half_open_max_probes`）；任一探测成功则关闭，任一探测失败则重新打开并重置计时。

## EndpointHealth 映射

| CircuitBreakerState | EndpointHealth |
| --- | --- |
| CLOSED（无失败） | HEALTHY |
| CLOSED（有失败未达阈值） | DEGRADED |
| OPEN | OPEN_CIRCUIT |
| HALF_OPEN | DEGRADED |
| DISABLED（端点禁用） | DISABLED |

## 迁移表

| From | Event | Condition | To |
| --- | --- | --- | --- |
| CLOSED | FAIL | 连续失败 >= failure_threshold | OPEN |
| CLOSED | FAIL | 连续失败 < failure_threshold | CLOSED |
| CLOSED | SUCCESS | — | CLOSED |
| OPEN | TICK | 已等待 >= open_timeout_seconds | HALF_OPEN |
| OPEN | TICK | 未到超时 | OPEN |
| HALF_OPEN | SUCCESS | — | CLOSED |
| HALF_OPEN | FAIL | — | OPEN |

## 配置（llm-endpoint.schema.json）

```yaml
circuit_breaker:
  failure_threshold: 5      # 连续失败阈值，>= 1
  open_timeout_seconds: 60  # OPEN 到 HALF_OPEN 等待，>= 1
  half_open_max_probes: 1   # 半开探测上限，>= 1
```

## 规则

- 只在记录失败后重放状态迁移，不猜测未发生的事件；
- `EndpointHealth.DISABLED` 不由熔断器迁移产生，由端点启用状态决定；
- 熔断状态与 `EndpointHealth` 的映射必须保持上表（测试覆盖）；
- 健康记录（`EndpointHealthRecord`，schemas/endpoint-health.schema.json）由 application 层 `evaluate_endpoint_health` 从 `CircuitBreakerState` 生成并记录 `last_error_category`；执行层（M7）在请求失败/成功时对状态机应用 `apply_failure` / `apply_success` / `apply_tick` 后落盘。