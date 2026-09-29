---
id: MEM-20260929-168
title: "可靠性语义的判据要「接起来」才成立：心跳必须证「挡住回收」、退避必须取引擎路径的实际落库轨迹、续租必须证非零；断言绑结构化字段而非错误文本"
status: ACTIVE
created_at: 2026-09-29
updated_at: 2026-09-29
scope: repository
confidence: 0.9
review_after: 2027-03-29
source_plans:
  - .cursor/plans/tasks/PLAN-20260929-247-goal-026-ec02-lease-heartbeat-retry-backoff.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260929-248-goal-026-ec02-lease-heartbeat-retry-backoff.md
supersedes: []
tags: [lease, heartbeat, backoff, retry-classification, clock-seam, goal-026, ec-02]
---

## 做了什么

GOAL-026 EC-02 给 §7 的三项义务补判据（三个新文件 / 7 例）：

1. `tests/adapters/sqlite/test_workflow_lease_lifecycle.py`：到期 ⇒ 回收 ⇒ 二次 claim（`fence`
   前进）；**心跳挡住回收**（过原 TTL 回收 0 条 + 仍 `LEASED` + 抢不走）；停跳后按**新**期限到期；
2. `tests/adapters/sqlite/test_workflow_retry_trajectory.py`：从 `tasks.retry_at` 取连续 4 次失败的
   实际间隔 ⇒ 实测 **`[30, 60, 100, 100]`**（单调不减 + 上界封顶 + 确实增长），第 5 次 ⇒ `DEAD_LETTER`；
   不可重试类别 ⇒ `FAILED` 且无重排事件；
3. `tests/worker/test_worker_renew_loop.py`：处理一个作业后续租**非零**且携带被持有的身份三元组；
   无作业时零。

## 为什么这样做

- **「各证一半」是最常见的假覆盖**：既有判据分别证了「心跳使 `expires_at` 变大」与
  「到期 + 回收 ⇒ 可再 claim」，**但两者合起来才排除**「心跳只是改了字段、回收逻辑根本不看它」
  这一形态。可靠性语义的判据必须把**因果链两端接起来**（延长 → 不被回收 → 停跳 → 按新期限回收）。
- **纯函数采样不等于轨迹**：退避正确性只在纯函数层采三点，**不能**证明引擎把同一个数落进了
  `retry_at`（两个适配器各自算就会漂移）。判据要读**存储行**并施加**单调性 + 上界 + 增长**三条。
- **计数器从不被断言 = 未取证**：`_FakeClient.renews` 存在但无人断言非零
  ⇒ 「续租线程真的跑了」从未被证。**存在一个计数器不是判据**。
- **分类必须绑结构化字段**：`FailureCategory` / 任务状态 / `EventType` 是结构化面，
  错误文本是散文面 —— 后者会被措辞改动骗过（承 MEM-141）。

## 怎么做与复现

1. 时钟缝：`SqliteWorkflowEngine(lease_ttl_seconds=60, now=<mutable clock>)`；到期用
   `clock.advance(...)` + `recover_expired_leases()` 计数确定性观测，**不 sleep**。
2. 轨迹：SQL 字面量直送 `execute` 读 `tasks.retry_at`，`parse_iso` 解析后与时钟值相减；
   每次失败后 `clock.advance(seconds=gap)` 走过窗口再 claim。
3. 续租：`_RecordingClient` 记录 `renew(task_id, lease_id, fence)`；用**有界等待**（≤5s）
   等守护线程首次续租。
4. 命令：`uv run --frozen --no-sync python -B -m pytest
   tests/adapters/sqlite/test_workflow_lease_lifecycle.py
   tests/adapters/sqlite/test_workflow_retry_trajectory.py
   tests/worker/test_worker_renew_loop.py -q`（**7 passed**）。
5. 按压：产品级改 `packages/domain/tasks.py` 的 `retry_delay`（常量）与 `decide_failure`
   （去掉不可重试规则）⇒ 各判红；raw `sha256` 复原回
   `358800b68ccb9fcb81313c1dec74942401ea777e9048fe24ba0428419c6a0106`。

## 适用边界

- 确定性判据落在 **SQLite**：PG 的 `server_now` 让假时钟无法推进 ⇒ PG 侧只能改行 / 真跑；
- **分布式 / 跨进程**租约场景不在射程；
- 续租判据用有界等待（守护线程 + 瞬时作业），极端负载下有**极小**假红窗口；
- 实测到的适配器分歧（`heartbeat` / SQLite `complete` 不校验过期）**只登记**，不改产品；
- `Timestamp` 是 dataclass 包装、**不支持排序比较** ⇒ 比较 `.value`（这是本轮判据自己踩到的坑）。

## 来源

- `PLAN-20260929-247`（GOAL-026 EC-02）与 `RECHECK-20260929-248`；
- 实跑留档：`scratch/goal026-ec02-press-matrix.log`（二进制写盘 / `CR` 计数 0）；
- 相关判据：`tests/adapters/sqlite/test_workflow_lease_lifecycle.py`、
  `tests/adapters/sqlite/test_workflow_retry_trajectory.py`、
  `tests/worker/test_worker_renew_loop.py`。
