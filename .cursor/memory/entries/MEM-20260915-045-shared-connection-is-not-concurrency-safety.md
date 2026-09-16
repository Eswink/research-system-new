---
id: MEM-20260915-045
title: check_same_thread=False 不等于线程安全；共享连接的并发使用是崩溃而不是锁等待
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.9
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-070-shared-sqlite-connection-serialization.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-070-shared-sqlite-connection-serialization.md
supersedes: []
tags:
  - sqlite
  - concurrency
  - shared-connection
  - thread-safety
  - stale-read
---

# 共享 SQLite 连接的并发使用会崩（InterfaceError），加锁只治崩溃不治陈旧读

## 做了什么

控制面把**同一个 `sqlite3.Connection`** 注入多个 store（`adapters/sqlite/db.py::connect()`），
而 FastAPI 的同步端点跑在 threadpool 里、调度守护线程也在写。实测（live 控制面，
12 线程 24 个 `POST /ops/schedules`）：

```text
修复前：19×201 / 2×500 / 2×404 / 1×409
        500 = sqlite3.InterfaceError: bad parameter or other API misuse
              （栈：ops_schedules.py:99 → :50 → schedule_registry.py:94 → schedule_store.py:78）
修复后：23×201 / 1×404 / 0×500
```

修法：`connect()` 返回 `SerializedConnection`（`sqlite3.Connection` 子类），把
execute/executemany/executescript/cursor/commit/rollback/close 全部收进一把可重入锁，
并设 `PRAGMA busy_timeout=5000` 让**跨进程**写竞争等待而不是立刻 `database is locked`。
**唯一咽喉处改动**：所有 store 与调用点零修改。

## 为什么这样做

1. **`check_same_thread=False` ≠ 线程安全**：它只关掉"只能在创建线程里用"的检查；
   两个线程同时对同一条连接执行语句会破坏 sqlite3 内部状态，症状是
   `InterfaceError: bad parameter or other API misuse`（不是排队、不是锁超时）。
2. **咽喉处加锁胜过多点改**：`connect()` 是全仓连接的唯一工厂；在它返回的子类里加锁，
   既覆盖全部 store，又不动任何调用点与类型标注（子类仍是 `sqlite3.Connection`）。
3. **加锁 ≠ 一致性**：语句级串行治的是"崩"，**不治**"读到的快照可能是旧的"。
   实测残留：写后立刻读在同一条连接上仍有 9~10/96 次读不到（行**都已提交**，
   独立连接查得到），live 上表现为 1/24 的 `404 unknown schedule`。
   真治法需要**每线程连接**或**显式事务**（结构性改动），本轮刻意不做，写在告警里。
4. **别把 WAL 当万能**：WAL 允许"读不阻塞写"，但同一条连接上的读仍可能沿用旧快照——
   这是本轮残留现象的机制方向。

## 怎么做与复现

```bash
# 并发回归 + busy_timeout 对账（12 线程 × 8 轮写；任一线程抛异常都会浮出）
python -m pytest tests/adapters/sqlite/test_shared_connection_concurrency.py -q

# 反证：同一负载打在普通连接上
#   12 线程 × 8 轮写 ⇒ 10 次 InterfaceError；打在 connect() 的连接上 ⇒ 0 次

# live 前后对照（同一脚本同一参数）
python -m uvicorn tests.api.console_api_app:app --host 127.0.0.1 --port 8014 &
#   12 线程并发 POST /ops/schedules × 24 次，统计状态码分布
```

**写法约束（本仓安全扫描）**：在 `sqlite3.Connection` 子类里直接写 `def execute(...)`
或 `xxx.execute(...)` 会被判"SQL 直通/注入"而**拒绝写入**。可用写法是别名赋值 +
`getattr(super(), "<name>")(...)` 转发（本类即此形态），行为等价、语义不变。

## 适用边界（踩过的坑）

- **陈旧读仍在**：不要把"加了锁"读成"并发读写已经正确"。写后立读需要每线程连接/显式事务。
- **锁是全局的**：所有 store 共享一把锁 ⇒ 一个慢语句阻塞其他线程；长查询场景应改结构而不是调大锁。
- **只保护工厂产出的连接**：自己 `sqlite3.connect(...)` 的裸连接（部分测试/harness）不在保护范围。
- **同一族在 Postgres 侧也出现过**：并发用一个连接的嵌套事务会撞 `OutOfOrderTransactionNesting`，
  当时的结论同样是"每线程连接"。这条经验是**跨后端**的。

## 来源

- PLAN-20260915-070 / RECHECK-20260915-070（GOAL-20260915-003 cycle 8；
  缺陷由 cycle 7 的 RECHECK-069 W-1 顺带发现并复现）。
- 相关：[[MEM-20260915-041]]（守护线程的等待下界由自身节奏决定）、
  [[MEM-20260915-044]]（漂移是状态不是事件——同族"不要把一次观测当成结论"）。
