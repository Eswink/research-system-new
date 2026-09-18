---
id: RECHECK-20260918-096
plan_id: PLAN-20260918-096
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-005-cycle4
baseline_ref: 43933a1
checked_head: worktree
---

# RECHECK-20260918-096 — 时钟/时序风险逐个判定（GOAL-005 cycle 4 = EC-04）

## 检查范围

PLAN-20260918-096 声称的交付面：`tests/postgres/` 下**注入时钟**的用例文件逐个判定
（安全/修复，带结构依据）、枚举脚本、同源文档段。

**不在本轮**：真墙钟矩阵（`test_cross_process_real.py`，见 W-4）、`tests/postgres/` 之外
的注入时钟用例（EC-04 的枚举面按 GOAL-004 收口结论表第 9 项限定在 `tests/postgres/`）、
以及"产品代码是否该改"这类超出判定的问题。

## 检查结果

| 复查项 | 检验方式 | 结果 |
| --- | --- | --- |
| AC-01 枚举有脚本判据 | 跑 `tools/probes/enumerate_clock_injected_pg_tests.py`（AST + 行扫描，只读） | PASS（`postgres test files: 27` / `clock-injected files: 12` / `wall-clock reads: 0` / `clockless constructors: 6`） |
| AC-01 枚举面与上游一致 | 对照 RECHECK-084 W-5 的「12 个文件、当时只修了 1 个」 | PASS（数字一致；被修掉 raw SQL 的那个文件已不注入时钟 ⇒ 不在枚举面内，`now()` 在 `tests/postgres/*.py` 只剩一行文档字符串） |
| AC-02 12 个文件逐个判定 | 逐文件读断言 + 追它们的**写入路径**（谁写这一列、谁读它） | PASS（12/12「安全」，见 PLAN 表；无「修复」项） |
| AC-02 无「跑一次没红」式依据 | 判据形态检查 | PASS（每条依据都点名**列**与**源码行**，例如 `expires_at == START + _TTL` ← `server_now`；`next_retry_at == START+3600` ← `projections.retry_schedule(server_now)`） |
| AC-02 无时钟构造点逐用例核对 | 6 个文件逐个看用到无时钟构造点的用例断言 | PASS（`test_cross_process`/`test_lease_fencing`/`test_workflow_engine_pg`：dedup、状态、异常、事件类型成员；`test_experiment_queue_pg`：`now` 是**方法参数**；`test_workflow_engine_parity`：无时钟分支**无调用点**；`test_dispatch_ownership_pg`：WorkerRegistry 只被断言状态/kind） |
| AC-03 唯一无条件 `now()` | AST 扫描 `adapters/postgres/*.py` 的字符串字面量 | PASS（`outbox.py` 的 `outbox_events.created_at`；`db.py` 两处是抽象本体与 `SELECT now()`；`worker_registry.py` 是 `_time_expr()` 的生产分支） |
| AC-03 该列无用例断言 | `grep -rn "pending_outbox()] ==" tests/` + 断言形态 | PASS（空；相关断言是 `EventType.X in kinds`） |
| AC-04 文档同源 | `docs/architecture/PORTS.md` | PASS（新增「时钟注入纪律」段 + 枚举脚本路径 + 指向本复检） |
| AC-05 门禁 | 定向套件 + m0 | PASS（见「门禁」） |
| 未改产品/断言/门禁 | `git diff` 对照 | PASS（新增 1 个只读探针 + 1 段文档；无测试断言、无门禁改动） |

## 反证与实测

本轮没有「修复」项，因此没有"去掉修复 ⇒ 用例红"式的反证；替代的判别力检查是**判定本身
的结构性**：

- 每个判定都给出「这一列由谁写」与「断言比较的是什么」，因此可以被独立复核甚至推翻
  （例如：若哪天 `projections.py` 改用 SQL `now()`，`next_retry_at == START+3600` 就会红——
  该断言**同时**是这条纪律的哨兵）。
- **负向检查**：`files with wall-clock reads: 0` 是脚本对 12 个文件逐行扫描的结果，
  不是"我觉得没有"。

## 告警（W）

- **W-1（一条调度依赖断言，非时钟依赖）**：`test_claim_concurrency_pg.py` 的
  `assert sum(1 for claimed in results.values() if claimed) >= 2`（"并发是真的"）在结构上依赖
  线程调度：只有当**一个** worker 在其余 worker 拿到第一条之前把 24 条全领完才会假。
  缓解是结构的：`threading.Barrier(4)` 保证四个 worker 都就绪后才开始领，引擎在 barrier
  **之前**建好。若将来在极端负载下变红，正确的修法是换成"进入领循环的线程计数"，
  **不是**删掉这条断言（它保护的是"测试真的在并发"这一前提）。
- **W-2（无时钟分支暂不可达）**：`test_workflow_engine_parity.py` 的 `_engine(kind, now=None)`
  分支（L56/59）当前**没有调用点**（`test_parity` 恒传双时钟）。将来若有用例走它，
  数据库时钟会进入 parity 比较 ⇒ 应在那一轮补判定，而不是默认它安全。
- **W-3（WorkerRegistry 生产用 DB 时钟）**：`PostgresWorkerRegistry` 的两个用例不注入时钟
  （用生产分支），但**不断言任何时间值**（只断言 worker 状态与 `dispatch_ownership().kind`）。
  抽象已在（`_time_expr()`，构造参数 `now` 可注入）⇒ 需要时无需改产品代码。
- **W-4（真墙钟矩阵有意在外）**：`tests/postgres/test_cross_process_real.py` 是**有意**用真
  墙钟 TTL + 硬 kill 的跨进程矩阵（`pytest.mark.timing_sensitive`，等待用**有界轮询**，
  见 M17 PART B 的修复记录）。它不在 EC-04 的枚举面内（枚举面 = 注入时钟的文件），
  本轮的判定**不覆盖**它，也不据此宣称"时序风险已清空"。

## 结论

**PASS_WITH_WARNINGS**。EC-04 要求的"逐个判定 + 结构依据"已落地：12 个注入时钟的 PG
用例文件全部判定为**安全**，依据落在写入源与断言形态上（不是"没跑红"）；枚举有脚本判据
且与上游记忆数字一致；唯一无条件 `now()` 的 SQL（outbox 行时间戳）没有任何断言依赖它；
时钟纪律写进了 `docs/architecture/PORTS.md` 并指向本复检。W-1…W-4 是适用边界：其中
W-4 明确本轮**没有**覆盖真墙钟矩阵。

## 门禁

- 定向：`tests/postgres`（DSN pin 配方，含 12 个判定文件）。
- m0 全量：见 GOAL-005 迭代日志 cycle 4 行与「状态历史」。
