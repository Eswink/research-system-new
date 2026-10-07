---
id: RECHECK-20261007-306
slug: goal-032-ec02-outbox-relay-evidence
title: 复检：GOAL-032 EC-02 `R26-5` 取证追认（relay 四判据 + 启用面两向 + 两向反证 + 记录更正只追加）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-07
updated_at: 2026-10-07
plan_id: PLAN-20261007-305
reviewer: root-agent
parent_goal: GOAL-20261007-032
verify_paths:
  - >-
    RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os
    uv run --frozen --no-sync python -B -m pytest tests/postgres/test_outbox_relay_forensics.py -q
    ⇒ 4 passed（PG 实体）
  - >-
    uv run --frozen --no-sync python -B -m pytest
    tests/architecture/python/test_outbox_relay_enablement_is_explicit.py -q ⇒ 5 passed（离线）
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261007-032 的 EC-02。**零产品改动**；**不改历史 GOAL 正文**（更正只追加）；
    口径只能是 at-least-once + idempotency + deduplication（**不得**宣称恰好一次）。
---

# RECHECK-20261007-306：GOAL-032 EC-02 `R26-5` 取证追认

## 检查结果

五条 AC 逐条实测：

1. **实现面（AC-1 前半）**：`PgOutboxRelay.run_once` 的实际语义逐行核实 ——
   `pending = engine.pending_outbox()` ⇒ 逐条 `sink.publish(envelope)` + 立即
   `engine.mark_outbox_published((envelope.event_id,))` ⇒ **每条独立 mark**（崩溃只影响
   未 mark 的那些）；backlog 度量在 drain **之后**记（M15 复审的既有修复方向正确）。
   `OutboxRelayScheduler._execute_pass` 只做 telemetry 包装，**执行体就是同一个
   `run_once`**（判据 `test_the_scheduler_wraps_the_same_relay_pass` 钉住）。
2. **启用面（AC-1 后半）**：PG 组合根**恰好一处** `True`（AST 断言）；产品根内**无扩散**
   （全根 AST 扫描）；`ApiDeps` 默认 `False` 且组合根**显式**写出；**门控两向**
   （假 ⇒ `None`；翻真 ⇒ 构造出调度器 —— 第二臂防「恒 None 的假实现」假绿）；
   `app.py` 里该字段**单一读取点**。
3. **四条判据（AC-2）**：`4 passed`（PG 实体）。读数逐条：一轮 `published == 2` 且
   pending 归零、空 outbox 第二轮 `== 0`；崩溃注入 ⇒ `published` 抛出、sink 已收 1 条、
   仍 pending 1 条 ⇒ 下一轮投递**同一条**（`event_id` 逐字相同）⇒ 才 mark；
   去重臂 ⇒ 放回同一条后 relay 确实重投（`run_once() == 1`）而 sink 交付数**仍为 1**、
   `duplicates == [event_id]`（**不是静默丢弃**）；数据臂 ⇒ 同 `event_id` 只有一行。
4. **两向反证（AC-3）**：`P1_RED 1 failed`（mark 的 UPDATE 摘掉 ⇒ pending 不归零，判据红）/
   `P2_RED 1 failed, 3 passed`（判据消费端去重摘掉 ⇒ 交付数变 2，判据红）/
   `FINAL_MATCHES_BASELINE True`。留档 `scratch/goal032-cycle2/press-matrix.log`
   （268 B、CR=0）。
5. **记录更正（AC-4）**：本 PLAN 的「事实更正」节逐条写明（登记被推翻的一半 / 仍成立的一半）；
   `git status` 对 `GOAL-20260929-026-*` **零改动**。
6. **门（AC-5）**：`ruff check` = `All checks passed!`；`ruff format --check` = 干净；
   `mypy` = `Success: no issues found in 2 source files`；**零产品改动**（`git diff --numstat`
   对 `adapters/` `services/` `packages/` 无条目）。

## 警告（如实登记）

- **`W-1`｜崩溃语义是**注入式**，不是真实进程 kill**：判据在**本进程内**模拟「publish 后、
  mark 前」那一刻（注入一个投递后抛错的 sink）。真实进程崩溃的覆盖面由既有
  `tools/probes/probe_outbox.py`（M14 一次性审计探针，场景 B/C/D，**树内但未被任何判据自动
  跑**）与 `tests/postgres/test_cross_process_real.py` 承载 —— 后者覆盖**任务面**的跨进程，
  **不是** relay 的跨进程。⇒ 「真实 kill 掉 relay 后重投」**未取证**。
- **`W-2`｜`probe_outbox.py` 自身有一处恒真断言**（本轮顺带实测）：场景 D 的
  `check("D consumers idempotent …", (len(sink1._dupes) + len(sink2._dupes)) >= 0, …)`
  —— `>= 0` 对计数**恒真**，这条 check 不判任何东西。本 RESTK 只**登记**它
  （修历史探针不在本轮范围内；它是 M14 的一次性资产、不在 m0 射程内），
  **不当作**「D 场景已验证去重」的证据。
- **`W-3`｜未启用组合根（SQLite 开发路径）的 relay 行为**：判据证的是「门控返回 `None`」
  （不假装有派发方）；它**没有**证「SQLite 路径上的事件最终谁能投递」—— 该路径的投递
  由 `SqliteOutboxEventPublisher` 的 `pending/published` 与 `/notifications`、`/runs/{id}/events`
  读面承担（既有面，不在本 EC 射程）。
- **`W-4`｜`consumer_offsets` 类消费者仍不存在**：`R26-5` 的**另一半**（按偏移量物化业务
  事实）没有被本轮推翻 —— 全仓只命中 `docs/storage/DATABASE_SCHEMA.md`。本轮**只登记**，
  不实现（属新能力 + 触碰 Canonical State 写入面）。
- **`W-5`｜PG 判据在本机不可达时 skip**：`pytestmark = pytest.mark.postgres` +
  `RESEARCHOS_REQUIRE_POSTGRES=1` 时 fail-closed（既有守卫）。**skip 不是 PASS**；
  本轮读数是**实跑**（DSN 指向本机 `localhost:15432`）。
- **`R-M1` 未收口**（不得宣称项目安全）；**投递语义仍非 exactly-once**（**明确否认**；
  口径只能是 at-least-once + idempotency + deduplication —— relay 的注释与判据都按这个口径写）。

## 结论

`PASS_WITH_WARNINGS`。五条 AC 全 PASS；`W-1`…`W-5` 如实登记。**零产品改动**；
**未**改历史 GOAL 正文（更正只追加）；**不得**宣称投递语义为「恰好一次」
（**明确否认**；口径只能是 at-least-once + idempotency + deduplication —— relay 的
投递语义正是「至少一次 + 消费端按 `event_id` 去重」，本复检按这个口径写）。
