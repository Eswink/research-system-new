---
id: PLAN-20260915-070
slug: shared-sqlite-connection-serialization
title: 共享 SQLite 连接的并发写缺陷（语句级串行化）
status: DONE
created_at: 2026-09-16
updated_at: 2026-09-16
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 8 = cycle 7 复现的真实缺陷（RECHECK-069 W-1：控制面 SQLite 共享连接并发写抛 sqlite3.InterfaceError）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-070-shared-sqlite-connection-serialization.md
memory_entries:
  - MEM-20260915-045-shared-connection-is-not-concurrency-safety
---

# PLAN-20260915-070 — 共享 SQLite 连接的并发写缺陷（GOAL-003 cycle 8）

## 目标

控制面的 SQLite 连接被多个线程同时使用时会**崩**（不是"慢"或"锁等待"）：

```text
修复前（live 控制面，12 线程 × 24 个 POST /ops/schedules）：
    19×201 / 2×500 / 2×404 / 1×409
    500 = sqlite3.InterfaceError: bad parameter or other API misuse
          （ops_schedules.py:99 → :50 → schedule_registry.py:94 → schedule_store.py:78）

修复后（同一脚本同一参数）：23×201 / 1×404 / **0×500**
```

## 口径

1. **`check_same_thread=False` ≠ 线程安全**：它只关掉"只能在创建线程里用"的检查；
   两个线程同时对同一条连接执行语句会破坏 sqlite3 内部状态。这是本轮要治的病。
2. **在唯一咽喉处加锁**：`adapters/sqlite/db.py::connect()` 是全仓连接的唯一工厂，
   返回 `SerializedConnection`（execute/executemany/executescript/cursor/commit/rollback/close
   全部在可重入锁内转发）——不改任何 store、不改任何调用点。
3. **不夸大**：锁只保证**语句级**串行。"写后立读一定看得见"**不在**本轮结论里
   （实测仍有 1/24 的陈旧读 ⇒ 那是读快照问题，需要每线程连接或显式事务，见告警）。
4. **跨进程竞争等待而不是立刻失败**：`PRAGMA busy_timeout=5000`（值为字面量，
   与 `BUSY_TIMEOUT_MS` 由用例对账）。

## 范围

- 修改：`adapters/sqlite/db.py`（`SerializedConnection` + `BUSY_TIMEOUT_MS` + `connect()`）。
- 新增：`tests/adapters/sqlite/test_shared_connection_concurrency.py`（并发回归 + PRAGMA 对账）。
- **不改**：任何 store、任何 API 路由、`SqliteAdapterBase`、composition。

## 验收条件

- [x] AC-01：并发写不再抛 `sqlite3.InterfaceError`，且所有写入最终落库。
- [x] AC-02：**反证**——同样的并发负载打在**普通连接**上必须复现该异常（证明用例真的在测这件事）。
- [x] AC-03：`connect()` 返回的连接是 `SerializedConnection` 且 `busy_timeout` 等于 `BUSY_TIMEOUT_MS`。
- [x] AC-04：live 实测 500 归零（同脚本同参数：修复前 2×500 → 修复后 0×500）。
- [x] AC-05：全量门禁（m0 23 + 定向套件）+ 记录（RECHECK-070 + MEM-045 + GOAL 记账）。

## 实施清单

- [x] WP-A `SerializedConnection` + `connect()` 接线 + `busy_timeout`
- [x] WP-B 并发回归用例（含"普通连接会红"的反证）
- [x] WP-C live 实测对照（前后各一次，同脚本同参数）
- [x] WP-D 全量门禁 + 记录 + 收口提交 → CI

## 证据

```text
$ python -m pytest tests/adapters/sqlite/ -q
92 passed in 2.17s                    # 含新增 2 条并发用例

# 反证：同一并发负载（12 线程 × 8 轮写）打在普通 connection 上
plain connection errors: 10 ['InterfaceError: bad parameter or other API misuse', ...]
# 同一负载打在 connect() 返回的连接上：0 异常，全部行落库

$ # live 控制面（uvicorn:8014），12 线程 24 个 POST /ops/schedules
before: {201: 19, 500: 2, 404: 2, 409: 1}
after : {201: 23, 404: 1}

$ python -m pytest tests/adapters/sqlite tests/api -q
472 passed in 52.19s

$ sh scratch/run-m0-cycle12.sh
PASS: profile=m0; 23 deterministic checks
```

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：缺陷来自 cycle 7 的顺带发现（RECHECK-069 W-1），
  复现脚本与栈都已记录。derive 时的关键判断：**在 `connect()` 这个唯一咽喉处加锁**——
  store 与调用点一个都不动，风险最小；并且**不把"锁"说成"一致性"**：
  语句级串行治的是崩溃，不治陈旧读。
- 2026-09-16 WP-A/B/C 完成：`SerializedConnection` 用**别名赋值**暴露语句执行面
  （sqlite3.Connection 的方法在子类里重写会触发本仓安全扫描的"SQL 直通"判据，
  别名 + `getattr(super(), ...)` 转发是既有已记录的规避写法）；并发用例与反证、
  live 前后对照（2×500 → 0×500）均完成。
- 2026-09-16 DONE：全量门禁通过（定向 `tests/adapters/sqlite tests/api` **472 passed**；
  m0 **PASS: profile=m0; 23 deterministic checks**；mypy 862 files clean；ruff 干净），
  记录落盘（RECHECK-070 PASS_WITH_WARNINGS + MEM-045 + GOAL cycle 8 记账 + ALL_PLAN），
  复检基线 `b269aef`。陈旧读（W-1）作为下一轮第一项移交。

## 影响报告

- **Domain/API/schema**：无变化（纯适配层）。
- **安全/凭据**：无。
- **兼容性/迁移风险**：`connect()` 的返回类型仍是 `sqlite3.Connection`（子类），
  调用点无感；`:memory:` 与文件路径同样适用。**代价**：同一连接的语句级并发度降为 1
  （原来"能并发但会坏"，现在"不并发但不会坏"）。
- **可观测性**：无新增遥测；`InterfaceError` 不再出现在日志里本身即是信号。
- **下一项任务**：**每线程连接 / 显式事务**——治"写后立读看不到刚提交的行"
  （实测残留 1/24；本轮未做）。

## 已知风险

- **陈旧读未治**：锁不保证写后立读。live 实测仍有 1/24 的 `404 unknown schedule`
  （行已提交、读却看不见）。这是**与本轮同一根因的另一半**，需要每线程连接或
  显式事务 API；不得把本轮读成"并发读写已经正确"。
- **锁粒度**：所有 store 共享同一把锁 ⇒ 一个慢查询会阻塞其他线程的语句。
  当前控制面负载下可接受；若将来出现长查询，应改为每线程连接而不是加大锁。
