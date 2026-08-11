# Workflow Reliability v0.4.0

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

Canonical failure categories 只定义在 `docs/reliability/FAILURE_MODEL.md`。Workflow 不维护第二套 failure enum，而是根据以下输入产生 retry disposition：

```text
FailureRecord.category
+ operation idempotency
+ attempt budget
+ endpoint/provider health
+ policy/budget decision
→ retry / rework / manual recovery / terminal
```

关键规则：

- `MODEL_RATE_LIMIT`、`WORKER_LOST` 可在预算和幂等条件满足时自动重试；
- `TOOL_TIMEOUT` 仅对幂等调用或已有 compensation 的调用重试；
- `VALIDATION_FAILURE` 创建新 attempt/rework，不复用已失败输出；
- `POLICY_DENIED`、`APPROVAL_REJECTED`、`BUDGET_EXHAUSTED` 进入人工或策略决策；
- `SCIENTIFIC_NEGATIVE_RESULT` 是研究结果，不转换为系统失败重试。

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
