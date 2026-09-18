---
id: PLAN-20260918-100
slug: dispatch-read-single-snapshot
title: 派发读面的一次读=一条语句=一个快照（EC-01：PG 两读快照一致性）
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-006
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-006 cycle 1 = EC-01（GOAL-005 收口结论第 2 项 / RECHECK-097 W-1：PG 两读快照一致性）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-006 并自动化循环推进、无需逐轮确认）。push-to-main-for-CI 授权沿用 GOAL-001…005 批准口径（只推 main、不 force、不重写历史、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-100-dispatch-read-single-snapshot.md
memory_entries:
  - MEM-20260918-073
---

# PLAN-20260918-100 — 派发读面的一次读 = 一条语句 = 一个快照

## 目标

GOAL-005 的 EC-05 只做了 ①（列表路径 N+1），② 未做并如实登记：`dispatch_ownership` 的
「重排投影 + 租约」是**两条独立 SQL**，两者之间不承诺快照一致 ⇒ 并发写期间可能出现
**撕裂读**（例如重排面已前移、租约面仍是旧值，`kind` 由两件来自不同时刻的事实组合）。

EC-01 要求二选一终态（实现一致读 / ADR 级论证不做）。本 PLAN 走**实现**：让
`dispatch_ownership`（与三实现的读面）做到**一次调用 = 一条语句 = 一个快照**。

### 先探明再动手（只读勘察，本 PLAN 的事实依据）

1. **撕裂读的暴露面是真实的**：`adapters/postgres/projections.py:231-232` 的
   `dispatch_ownership_many` 依次调用 `retry_schedules` 与 `live_lease_holders_many`，
   每条各自 `conn.execute` 一次；PG 侧连接是 `autocommit=True`（`adapters/postgres/db.py:257`）
   ⇒ 两条语句各自开事务、各自取快照，中间窗口对其它会话可见。
2. **SQLite 同形暴露**：`adapters/sqlite/workflow_engine.py:217-218` 同样是两次
   `conn.execute`；`SerializedConnection` 的锁与"行取尽"只保证**单条语句**的自洽
   （`adapters/sqlite/db.py:184-188` 逐字写明），语句之间别的连接可以提交。
3. **`RECHECK-097` W-1 的括注与树内事实不符**（事实更正，如实登记）：
   该 W 写「port docstring 与 `PORTS.md` 已如实写明（不承诺跨表快照一致）」，
   但全树搜索「撕裂 / 不承诺 / 快照一致 / 两次读」在
   `packages/application/ports/workflow_engine.py`、`docs/architecture/PORTS.md`、
   `docs/api/CONTROL_PLANE_API.md` 三处**都只命中「每次调用两条 SQL」这一句**
   （`PORTS.md:315`），**没有**任何"不承诺快照一致"的措辞。
   ⇒ 该边界**只存在于 RECHECK 记录里，不在契约里**；本轮把它作为"必须收敛文档面"的
   依据之一（结论：既然要动，就正面写清一次读的快照语义，而不是补一句免责）。
4. **注入点已存在**：两个引擎的构造函数都接受 `connection=`（PG：
   `workflow_engine.py:76-88`；SQLite：`sqlite3.Connection` 注入），且 PG 的
   `resolve_connection` 对外部注入的连接 `owns=False` ⇒ 探针可以包住真实连接而不改变
   所有权语义。
5. **`kind` 的组合规则在域侧**（`DispatchOwnership` 自己算）⇒ 一致性问题的唯一来源就是
   取数，不是判定；本 PLAN 不动判定。

## 口径

- **一次读 = 一条语句**：`retry_schedules` / `live_lease_holders_many` /
  `dispatch_ownership_many` 三个入口**共用同一条 SQL 文本**（`UNION ALL` 两分支 + 判别列
  `kind`），各自只解析自己那一面。判据只有一处，不会再出现"两个入口各一套 SQL 漂移"。
- **代价换语义**：单面调用（`retry_schedule`、`live_lease_holders`）也会读到另一面的
  行——这是**有意**的（同一段判据 + 同一快照），行数由 `run_id` 集合界住；在
  `PORTS.md` 写明。
- **零值拼装**：过滤仍全走**绑定参数**（PG `= ANY(%s)`、SQLite `json_each(?)`），
  SQL 文本是**字面量常量**，不拼接、不 `format`、不 f-string。
