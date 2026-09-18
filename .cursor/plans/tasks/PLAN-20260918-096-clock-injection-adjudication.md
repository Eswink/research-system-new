---
id: PLAN-20260918-096
slug: clock-injection-adjudication
title: 时钟/时序风险逐个判定：12 个注入时钟的 PG 用例文件（EC-04）
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-005
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-005 cycle 4 = EC-04（GOAL-004 收口结论表第 9 项 / RECHECK-084 W-5）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-005 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-096-clock-injection-adjudication.md
memory_entries:
  - MEM-20260918-070
---

# PLAN-20260918-096 — 时钟/时序风险逐个判定（GOAL-005 cycle 4 = EC-04）

## 目标

GOAL-004 收口把「12 个注入时钟的 PG 用例文件只 grep 排查过、当时只修了 1 个」登记为
残留（RECHECK-084 W-5）。本 PLAN 按 EC-04 的判据把 12 个文件**逐个判定**，每个判定带
**结构依据**（不接受「跑一次没红」）。

## 枚举（脚本判据，不靠记忆）

新增只读探针 `tools/probes/enumerate_clock_injected_pg_tests.py`：按 AST + 行扫描，
对 `tests/postgres/*.py` 输出每个文件的 ① 注入时钟的行 ② 墙钟读（`datetime.now` /
`utcnow` / `time.time` / `Timestamp.now` / `perf_counter` / `monotonic` / `sleep` /
`CURRENT_TIMESTAMP`）③ 构造点里**没传** `now=` 的（回落到数据库时钟的路径）
④ 断言里出现时间列的行。

实跑（`scratch/ec04-enumeration.txt`）：`postgres test files: 27` / **`clock-injected
files: 12`** / `files with wall-clock reads: 0` / `files with clockless constructors: 6`。

另：`grep -rn "now()" tests/postgres/*.py` 只剩一行**文档字符串**（`test_workflow_retry_backoff_pg.py`
的说明），与 RECHECK-084 W-5「修复后为零」一致。

## 全局结构依据（12 个文件共用）

- **写入与比较同一个源**：`adapters/postgres/db.py` 的 `db_time_expr(now)`
  （SQL 片段：生产 `now()` / 测试绑定参数）与 `server_now(conn, now)`
  （Python 侧比较：生产 `SELECT now()` / 测试注入值）。时钟敏感列（`leases.expires_at` /
  `heartbeat_at` / `tasks.retry_at`）由 Python 侧算好**绑定写入**，判据比较也走同一个源。
- **全树唯一无条件 `now()`**（AST 扫描 `adapters/postgres/*.py` 的字符串字面量）=
  `outbox.py` 的 `outbox_events.created_at`。**没有任何用例断言这一列的取值或排序**：
  相关断言是事件类型**成员**（`EventType.X in kinds`）。引擎把注入时钟传给 outbox
  （`workflow_engine.py` 构造 `PgOutboxWriter(self._conn, self._now)`）⇒ `occurred_at`
  也是确定的。
- **WorkerRegistry** 走同形的 `_time_expr()`（构造参数 `now` 可注入）。

## 逐文件判定

| # | 文件 | 注入时钟 | 断言的时间值来源 | 判定 |
| --- | --- | --- | --- | --- |
| 1 | `test_claim_concurrency_pg.py` | `now=lambda: START`（×2）、`now=clock`、`engine._now = lambda: later`（L154） | 无时间值断言：断言是**不相交**（`len(all) == len(set(all))`）、**条数**、**fence 严格递增**；`join(timeout=60)` 是活性哨兵，超时会让后面的条数断言红 | 安全 |
| 2 | `test_cross_process.py` | `now=lambda: clock["now"]`（L96-98 / L107-109） | 注入时钟的两条做 fencing（`lease_id` 不等、`InvalidInputError`）；L61/74/75 的 DB 时钟引擎只断言 dedup / 状态，无时间值 | 安全 |
| 3 | `test_dispatch_ownership_pg.py` | `now=lambda: now`（L70，缺省 `START`） | `expires_at == Timestamp(START + _TTL)`（L142）由 `workflow_claim.py` 用 `server_now` 算出；L115/167 的 `PostgresWorkerRegistry` 用 DB 时钟，但只断言 worker 状态与 `dispatch_ownership().kind` | 安全 |
| 4 | `test_experiment_queue_pg.py` | store **无构造时钟**：`now` 是**方法参数**（L99…L153） | `claimed_at == NOW` / `_at(TTL±1)` / `not_before` 都是**传进去的值**；`_requeue_expired(now, ttl)` 用传参判过期 | 安全 |
| 5 | `test_lease_fencing.py` | L53/L83 注入；L69/L102 DB 时钟 | 注入的两条做 recover/fencing；DB 时钟的两条断言是**异常**与 `lease_id` 变化 | 安全 |
| 6 | `test_workflow_acquire_backoff_pg.py` | `now=lambda: now`（L53） | 断言是「取到没取到」（`None` / 异常）与 deadline 比较，值来自注入时钟 | 安全 |
| 7 | `test_workflow_due_retries_pg.py` | `now=lambda: now`（L58） | `due_retry_task_ids == (task.id,)`（L106）由注入时钟推进 | 安全 |
| 8 | `test_workflow_engine_parity.py` | 双时钟（sqlite / pg 各一，L125-126） | `_engine(kind, now=None)` 的**无时钟分支（L56/59）没有任何调用点**；scenario 返回值是状态/计数/异常名 | 安全 |
| 9 | `test_workflow_engine_pg.py` | L95/L126/L154 注入；L57/69/82/111/142 DB 时钟 | 注入的三条断言时间（`expires_at` 递增、过期回收）；DB 时钟的五条断言 dedup/状态/事件类型**成员** | 安全 |
| 10 | `test_workflow_retry_backoff_pg.py` | `now=lambda: START`（L58） | `stored > START`（L141）来自 `workflow_ops.py` 的 `server_now + delay`；`retry_at is None`（L161） | 安全 |
| 11 | `test_workflow_retry_policy_pg.py` | `now=lambda: START`（L54） | 断言是状态与重排/死信（由注入时钟驱动） | 安全 |
| 12 | `test_workflow_retry_schedule_pg.py` | `now=lambda: now`（L60）+ 显式推进（L115/120/138） | `next_retry_at == START + 3600`（L142）来自 `projections.retry_schedule(server_now)` | 安全 |

