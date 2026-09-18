---
id: RECHECK-20260918-100
plan_id: PLAN-20260918-100
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-006-cycle1
baseline_ref: 55d789b
checked_head: worktree
---

# RECHECK-20260918-100 — 派发读面的一次读 = 一条语句 = 一个快照（GOAL-006 cycle 1 = EC-01）

## 检查范围

PLAN-20260918-100 声称的交付面：`dispatch_ownership` 的一次调用只发**一条语句**
（PG 与 SQLite 两个方言同一形态）、组合 `kind` 的两件事实来自**同一个快照**（注入写反证）、
既有同判语义不变、契约与三处文档同源收敛。

**不在本轮**：EC-01 的 (b) 分支（ADR 级论证不做）——本 PLAN 走 (a) 实现，未选择 (b)；
`dispatch_ownership` 的**判定语义**本身（`kind` 的组合规则、三态取值）与响应形状不变，
属 GOAL-004 EC-05 已收口面，不在本轮重开。

## 检查结果

| 复查项 | 检验方式 | 结果 |
| --- | --- | --- |
| 撕裂读暴露面真实（先确认再改） | 读旧实现：`projections.dispatch_ownership_many` 依次 `retry_schedules` + `live_lease_holders_many`；PG `autocommit=True`、SQLite `SerializedConnection` 只保证单语句自洽 | PASS（两条独立语句、各自取快照，中间窗口对其它会话/连接可见） |
| AC-01 一次调用一条语句（PG） | `tests/postgres/test_dispatch_read_snapshot_pg.py`：连接代理计数 + 注入写 | PASS（`probe.count == 1`） |
| AC-01 一次调用一条语句（SQLite） | `tests/adapters/sqlite/test_dispatch_read_snapshot.py`：同形探针（文件库） | PASS（`probe.count == 1`） |
| AC-02 无撕裂读 | 探针在第一条语句返回后用**另一条连接**把租约改成过期 ⇒ 答案仍是写前快照 | PASS（`kind == BOTH` + 持有者在列；两个方言各一条用例） |
| AC-02 注入写确实生效（判据自证） | 同用例尾部用新引擎读事后状态 | PASS（写后 `kind == RETRY_DISPATCH`，说明注入的写不是空操作） |
| AC-02 反证（实跑） | 把实现改回**两次独立取数**再跑探针 | PASS（PG：`assert 2 == 1` + `assert 'RETRY_DISPATCH' == 'BOTH'`；SQLite 同为 `2 == 1` 与 `RETRY_DISPATCH != BOTH`） |
| AC-03 同判不变 | 契约（三实现）+ PG parity + SQLite 单测 + 列表批量读哨兵全跑 | PASS（`tests/adapters/sqlite tests/contracts/test_dispatch_ownership_contract.py tests/postgres/test_dispatch_ownership_pg.py` 189 passed；加两条探针 37 passed；定向 1432 passed / 5 skipped） |
| AC-04 三处文档同源 | 读 port 两个 docstring / `PORTS.md` / `CONTROL_PLANE_API.md` | PASS（"一次读 = 一条语句 = 一个快照"、Fake 显式边界、单面调用代价三处一致） |
| AC-04 事实更正登记 | 全树搜索"撕裂/不承诺/快照一致/两次读"（baseline 树） | PASS（RECHECK-097 W-1 声称的"port docstring 与 PORTS.md 已写明"**树内不存在**；本节与 `PORTS.md` 均如实登记） |
| AC-05 规模门禁 | `tests/tooling/test_python_source_limits.py` | PASS（**937 passed**；PG 投影 300 行 / 最长函数 41 行，SQLite 投影 296 行 / 47 行） |
| AC-05 文档一致性门 | `tools/docs_consistency_check.py` | PASS（6 deterministic checks） |

### 交付物在位（结构证据）

- `adapters/postgres/projections.py`：`_FACTS_SQL`（单条 `UNION ALL` + 判别列 `kind`）与
  `_dispatch_facts`（**一次** `conn.execute`）；`retry_schedules` / `live_lease_holders_many` /
  `dispatch_ownership_many` 三个入口**同源**取数（判据只有一处）。
- `adapters/sqlite/projections.py`：同形 `_FACTS_SQL` / `_dispatch_facts` / `dispatch_ownerships`
  （`json_each(?)` 绑定参数）；`adapters/sqlite/workflow_engine.py` 的
  `_dispatch_ownerships` 只保留 `_ensure_open` + 记账。
- `tests/postgres/test_dispatch_read_snapshot_pg.py`、
  `tests/adapters/sqlite/test_dispatch_read_snapshot.py`：同形探针（计数 + 注入写 + 生效自证）。
