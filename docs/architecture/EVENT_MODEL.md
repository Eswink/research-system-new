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
run.resume_failed
```

`manifest.frozen` 的 payload 带三项冻结引用：`digest`（覆盖 `frozen_at` 的快照标识）、
`semantic_digest`（排除冻结时刻，resume 漂移校验的输入）、`pricing_version` +
`pricing_digest`。语义 digest 必须在事件里：执行期失败收敛的 run 没有 `RunOutcome`
可读，只能从事件链把 run 行的冻结引用补回来（GOAL-004 cycle 4 = EC-04）。

**旧事件形态**（GOAL-005 cycle 6 = EC-06）：早于语义 digest 那一轮的 `manifest.frozen`
payload **只有 `digest`**（可能另有 `run_id`）。回填路径对缺失键的处理是"当作没有这一项"
（`FrozenManifestRefs.from_payload` 只认非空字符串）⇒ 这类 run 的
`manifest_semantic_digest` 落 `None`，**不伪造**语义 digest（伪造的引用会被漂移校验拿去
比对一份不存在的 manifest，比留空更糟）。这类历史行在控制面读面上由
`RunDetailDto.rebuild` **点名**：`status=REFUSED` +
`missing=["manifest_semantic_digest", …]`（哪条事实缺、重建此路不通），而不是一个含糊的
`None`；`/resume` 的拒绝文案与它同源（同一个分类器
`packages/application/run_orchestration/rebuild_readiness.py`）。

`run.resume_failed` 是**续跑失败被补偿**的记录（GOAL-004 cycle 7 = EC-06）：一次续跑
尝试执行失败后，canonical 被放回 `PAUSED`，payload 带 `failure_type` / `message` /
`compensated_to`。失败**不是终态**，所以它不等于 `run.failed`；读面也不新增"停车原因"
字段——原因只在事件链里（与 GOAL-004 cycle 2 的口径一致）。

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
