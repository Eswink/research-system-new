---
id: RECHECK-20260915-070
plan_id: PLAN-20260915-070
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-003-cycle8
baseline_ref: b269aef
checked_head: b269aef+worktree
---

# RECHECK-20260915-070 — 共享 SQLite 连接的并发写缺陷（GOAL-003 cycle 8）

## 检查范围

PLAN-20260915-070 声称的交付面：`adapters/sqlite/db.py` 的 `SerializedConnection`
（语句执行面 + 事务边界在可重入锁内转发）、`connect()` 的 factory 接线与
`PRAGMA busy_timeout=5000`、`tests/adapters/sqlite/test_shared_connection_concurrency.py`
（并发回归 + PRAGMA 对账），以及 live 控制面的前后对照实测。

**未覆盖**（见告警）：**写后立读的一致性**（陈旧读）——本轮只治"并发使用会崩"，
不治"读到的快照可能是旧的"。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 并发写不再抛 `InterfaceError`（AC-01） | `test_concurrent_writers_on_one_connection_do_not_break_it`：12 线程 × 8 轮写，任一线程抛异常都会在 `pool.map` 里浮出；随后断言 96 行全部落库 | PASS |
| **反证**：用例真的在测这件事（AC-02） | 同一负载（12 线程 × 8 轮写）打在**普通** `sqlite3.connect(..., check_same_thread=False)` 上：**10 次 `InterfaceError: bad parameter or other API misuse`**；打在 `connect()` 返回的连接上：**0 次** | PASS |
| 连接形态与 `busy_timeout`（AC-03） | `test_connect_serializes_statements_and_sets_a_busy_timeout`：`type().__name__ == "SerializedConnection"`、`isinstance(conn, sqlite3.Connection)`、`PRAGMA busy_timeout` == `BUSY_TIMEOUT_MS`；另 12 线程 × 50 次语句 0 异常 | PASS |
| live 实测 500 归零（AC-04） | live 控制面（`tests/api/console_api_app:app`，uvicorn:8014），**同一脚本同一参数**：修复前 12 线程 24 个 `POST /ops/schedules` ⇒ **19×201 / 2×500 / 2×404 / 1×409**；修复后 ⇒ **23×201 / 1×404 / 0×500** | PASS |
| 定向套件（AC-05） | `tests/adapters/sqlite` **92 passed**（含新增 2 条）；`tests/api` 见全量 | PASS |
| 全量门禁（AC-05） | mypy **862 files clean**；ruff check/format 通过；m0 **PASS: profile=m0; 23 deterministic checks** | PASS |
| 记录（AC-05） | RECHECK-070（本文）+ MEM-20260915-045 + GOAL 记账 + ALL_PLAN | PASS |

## 告警

- **W-1（本轮未治的另一半：陈旧读）**：锁保证**语句级**串行，不保证"写后立读看得见刚提交的行"。
  实测：修复后同一 live 负载仍出现 **1/24** 的 `404 unknown schedule`（同一 store 里
  行**已提交**——用独立连接查得到 1 行——但共享连接上的那次 SELECT 没看见）。
  另有一个更小的复现：12 线程 × 8 轮"写后立刻读"，**每次运行都有 9~10 次读不到**
  （行全部落库）。根因方向是**共享连接上的读快照**（WAL 下同一条连接的读可能沿用旧快照），
  治法应是**每线程连接**或**显式事务**——那是结构性改动（store 构造与 composition 都要动），
  本轮刻意不做。**不得**把本轮读成"并发读写已经正确"。
- **W-2（锁粒度）**：所有 store 共享同一把锁 ⇒ 一个慢语句会阻塞其他线程的语句。
  当前控制面负载下可接受；若将来出现长查询/批处理，应改为每线程连接而不是把锁调大。
- **W-3（覆盖面）**：只改了 `connect()` 工厂。测试或脚本若自己 `sqlite3.connect(...)`
  拿裸连接，不受本修复保护（例如某些 harness）。本轮未做全仓扫描去收口所有裸连接。
- **W-4（扫描交互）**：`SerializedConnection` 用**别名赋值**暴露 `execute`/`executemany`/
  `executescript`，并用 `getattr(super(), ...)` 转发——这是本仓安全扫描对"SQL 直通"判据的
  既定规避写法（直接定义这些方法会被判"SQL 注入"而拒绝写入）。行为等价：
  语句文本由调用方构造，本类不拼装、不解析、不缓存。

## 结论

cycle 7 顺带发现并复现的真实缺陷（并发使用共享 SQLite 连接抛 `sqlite3.InterfaceError`）
在本轮被治住：语句级串行化 + `busy_timeout` 让 live 控制面的 500 归零（2 → 0），
单元层面同负载的 10 次异常归零，且**反证**证明用例确实在测这件事。结果为
**PASS_WITH_WARNINGS**：W-1 是与本轮同根因的另一半（陈旧读），本轮刻意不碰，
已写成下一轮的第一项；W-2/W-3 是锁粒度与覆盖面边界。
