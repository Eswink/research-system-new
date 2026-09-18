---
id: MEM-20260918-073
title: "组合读面必须一条语句取齐两件事实——快照一致性靠语句，不靠文档"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.9
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260918-100-dispatch-read-single-snapshot.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260918-100-dispatch-read-single-snapshot.md
supersedes: []
tags:
  - read-surface
  - snapshot-consistency
  - ports
  - sql
  - test-determinism
---

# 组合读面：一条语句取齐，快照靠语句本身

## 做了什么

GOAL-006 cycle 1（EC-01）把 `dispatch_ownership` 的**撕裂读**清掉：此前"重排读面 + 活租约"
由**两条独立 SQL** 取出再组合成 `kind`，而 PG 连接是 `autocommit=True`（每条语句各取快照）、
SQLite 的 `SerializedConnection` 只保证**单条语句**自洽（`adapters/sqlite/db.py` 逐字写明）
⇒ 并发写落在两条语句之间时，`kind` 会把**不同时刻**的两件事实拼在一起（例如重排面已前移、
租约面仍是旧值）。

现在两个方言都用**一条语句**取两件事实：`UNION ALL` + 判别列 `kind`（`'RETRY'` / `'LEASE'`），
`_dispatch_facts` / `_FACTS_SQL` 是唯一取数点；`retry_schedules`、`live_lease_holders_many`、
`dispatch_ownership_many` 三个入口从**同一份 facts**各取所需（判据只有一处）。一致性交给
**语句快照**本身——不动隔离级别、不加显式事务。

## 为什么这样做

- **两次读 + 文档免责 = 没解决**：RECHECK-097 W-1 声称"port docstring 与 `PORTS.md` 已写明
  不承诺快照一致"——树上当时**没有这句**（只有"每次调用两条 SQL"）。文档写"我不保证"既不
  改变行为、也不给调用方任何可依赖的东西。要么实现、要么 ADR 级论证，二者必居其一。
- **单语句是"零成本"的一致性**：`READ COMMITTED` 下事务内两条语句仍各取快照（要
  `REPEATABLE READ` 才是快照隔离）⇒ "包一个事务"并不能解决问题；一条语句才天然同刻。
- **同源取数顺带消灭漂移**：三个入口共用一条 SQL 文本，"单 run 读 = 批量读的一条"从
  "两处各写一遍、行为对齐"升级为"同一段代码"。

## 怎么做与复现

判据是**确定性**的（不靠线程调度）：连接代理数语句，并在**第一条语句返回之后**用
**另一条连接**注入一次只影响一面的写（把租约改成过期），然后断言三件事：

```bash
# 两方言各一条探针用例（头两条断言 = 语义，第三条 = 结构）
uv run --frozen --no-sync python -B -m pytest tests/adapters/sqlite/test_dispatch_read_snapshot.py -q
RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os \
  uv run --frozen --no-sync python -B -m pytest tests/postgres/test_dispatch_read_snapshot_pg.py -q
# 反证：把取数拆回两条独立语句 ⇒ 期望红（`2 == 1`，且语义 `'RETRY_DISPATCH' == 'BOTH'`）
```

1. 答案仍是**调用开始时**的快照（`kind == BOTH` + 持有者在列）；
2. **注入的写确实生效**（事后新引擎读得到写后状态）——否则第 1 条没有判别力；
3. `probe.count == 1`（一次调用一条语句）。

## 适用边界（踩过的坑）

- **这是语句级一致，不是事务级**：`now` 的解析在生产路径（无注入时钟）是**另一条语句**
  （`SELECT now()`），与取数语句不同刻（毫秒窗口）。既有"写入与比较同一个时钟源"的纪律
  覆盖这一点，别把本条读作"整个调用原子"。
- **Fake 不适用该判据**：Fake 没有语句面，一致性来自"同一段装配在同一次 Python 调用内"，
  且**无**并发写保护 ⇒ 探针只能钉两个持久化方言；Fake 的弱化是显式边界。
- **单面调用会多读一面**：`retry_schedule` / `live_lease_holders` 现在也取另一面的行
  （行数由 `run_id` 集合界住）。换来"判据只有一处 + 同一快照"；将来若出现热路径调用，
  要重新评估而不是无脑拆回去。
- **UNION ALL 要 ORDER BY 收口**：旧实现靠 `ORDER BY t.run_id, l.task_id` 保证持有者顺序；
  单语句版必须在外层补 `ORDER BY kind, run_id, task_id`，否则持有者顺序不保证、同判用例
  会变成偶发红。
- **历史记录的"已写明/已修复"要复验**：这条 W 的括注不实，只有全树搜索能戳穿；
  看到"文档已写明"先去搜那句话。
- 相关：[[MEM-20260918-071]]（批量读面的同判与 N+1 哨兵）、
  [[MEM-20260918-070]]（adapter 内的权威时钟纪律）。

## 来源

- PLAN-20260918-100 / RECHECK-20260918-100（GOAL-20260918-006 cycle 1 = EC-01）。
- 上游：RECHECK-20260918-097 W-1（EC-05 ② 未做）与 GOAL-005 收口结论第 2 项。
