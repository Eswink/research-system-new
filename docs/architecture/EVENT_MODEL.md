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
run.resume_compensation_failed
```

`manifest.frozen` 的 payload 带冻结引用与执行体事实：`digest`（覆盖 `frozen_at` 的快照
标识）、`semantic_digest`（排除冻结时刻，resume 漂移校验的输入）、`pricing_version` +
`pricing_digest`、`run_id`，以及 `execution_backend`（执行基质；`None` = 冻结时未声明）
与 `runtime_fingerprint`（AGENTS.md §4 指纹槽位的**状态**记录；空对象 = 未声明该面）。
后三项是 GOAL-007 EC-01/EC-04 依次加的**加性**键——旧 reader 忽略即兼容，且
`GET /runs/{id}` 的 `execution` 读面回读的正是这份 payload（不另存副本）。
语义 digest 必须在事件里：执行期失败收敛的 run 没有 `RunOutcome`
可读，只能从事件链把 run 行的冻结引用补回来（GOAL-004 cycle 4 = EC-04）。

`model.probed`（GOAL-010 EC-04 起**真的会发出**；此前只是声明过的枚举成员）：run 收敛后，
若这次执行的会话**观测到** provider 侧报告的 model 名，就把指纹四要素（返回 model 名 /
端点头 / probe 版本 / 兼容性结论 + 缺项点名）落成一条 `model.probed`。payload 键与
`GET /runs/{id}` 的 `execution.runtime_fingerprint` 读数一一对应（`verdict` → `status`），
另带 `observed_model_identifiers`（本次观测到的**全部**名字，去重排序）。**没有观测 ⇒
不发事件**：读面此时保持冻结占位，而不是拿到一条空记录。usage/制品计数器
（`model_tokens` / `usage_entries` / `artifact_ids` / `evidence_ids`）**不**随这条事件发布：
它们的真值面是 cost/usage 读面，记录里的默认 0 不是实测值。

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

`run.resume_compensation_failed` 是**补偿本身失败**的记录（GOAL-20260918-006 cycle 6 =
EC-06 (b)）：一次补偿尝试（迁移 + 落库）没做成时 run 仍停在原 canonical 状态、下一轮重新
评估；这条事件让"这次补偿没做成"在读面上可判，而不是只在遥测/log 里（此前该路径是
`except: pass`）。payload 键：`run_id` / `failure_type` / `message` / `canonical_state`——
前三个与 `run.resume_failed` 同形但描述的是**补偿**这次的失败，`canonical_state` 是补偿
失败时 run 仍停在的状态（没有被伪造成 `PAUSED`）。**一等边界**：`run.resume_failed` 的
payload 只有异常类型与文本，**不含任务级归因**（"哪一步炸的"要读该 run 的事件链上下文，
本事件与它都不承诺任务/phase 身份）。

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