- **不改判定、不改响应形状、不改时钟**：`kind`/`retry`/`leases` 的取值、`UNKNOWN` 降级
  口径与 `now` 的来源（生产 DB 时钟 / 测试注入时钟）逐字不变。
- **Fake 的边界显式**：Fake 没有 SQL 语句面（内存装配），其一致性来自"同一段装配在同一
  次 Python 调用内完成"；Fake **不做**并发写保护（无锁、无隔离级别）。这条写成显式边界，
  不假装它与持久化实现同等强度。
- **不做 ADR**：本轮不新增 ADR、不改 canonical 状态、不动迁移。

## 验收条件

- **AC-01 一次调用一条语句**：结构判据 = 读面调用期间连接上的**语句计数 == 1**
  （探针计数，PG 与 SQLite 各一），且 SQL 文本是模块级常量（无动态拼装）。
- **AC-02 无撕裂读**（核心判据）：探针在**第一条语句返回之后**用**另一条连接**写入一个
  只影响其中一面的事实（把租约持有者标成 LOST）⇒ 读面返回的仍是**该次读开始时**的一致
  快照（两件事实同刻），且该写入确实生效（事后用新引擎读得到写后状态）。
  **反证**：把实现拆回两条语句 ⇒ 该用例红（第二面读到写后状态 ⇒ 撕裂）。
- **AC-03 同判不变**：既有契约用例（三实现同判）、PG parity、列表批量读与 N+1 哨兵、
  `dispatch_ownership` 单 run 用例全部保持绿（**不改断言**）。
- **AC-04 文档同源收敛**：`packages/application/ports/workflow_engine.py` 的两个
  docstring、`docs/architecture/PORTS.md`、`docs/api/CONTROL_PLANE_API.md` 三处**同一口径**
  （一次读 = 一条语句 = 一个快照；Fake 的显式边界；单面调用也会读到另一面这一代价）。
- **AC-05 门禁**：规模门禁（50 行函数 / 450 行文件）自查 → 定向套件 → m0 全量 23 项 →
  CI 六 job 到终态并记账。

## 实施清单

### WP-A — PG 侧单语句一致读（`adapters/postgres/projections.py`）

- [x] `_FACTS_SQL`：一条 `UNION ALL` 语句，判别列 `kind`（`'RETRY'` / `'LEASE'`），
      两面各自沿用**逐字不变**的判据与过滤：重排面 `run_id = ANY(%s) AND status = %s`；
      租约面 `t.run_id = ANY(%s) AND l.expires_at >= %s AND (l.worker_id IS NULL OR
      l.worker_id NOT IN (SELECT worker_id FROM workers WHERE state = 'LOST'))`。
- [x] `_dispatch_facts(conn, run_ids, now)`：**一次** `conn.execute` ⇒
      `(deadlines_by_run, holders_by_run)`；空入参不读库。
- [x] `retry_schedules` / `live_lease_holders_many` 改为"从同一份 facts 取自己那一面"；
      `dispatch_ownership_many` 用同一份 facts 走既有装配（`_summarize_retries` 与
      `LeaseHolder` 构造逐字不变）。
- [x] 模块 docstring 写明"一次读 = 一条语句 = 一个快照（PG 单语句的快照语义）"。

### WP-B — SQLite 侧同形（`adapters/sqlite/projections.py`）

- [x] 同形改造：一条 `UNION ALL`（`json_each(?)` 过滤），三个入口同源；SQLite 无需类型
      转换（动态类型），判别列与列名与 PG 一致，便于"同判形态"可比对。
- [x] `adapters/sqlite/workflow_engine.py` 的 `_dispatch_ownerships` 改为"一次 facts +
      同一段装配"（方法与记账口径不变）。

### WP-C — 判据用例与反证

- [x] `tests/postgres/test_dispatch_read_snapshot_pg.py`：单快照探针用例
      （连接代理：计数 + 在第一条语句后注入外部写；断言答案取写前快照、语句数 == 1、
      写入事后可见）。**首轮踩坑并修正**：把语义断言放在计数断言之前——否则反证只会
      停在"2 != 1"，看不到 `BOTH → RETRY_DISPATCH` 的撕裂本体。
- [x] `tests/adapters/sqlite/test_dispatch_read_snapshot.py`：同形探针（文件库 + 第二条
      连接做外部写）。
- [x] **反证实跑**：两方言各把取数拆回两条独立语句 ⇒ 探针红（`2 == 1`，语义断言
      `'RETRY_DISPATCH' == 'BOTH'`）；还原 ⇒ 绿（过程与输出记入「证据」）。