**结论：12/12 判定「安全」，无「修复」项。** 每个判定都落在结构上（谁写这一列、谁读它、
断言比较的是什么），不依赖「跑过一次没红」。

## 验收条件

- **AC-01**：枚举有**脚本**判据（`tools/probes/enumerate_clock_injected_pg_tests.py`），
  输出文件数、注入数、墙钟读数、无时钟构造点数；本 PLAN 记录实跑输出。
- **AC-02**：12 个文件逐个有判定（安全/修复）+ 结构依据；无「未观测到失败」式结论。
- **AC-03**：全局结构依据可复核：唯一无条件 `now()` 的 SQL 是 `outbox_events.created_at`
  且无用例断言它（AST 扫描 + 断言形态）；`db_time_expr`/`server_now` 是写入与比较的共同源。
- **AC-04**：同源文档写明时钟注入纪律（`docs/architecture/PORTS.md`），指向枚举脚本与复检。
- **AC-05**：定向/全量门禁绿；CI 六 job 到终态并记账。

## 实施清单

### WP-A — 枚举探针（已完成）

`tools/probes/enumerate_clock_injected_pg_tests.py`（只读：不写文件、不联网、不执行仓库代码），
`ruff format` 通过；实跑输出见「证据」。

### WP-B — 逐文件判定（已完成）

12 个文件逐个读断言与写入路径（见上表）；6 个含「无时钟构造点」的文件额外做了**逐用例**
核对（`test_cross_process.py` / `test_lease_fencing.py` / `test_workflow_engine_pg.py`
的 DB 时钟用例是 dedup/状态/异常；`test_experiment_queue_pg.py` 的时钟是方法参数；
`test_workflow_engine_parity.py` 的无时钟分支无调用点；`test_dispatch_ownership_pg.py`
的 WorkerRegistry 只被断言状态）。

### WP-C — 文档与记录（已完成）

`docs/architecture/PORTS.md` 增「时钟注入纪律」段；RECHECK-20260918-096、MEM-20260918-070、
`ALL_PLAN`、`memory/INDEX.md`、GOAL-005 回写、CI 轮询到终态。

## 证据

- **枚举实跑**（`uv run --frozen --no-sync python -B tools/probes/enumerate_clock_injected_pg_tests.py`）：
  `postgres test files: 27`、`clock-injected files: 12`、
  `files with wall-clock reads: 0`、`files with clockless constructors: 6`
  （`test_cross_process` / `test_dispatch_ownership_pg` / `test_experiment_queue_pg` /
  `test_lease_fencing` / `test_workflow_engine_parity` / `test_workflow_engine_pg`）。
- **AST 扫描**（`adapters/postgres/*.py` 字符串字面量里的 `now()`）：唯一 SQL 写入点是
  `outbox.py` 的 `outbox_events.created_at`；`db.py` 的两处是抽象本身与 `SELECT now()`；
  `worker_registry.py` 的 `now()` 是 `_time_expr()` 的生产分支。
- **断言形态**：`grep -rn "pending_outbox()] ==" tests/` 空 ⇒ 无「事件顺序」断言；
  相关断言都是 `EventType.X in kinds`。
- **原始 SQL 时钟**：`grep -rn "now()" tests/postgres/*.py` 仅剩一行文档字符串
  （`test_workflow_retry_backoff_pg.py:9` 的说明文字），与 RECHECK-084 W-5 的修复一致。
- **门禁**：目标 ~12 文件的 PG 定向套件 + m0 全量，见「状态历史」。

## 状态历史

- 2026-09-18 建档（GOAL-20260918-005 cycle 4 = EC-04，driver=client-goal /
  owner=root-agent）：枚举脚本先落地（12 个注入时钟文件，与 RECHECK-084 W-5 的记忆数字
  一致，但本轮的判据是脚本输出而非记忆）；`status: IN_PROGRESS`。
- 2026-09-18 收口：12/12 判定「安全」（含 6 个含无时钟构造点的文件逐用例核对）；
  `status: DONE`。

## 影响报告

- **Domain / API / schema**：无变化（本轮只加判定与文档，不改产品代码）。
- **持久化 / 迁移**：无。
- **安全 / 凭据**：无；探针只读仓库文件、只打印，不联网、不写盘。
- **兼容性 / 迁移风险**：无运行时影响；新增的是 `tools/probes/` 下的只读探针。
- **上游版本影响**：无。
- **下一项任务**：GOAL-005 cycle 5 = EC-05（读面语义边界）。
