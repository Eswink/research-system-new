# Workflow Reliability v0.2.2

## 1. 执行语义

系统按：

```text
at-least-once delivery
+
idempotent handlers
+
dedupe
```

设计。

## 2. Task Lease

Worker 获取：

```text
lease_id
owner
expires_at
heartbeat_interval
attempt
```

超时后可重新调度。

## 3. Retry Classification

```text
TRANSIENT_NETWORK
RATE_LIMIT
MODEL_UNAVAILABLE
TOOL_TIMEOUT
WORKER_CRASH
VALIDATION_FAILURE
POLICY_DENIED
BUDGET_EXHAUSTED
NON_IDEMPOTENT_FAILURE
SCIENTIFIC_NEGATIVE_RESULT
SYSTEM_BUG
```

只有允许重试的类别自动重试。

## 4. Backoff / Circuit Breaker

Endpoint/Tool Provider 维护：

```text
failure_count
window
open_until
half_open_probe
```

避免故障风暴。

## 5. Idempotency

副作用调用至少支持：

```text
operation_key
request_digest
result_ref
status
```

对于无幂等支持的外部 API：

- 不自动重试；
- 或先写 intent / reservation；
- 或提供 compensation。

## 6. Transactional Outbox

Domain transaction 同时写：

```text
business entity
+
outbox event
```

异步 publisher 发送并标记完成。

## 7. Cancellation

区分：

```text
REQUESTED
COOPERATIVE
FORCED
COMPENSATING
CANCELLED
```

强制终止后要检查 Workspace/Artifact/Lease 是否残留。

## 8. Resume

Resume 前验证：

- Manifest；
- Tool Set；
- Model binding/fingerprint；
- Workspace snapshot；
- credentials；
- pending non-idempotent operations。

## 9. Fork

当模型、Tool、Prompt、策略需要实质改变时，优先 Fork Run/Task，而不是污染原轨迹。