- [x] 既有用例复跑：契约同判、parity、列表批量读哨兵（**未改任何断言**）。

### WP-D — 契约与文档同源收敛

- [x] port docstring（`dispatch_ownership` / `dispatch_ownership_many`）：一次读 = 一条
      语句 = 一个快照；单面调用也读另一面的代价；Fake 的显式边界。
- [x] `docs/architecture/PORTS.md`：把"每次调用两条 SQL"更新为"一条语句（`UNION ALL`）
      = 一个快照"，并把 RECHECK-097 W-1 的事实更正（边界此前不在契约里）如实登记。
- [x] `docs/api/CONTROL_PLANE_API.md`：`dispatch` 段补一句"两件事实出自同一快照"。
- [x] RECHECK-20260918-100、MEM-20260918-073、ALL_PLAN、`memory/INDEX.md`、
      GOAL-006 回写（EC-01 状态 / 迭代日志 / child_plans / 状态历史）。

## 证据

- **反证实跑**（两方言各一次，跑完还原）：
  - PG：把 `dispatch_ownership_many` 指回"两次独立取数" ⇒
    `tests/postgres/test_dispatch_read_snapshot_pg.py` **1 failed**：
    先 `assert 'RETRY_DISPATCH' == 'BOTH'`（撕裂本体），再 `assert 2 == 1`（语句计数）；
    还原 ⇒ **2 passed**。
  - SQLite：同形 ⇒ **1 failed**（`'RETRY_DISPATCH' == 'BOTH'` 与 `2 == 1`）；
    还原 ⇒ **2 passed**。
- **判据用例**：`tests/adapters/sqlite/test_dispatch_read_snapshot.py` +
  `tests/postgres/test_dispatch_read_snapshot_pg.py` ⇒ **2 passed**（0.42s）。
- **同判不变**：`tests/adapters/sqlite tests/contracts/test_dispatch_ownership_contract.py
  tests/postgres/test_dispatch_ownership_pg.py` ⇒ **189 passed**（27.95s）。
- **定向（DSN pin）**：`tests/adapters tests/contracts tests/api tests/postgres` ⇒
  **1432 passed / 5 skipped**（223.34s）。
- **规模门禁**：`tests/tooling/test_python_source_limits.py` ⇒ **937 passed**
  （PG 投影 300 行 / 最长函数 41 行；SQLite 投影 296 行 / 47 行）。
- **文档门**：`tools/docs_consistency_check.py` ⇒ **DOCS-CHECK PASS: 6 deterministic checks**。
- **m0 全量**：见「状态历史」。

## 状态历史

- 2026-09-18 建档（GOAL-20260918-006 cycle 1 = EC-01，driver=client-goal /
  owner=root-agent）：只读勘察确认撕裂读暴露面真实、注入点已存在、RECHECK-097 W-1 的
  "已写明"括注与树内事实不符；选定"实现一致读"分支；`status: IN_PROGRESS`。
- 2026-09-18 执行与收口：WP-A…WP-D 完成；两方言反证各 1 红（语句计数 + 撕裂本体）、
  还原后全绿；定向 **1432 passed / 5 skipped**；规模门禁 **937 passed**；文档门 PASS；
  `status: DONE`（RECHECK-20260918-100 = PASS_WITH_WARNINGS，W-1…W-5）。
- 2026-09-18 首轮实现修正（记录，不改断言）：SQLite `projections.py` 的装配搬进去后漏了
  `decode_timestamp` 导入 ⇒ 10 条红（`NameError`）；补导入即绿——**搬代码时要把该模块
  用到的解码函数一并带上**。

## 影响报告

- **Domain / API / schema**：Domain 无变化；HTTP 响应形状与取值**不变**（同判是硬要求）；
  无 schema/迁移变化（只改读取 SQL 形态）。
- **持久化 / 迁移**：无迁移；只读 `tasks` / `leases` / `workers`。
- **安全 / 凭据**：过滤全走绑定参数（PG `= ANY(%s)`、SQLite `json_each(?)`），SQL 文本
  是字面量常量；`lease_id` 仍不进读面；无凭据面变化。
- **兼容性 / 迁移风险**：低。语义是**加强**（从"两条语句、无快照保证"到"一条语句、
  一个快照"）；单面调用多读一面行数由 `run_id` 集合界住。
- **上游版本影响**：无。
- **下一项任务**：GOAL-006 cycle 2 = EC-02（`DEAD_LETTER` 消费，二选一）。
