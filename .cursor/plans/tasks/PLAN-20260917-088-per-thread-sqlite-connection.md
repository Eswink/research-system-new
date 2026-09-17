---
id: PLAN-20260917-088
slug: per-thread-sqlite-connection
title: 控制面 SQLite 锁粒度落到每线程连接（EC-05 第①半：共享连接不再被跨线程使用）
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260917-004
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260917-004 cycle 5 = EC-05 第①半（后继入口第 6 项的前半）。授权来源：2026-09-17 用户 goal 模式指令（新建承接 GOAL-004 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260917-088-per-thread-sqlite-connection.md
memory_entries:
  - MEM-20260917-063
---

# PLAN-20260917-088 — 每线程 SQLite 连接（GOAL-004 cycle 5 = EC-05 第①半）

## 目标

控制面把**一个** `SerializedConnection` 注入 ~30 个 store，而 FastAPI 的同步端点跑在
threadpool 里、五个守护线程也在写。`SerializedConnection`（PLAN-20260915-070/076）用一把
可重入锁把语句级与事务级串行化，**但共享连接仍被跨线程使用**：`check_same_thread=False`
只关掉了检查，任何绕过锁的入口都会破坏连接状态（cycle 7 实测 `sqlite3.InterfaceError`
⇒ 2×500），"写后立读"的可见性也始终挂着一条告警（RECHECK-070）。

本轮把锁粒度落到**每条线程一条连接**：控制面拿到的不再是一条连接，而是
`ThreadLocalConnection`——对外仍是一个连接对象（store 代码零改动），对内每条线程懒开
自己的一条（WAL + `busy_timeout`，与 `db.connect` 同一套参数）。

**范围**：EC-05 的另一半（worker claim 与 retry dispatch 的**统一派发读面**）不在本 PLAN，
留待下一 cycle 的 PLAN-089——本 PLAN 独立可验收（"共享连接不再被跨线程使用"本身可证伪）。

## 口径

1. **代理面，不改 store**：连接上除 `with` 块与 `row_factory` 写回之外的一切入口
   （语句、游标、事务边界、pragma）都由 `__getattr__` 转发到本线程连接；
   `with conn:` = 本线程连接的事务块（与 sqlite3 语义一致）。
2. **`:memory:` 例外要明说**：SQLite 的内存库**属于连接**，每线程一条会各自看到空库
   ⇒ 这种路径共用一条（`db.connect` 原行为）。它是测试夹具的默认路径，所以必须显式钉住，
   不能伪装成"每线程"。
3. **关闭是"关全部"**：`close_all()` 关闭登记过的每条连接（应用 shutdown 走它）；
   `close()` 仍按 sqlite3 语义只关本线程那条。
4. **判据只增强**：既有 `SerializedConnection` 的边界/事务/游标/并发用例原样保留
   （它们测的是那个类本身），新增池单测与 API 负载用例。

## 验收条件

- [x] AC-01 **真的每线程一条**：池单测（文件库）——两个线程拿到的连接对象不同、
  懒创建、连接数随**线程**数增长（`connection_count()`），不是每次请求一条。
- [x] AC-02 **写可见性**：线程内写后立读；另一线程提交后可见（WAL，不靠一把大锁）。
- [x] AC-03 **并发负载干净**：12 线程 × 24 次 `POST /ops/schedules` 在**文件库**路径
  全 201、无 5xx、无 404，且 24 条都从读面列得出来；`:memory:` 路径同负载同样干净
  （基线对照，证明代理面没把原语义改坏）。
- [x] AC-04 **兼容面**：整库 API 套件（420 例，夹具统一走池）全绿；`with conn:` 事务、
  `row_factory`、`executescript` 面由池单测覆盖；mypy 911 files 绿、ruff 绿。
- [x] AC-05 **边界与收口**：`:memory:` 共用一条被显式钉住（含 `is_memory_path` 判据）；
  `close_all()` 幂等且覆盖全部登记连接；文档（`docs/architecture/PORTS.md` 或 sqlite 段）
  与 `CONTROL_PLANE_API.md` 口径同步；m0 23 项 + 受影响套件 + live e2e + RECHECK-088 +
  MEM-063 + GOAL/ALL_PLAN 记账。

## 实施清单

- [x] WP-A **测量**：复现 cycle 7 的 12 线程/24 次登记场景（hermetic 版）并记录基线分布
  （`:memory:` 夹具下 24×201、无 5xx、无 404 —— 与 live 探针的历史分布不同，如实记录）。
- [x] WP-B **每线程连接**：`adapters/sqlite/pool.py`（`ThreadLocalConnection` + `is_memory_path`）、
  `_open_sqlite` 返回池、`ApiDeps.close()` 走 `close_all()`、测试夹具统一走池
  （`:memory:` 退化为共用一条）+ 池单测 5 条 + 文件库负载用例 1 条。
- [x] WP-C **收口**：定向 + m0 + live e2e + RECHECK-088 + MEM-063 + GOAL/ALL_PLAN 回写。

## 证据

- 提交：`64d668a`（池 + 装配 + 夹具 + 5 条池单测 + 2 条负载用例）、`121246c`（拆分提交：`tests/api/base_fixtures.py`，修 50 行/函数门禁）。
- 定向：`tests/adapters/sqlite/test_thread_local_connection.py` **5 passed**；
  `tests/api/test_ops_schedules_concurrency_api.py` **2 passed**（内存/文件两路径）；
  `tests/api` 全量 **420 passed**；`tests/adapters/sqlite tests/application tests/contracts
  tests/e2e tests/postgres` 复跑 **1371 passed / 4 skipped**（213.47s）；mypy **911 files** 绿；
  live e2e **36 passed**（真 app + 文件库路径）。
- m0：**PASS: profile=m0; 23 deterministic checks**（全量 pytest **3846 passed / 10 skipped**，
  510.93s）。首跑红 1 处 = `conftest.make_base_deps` 54 行（本改动引入）⇒ 拆出
  `tests/api/base_fixtures.py` 后复跑全绿（门禁未改）。
- 记录：RECHECK-20260917-088（PASS_WITH_WARNINGS，W-1…W-4）+ MEM-20260917-063。

## 状态历史

- 2026-09-17 建档（GOAL-20260917-004 cycle 5 = EC-05 第①半）；`status: IN_PROGRESS`。
- 2026-09-17 收口：WP-A/WP-B/WP-C 完成；池单测 5 + 负载 2 + 全量 API 420 + 定向 1371
  全绿；live e2e 36 绿；RECHECK-088 PASS_WITH_WARNINGS；`status: DONE`。

## 影响报告

- **Domain**：无变化。
- **API/schema**：无新端点、无 DTO 变化（代理面对 HTTP 面透明）。
- **持久化**：连接布局变化（文件库每线程一条）——**无 schema/迁移**；WAL 与 `busy_timeout`
  参数与 `db.connect` 一致；`:memory:` 行为逐字不变。
- **安全/凭据**：无新面（连接路径与参数不变）。
- **兼容性/迁移风险**：`with conn:` 的语义从"全局锁住的块"变成"本线程事务块"——并发写
  由 SQLite 的 WAL 写锁 + `busy_timeout` 协调；`SerializedConnection` 本身与其用例不变，
  仍服务于"必须共用一条连接"的场景（`:memory:`、单连接工具路径）。
- **上游版本影响**：无新依赖。
