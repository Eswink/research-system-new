# Event Model v0.4.0

## 1. Domain Events

新增核心事件：

```text
protocol.compiled
preflight.completed
manifest.frozen
team.resolved
role.activated
model.probed
model.resolved
model.drift_detected
budget.reserved
task.created
task.leased
task.heartbeat
task.retry_scheduled
task.completed
task.failed
task.cancelled
handoff.created
approval.requested
approval.decided
memory.proposed
memory.committed
tool_pack.installed
tool_pack.updated
tool_pack.revoked
tool_call.started
tool_call.completed
workspace.snapshot.created
artifact.verified
claim.verified
claim.disputed
memory.deleted
run.forked
run.completed
run.cancelled
run.failed
run.degraded
```

`manifest.frozen` 的 payload 带三项冻结引用：`digest`（覆盖 `frozen_at` 的快照标识）、
`semantic_digest`（排除冻结时刻，resume 漂移校验的输入）、`pricing_version` +
`pricing_digest`。语义 digest 必须在事件里：执行期失败收敛的 run 没有 `RunOutcome`
可读，只能从事件链把 run 行的冻结引用补回来（GOAL-004 cycle 4 = EC-04）。

## 2. Event Envelope

```text
event_id
event_type
schema_version
occurred_at
actor
scope
project_id
run_id?
phase_run_id?
task_id?
agent_session_id?
trace_id
payload
payload_digest
```

## 3. Outbox

Domain event 先写 Outbox，再发布。

Consumer 必须按 `event_id` 去重。

## 4. Sensitive Content

不保存：

- secret
- auth header
- raw private CoT
- 默认完整 Prompt/Response

## 5. Schema Evolution

Event schema 只能向后兼容演进；破坏性变化增加新版本和 migration/projection。
