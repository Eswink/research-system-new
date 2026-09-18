---
id: MEM-20260918-070
title: "PG 用例的时钟判定：注入时钟与数据库时钟只有一处源，判据要落在写入路径上"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.9
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260918-096-clock-injection-adjudication.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260918-096-clock-injection-adjudication.md
supersedes: []
tags:
  - postgres
  - clock
  - test-determinism
  - evidence
---

# 时钟注入纪律与 12 个 PG 用例文件的判定

## 做了什么

GOAL-005 cycle 4（EC-04）把 RECHECK-084 W-5 的残留（"12 个注入时钟的 PG 用例文件只
grep 排查过、当时只修了 1 个"）收口：新增只读探针
`tools/probes/enumerate_clock_injected_pg_tests.py`（AST + 行扫描，输出每个文件的注入行、
墙钟读、**无时钟构造点**、时间断言），据其输出把 **12 个文件逐个判定为「安全」**，
依据落在**写入路径**上（谁写这一列、谁读它、断言比较什么）。同源纪律写进
`docs/architecture/PORTS.md` 的「时钟注入纪律」段。

## 为什么这样做

- **时钟纪律本身是"一个源"**：`adapters/postgres/db.py` 的 `db_time_expr(now)`（SQL 片段：
  生产 `now()` / 测试绑定参数）与 `server_now(conn, now)`（Python 侧比较：生产
  `SELECT now()` / 测试注入）**同时**用于写时钟敏感列（`leases.expires_at` /
  `heartbeat_at` / `tasks.retry_at`）与做判据比较 ⇒ 注入时钟的用例不会一半按假时钟、
  一半按数据库时钟。
- **唯一例外是已知且无害的**：AST 扫描 `adapters/postgres/*.py` 的字符串字面量，
  唯一**无条件** `now()` 是 `outbox.py` 的 `outbox_events.created_at`（事件行时间戳）；
  相关断言只按事件**类型成员**（`EventType.X in kinds`），没有断言它的取值或排序。
- **"跑一次没红"不是依据**：判定必须能独立复核——例如
  `next_retry_at == START + 3600` 之所以安全，是因为它由
  `projections.retry_schedule(server_now)` 产生；这一条同时也是一条**哨兵**：哪天改成
  SQL `now()`，该断言就会红。
- **6 个文件含"无时钟构造点"不等于风险**：`now` 也可能是**方法参数**
  （`PostgresExperimentStore.claim_due_entry(now=...)`）或该分支**没有调用点**
  （parity 的 `_engine(kind, now=None)`）——所以要看用到它的**用例断言什么**。

## 怎么做与复现

```bash
uv run --frozen --no-sync python -B tools/probes/enumerate_clock_injected_pg_tests.py
# ⇒ postgres test files: 27 / clock-injected files: 12 / wall-clock reads: 0 /
#   clockless constructors: 6（6 个文件逐个核对过用例断言）
RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os \
  uv run --frozen --no-sync python -B -m pytest tests/postgres -q     # ⇒ 91 passed
# 全局结构依据（AST，字符串字面量里的 now()）
uv run --frozen --no-sync python -B -c "<扫 adapters/postgres/*.py 的 ast.Constant>"
grep -rn "now()" tests/postgres/*.py    # ⇒ 只剩一行文档字符串
```

## 适用边界（踩过的坑）

- **枚举面 = `tests/postgres/` 下注入时钟的文件**；`test_cross_process_real.py`
  （真墙钟 TTL + 硬 kill，`pytest.mark.timing_sensitive`，等待用有界轮询）**有意**在外，
  本轮判定不覆盖它，也不能读成"时序风险已清空"。
- **一条调度依赖断言**：`test_claim_concurrency_pg.py` 的
  `sum(... >= 2)`（"并发是真的"）依赖线程调度（barrier + 引擎先建好是结构缓解）；
  若在极端负载下变红，改成"进入领循环的线程计数"，不要删断言。
- **WorkerRegistry 生产用 DB 时钟**（`_time_expr()` 已可注入），用它但不断言时间的用例安全；
  将来要断言其时间就得注入。
- 相关：[[MEM-20260917-063]]（per-thread 连接与代理面，同类 PG 测试基础设施）、
  [[m17-partb-review-findings]]（真墙钟矩阵的 flaky 修复与 `timing_sensitive` marker）。

## 来源

- PLAN-20260918-096 / RECHECK-20260918-096（GOAL-20260918-005 cycle 4 = EC-04）。
- 上游：RECHECK-20260917-084 W-5（只 grep 排查的残留）。
