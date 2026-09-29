---
id: MEM-20260929-169
title: "取消后「不再产生副作用」的锚点是删租约、不是 cancelled 标志：完成路径里根本没有这个检查；动取消语义会连坐陈旧完成"
status: ACTIVE
created_at: 2026-09-29
updated_at: 2026-09-29
scope: repository
confidence: 0.9
review_after: 2027-03-29
source_plans:
  - .cursor/plans/tasks/PLAN-20260929-249-goal-026-ec03-breaker-dead-letter-cancel.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260929-250-goal-026-ec03-breaker-dead-letter-cancel.md
supersedes: []
tags: [cancellation, lease, sqlite, workflow-engine, goal-026, ec-03]
---

## 做了什么

GOAL-026 EC-03 给「取消语义」补判据时，用**按压**把机制锚点问出来了：
把 `adapters/sqlite/cancel_run.py::cancel_task` 事务块里的
`DELETE FROM leases WHERE task_id = ?` 删掉（其余不动）⇒ 取消之后拿**旧租约**提交完成，
本该被拒的**陈旧完成被接受**。

## 为什么这样做

- **抑制副作用的锚点在别处**：`adapters/sqlite/workflow_ops.py` 的完成路径**没有**
  `cancelled` 检查（全仓只有 claim 候选扫描用 `cancelled = 0` 过滤）。取消之所以能
  「之后不再产生副作用」，是因为**旧租约被删除** ⇒ `_require_current_lease` 找不到行 ⇒
  拒绝。也就是说：**取消的安全性挂在租约生命周期上**，而不是挂在取消标志上。
- **这件事的后果是连坐**：任何「取消时不再删租约」或「让完成路径容忍缺失租约」的改动，
  都会**同时**打开「取消后仍产生副作用」这个口子，而**表面上**看起来只是在动租约/回收逻辑。
  改取消、改租约、改完成三处中任何一处，都必须把「取消后的陈旧完成」重跑一遍。
- **容易误判的读法**：`_COMPLETION_ALREADY_APPLIED` 不含 `CANCELLED` ⇒ 陈旧完成**不会被当成
  重放静默吞掉**，而是必须**响亮地被拒**（`InvalidInputError`）。所以「完成幂等集里没有
  `CANCELLED`」与「取消后完成被拒」是**两条互补事实**，只改一半就会从「被拒」变成
  「被吞掉」或「被接受」。

## 怎么做与复现

1. 判据：`tests/adapters/sqlite/test_workflow_cancel_semantics.py`
   （重复取消 ⇒ 结构化 `deduped` + outbox 计数不变；陈旧完成 ⇒ `InvalidInputError` + outbox 零新增）。
2. 按压：删掉 `DELETE FROM leases` 那一行 ⇒ 判据红（`Failed: DID NOT RAISE InvalidInputError`）。
3. 按压态取证（`scratch/goal026_ec03_pressb_probe.py`，公开 API）：
   `status_after_stale_completion = SUCCEEDED`、`outbox_events_before = 2 after = 3`
   ⇒ 「取消后仍产生副作用」是实测形态。
4. 复原：raw `sha256` 回到 `a9d132c525a30bf3a70432a9876429d4e429a67442acde29c296258e28929982`。

## 适用边界

- 结论落在 **SQLite** 适配器；PG 侧未在本轮射程内复核（承 EC-02 `W-1`/`W-2`）。
- 「取消**在飞**工作」不在射程：取消是**协作式**的，没有向在飞执行发信号的通道
  ⇒ 本判据只覆盖「陈旧完成」这一形态（登记 `R26-3`）。
- 断言绑**结构化面**（状态串 / 计数 / 异常类型），不匹配错误文案。

## 来源

- `PLAN-20260929-249`（GOAL-026 EC-03）与 `RECHECK-20260929-250`；
- 实跑留档：`scratch/goal026-ec03-press-matrix.log`（二进制写盘 / `CR` 计数 0）；
- 相关代码：`adapters/sqlite/cancel_run.py::cancel_task`、
  `adapters/sqlite/workflow_ops.py::_COMPLETION_ALREADY_APPLIED`；
- 同轮另一条记忆：[[MEM-20260929-170]]（吞掉迁移异常 = fail-open）；租约/心跳侧见
  [[MEM-20260929-168]]。
