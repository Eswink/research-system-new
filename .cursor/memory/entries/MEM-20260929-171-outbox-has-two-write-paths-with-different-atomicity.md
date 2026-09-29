---
id: MEM-20260929-171
title: "发件箱有两条写路径且原子性不同：引擎 `OutboxWriter` 写调用方事务（all-or-nothing），发布器 `publish` 自提交（后续失败带不走它）；注释说的相反，靠失败注入才量出来"
status: ACTIVE
created_at: 2026-09-29
updated_at: 2026-09-29
scope: repository
confidence: 0.9
review_after: 2027-03-29
source_plans:
  - .cursor/plans/tasks/PLAN-20260929-251-goal-026-ec04-compensation-and-transactional-outbox.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260929-252-goal-026-ec04-compensation-and-transactional-outbox.md
supersedes: []
tags: [outbox, atomicity, failure-injection, sqlite, goal-026, ec-04]
---

## 做了什么

GOAL-026 EC-04 用**失败注入**量出两条 outbox 写路径的原子性**不同**，并因此更正了一处
**与实测相反**的注释：

- **引擎路径** `adapters/sqlite/outbox.py::OutboxWriter.publish`：写**调用方事务**内
  ⇒ 同一提交块内的事件写失败会让租约行 / 任务状态**一起回滚**（实测
  `counts = (0, 0, 1)`、状态仍 `QUEUED`；正控制 `(1, 1, 1)` / `LEASED`）。
- **发布器路径** `adapters/sqlite/event_publisher.py::SqliteOutboxEventPublisher.publish`：
  `with self._conn:` **自提交** ⇒ 自提交之后，同一调用块内的**后续失败不会把它带走**
  （实测：同连接与第二连接都看得见那一行）。
- 该文件旧注释（PA-1 F7 段）声称后者「会把事件一起回滚」⇒ 按实测**只改注释**（零行为变更）。

## 为什么这样做

- **注释不是契约，判据才是**：这处错误说法在仓里存在了很久，且**被下游文档复述**
  （既有判据文件的模块 docstring 也这么写）。只有**失败注入**能区分「写在同一事务里」
  与「先提交、再继续」——全绿路径对两者完全无感。
- **同一能力的两个入口可能语义不同**：`OutboxWriter` 与 `publish` 都叫「发事件」，
  但一个在调用方事务内、一个自提交。「用了 outbox」**不等于**「拿到了事务性 outbox」——
  问原子性必须问到**具体入口**。
- **自提交是取舍不是缺陷**：PA-1 F7 选它是为了**耐久性 + 跨连接可见**（崩溃不丢、API 重启能读到）。
  代价就是「后续失败带不走它」。因此处置是**改说法 + 把两条路径的差异写进判据**，
  而不是把自提交改掉（那会退掉 F7 的收益）。

## 怎么做与复现

1. **注入**用 SQLite **授权回调**（`conn.set_authorizer(cb)`，命中 `SQLITE_INSERT` +
   表名 `outbox_events` 即返回 `SQLITE_DENY`）——**不拼任何 SQL 文本**，也不改产品代码。
2. 注入点放在提交块的**最后一条语句**上（`persist_new_lease`：租约 → 任务状态 → 发事件），
   这样「业务事实是否跟着回滚」才是真问题。
3. 断言三件事：故障**真的触发过**（`denied == 1`）、三张表**计数**、任务**状态串**；
   再加一条「回滚后还能重新 claim」证明失败的尝试**不留毒**。
4. 命令：`uv run --frozen --no-sync python -B -m pytest
   tests/adapters/sqlite/test_outbox_atomicity.py -q` ⇒ **5 passed**。
5. 按压（把事件挪出业务事务）：在 `outbox.publish` 前加 `conn.commit()` ⇒ 判据红
   （`AssertionError: 事件写失败后不得留下租约行或事件行`）；raw `sha256` 复原回
   `e5a21a8cc5271e69fe0946608bd0c4df4a62cac45f89833279c431196e64c490`。

## 适用边界

- 结论落在 **SQLite** 适配器与 **claim 路径**；`submit` / `complete` 路径与 **PG 侧**
  未做失败注入（PG 侧既有判据仍只在全绿路径）。
- 注入是**授权回调级**（拒写表），不是真实磁盘满 / 提交冲突；它证明的是「同一事务边界内
  会一起回滚」，不是「所有故障形态都不会留下半条」。
- 仓内**没有**应用级事件消费者 ⇒ 本记忆只覆盖**存储面**，消费端去重未取证。
- 既有判据文件 `tests/adapters/sqlite/test_event_publisher.py` 的 docstring 仍复述旧说法
  （本 GOAL 不改既有判据 ⇒ 只登记）；读口径以判据与 `RECHECK-20260929-252` 为准。

## 来源

- `PLAN-20260929-251`（GOAL-026 EC-04）与 `RECHECK-20260929-252`（§1 / §2 / §6）；
- 事前探针与按压留档：`scratch/goal026_ec04_probe.py`、
  `scratch/goal026-ec04-press-matrix.log`（二进制写盘 / `CR` 计数 0）；
- 相关代码：`adapters/sqlite/outbox.py`、`adapters/sqlite/event_publisher.py`、
  `adapters/sqlite/workflow_claim.py`；
- 同族记忆：[[MEM-20260929-170]]（吞掉迁移异常 = fail-open：同属「代码说法 vs 实测行为」）。