- 三处契约/文档：`packages/application/ports/workflow_engine.py`、`docs/architecture/PORTS.md`、
  `docs/api/CONTROL_PLANE_API.md`。

## 反证与实测

1. **反证（PG）**：把 `dispatch_ownership_many` 指回"两次独立取数"（临时函数，跑完即删）
   ⇒ `tests/postgres/test_dispatch_read_snapshot_pg.py` **1 failed**：
   `assert 2 == 1`（语句计数）与（重排断言顺序后）`assert 'RETRY_DISPATCH' == 'BOTH'`
   ——后者就是**撕裂读本体**：重排面是写前的、租约面是写后的。还原后 **2 passed**。
2. **反证（SQLite）**：同形改回两次取数 ⇒ **1 failed**（`2 == 1`，语义断言
   `'RETRY_DISPATCH' == 'BOTH'`）。还原后 **2 passed**。
3. **定向**：`tests/adapters tests/contracts tests/api tests/postgres`
   **1432 passed / 5 skipped**（223.34s，DSN pin 配方）；其中派发相关
   `tests/adapters/sqlite tests/contracts/test_dispatch_ownership_contract.py
   tests/postgres/test_dispatch_ownership_pg.py` **189 passed**。
4. **规模门禁**：`tests/tooling/test_python_source_limits.py` **937 passed**。
5. **文档门**：`tools/docs_consistency_check.py` **DOCS-CHECK PASS**。
6. m0 全量 23 项：见 GOAL-006 迭代日志 cycle 1 行。

## 告警（W）

- **W-1（"一个快照"= 语句级，不是事务级）**：判据成立的前提是"一次调用只发一条语句"，
  由用例计数钉住；若将来有人把取数拆成两条（例如为性能分方言分路径），用例会红而不是
  静默退化。**但**这不是"整个读面调用是原子事务"——`now` 的解析（生产路径的
  `server_now` → `SELECT now()`）在无注入时钟时是**另一条语句**，与取数语句不同刻
  （毫秒级窗口）。这是既有的时钟纪律（写入与比较同源），不在 EC-01 的判据内，如实登记。
- **W-2（单面调用多读一面的代价未量化）**：`retry_schedule`（单 run）与
  `live_lease_holders`（单 run/批量）现在也会取另一面的行。行数由 `run_id` 集合界住，
  但**没有**测量对高频调用点的影响（控制面读面，非热路径）。若将来出现热路径调用，
  应重新评估"同源取数"与"分面取数"的取舍——那时判据要升级为"每面一条语句 + 显式
  快照说明"，而不是无脑拆回去。
- **W-3（Fake 的强度仍是弱同判）**：Fake 没有语句面 ⇒ 探针判据对它**不适用**（不是
  "也通过了"）。Fake 的一致性只由"同一段装配在同一次 Python 调用内"保证，无并发写保护。
  这条已在 port docstring 与 `PORTS.md` 写成显式边界，但**不得**读作"三实现同等强度"。
- **W-4（RECHECK-097 W-1 的括注不实）**：该 W 写"port docstring 与 `PORTS.md` 已如实写明
  不承诺跨表快照一致"，baseline 树上**没有**这句（只有"每次调用两条 SQL"）。本轮把边界
  写成**正面契约**（一次读即一个快照），并在 `PORTS.md` 追加事实更正；**未修改**
  RECHECK-097 与 GOAL-005（历史记录只追加、不改写）。教训：历史记录里的"已写明/已修复"
  必须以树内搜索复验。
- **W-5（未覆盖：真并发窗口下的压测）**：探针是**确定性注入**（在语句边界插入外部写），
  不是真并发压力测试；它证明的是"两件事实不可能来自不同快照"，不证明"高并发下读面无
  性能退化"。后者不在 EC-01 判据内。

## 结论

**PASS_WITH_WARNINGS**。EC-01 选 (a) **实现一致读**并落地：两个持久化方言的
`dispatch_ownership` 一次调用只发**一条语句**（`UNION ALL` + 判别列），组合 `kind` 的两件
事实因此同刻；反证实跑两方言各 1 红（语句计数 2 != 1，且语义上 `BOTH` → `RETRY_DISPATCH`
即撕裂读本体）；既有同判语义与响应形状逐字不变（契约/parity/列表哨兵全绿）；三处文档
与 port docstring 同源收敛，并把 Fake 的弱化与单面调用代价写成显式边界。W-1…W-5 是适用
边界：语句级 vs 事务级、单面调用代价未量化、Fake 不适用探针、RECHECK-097 括注不实（已
登记更正）、未做真并发压测。

## 门禁

- 定向（DSN pin）：见「反证与实测」第 3 条。
- 规模门禁 / 文档门：见「反证与实测」第 4、5 条。
- m0 全量 23 项：见 GOAL-006 迭代日志 cycle 1 行。
