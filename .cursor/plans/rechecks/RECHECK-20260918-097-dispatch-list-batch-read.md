---
id: RECHECK-20260918-097
plan_id: PLAN-20260918-097
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-005-cycle5
baseline_ref: 3358b2e
checked_head: worktree
---

# RECHECK-20260918-097 — 列表路径的批量派发读面（GOAL-005 cycle 5 = EC-05 ①）

## 检查范围

PLAN-20260918-097 声称的交付面：批量读面（port + 三实现）、控制面列表路径改走批量读、
同判与 N+1 的用例与反证、EC-05 的文档面。

**不在本轮**：EC-05 ②（PG 两读快照一致性）——EC-05 允许"至少一项"，本轮做 ①；
`dispatch_ownership` 的判定语义本身（GOAL-004 EC-05 已收口）。

## 检查结果

| 复查项 | 检验方式 | 结果 |
| --- | --- | --- |
| N+1 真实存在（先确认再改） | 读 `list_runs` → `_detail_dto` → `dispatch_ownership_read` 调用链 | PASS（每条 run 一次 `dispatch_ownership`，每条内部两次读） |
| AC-01 同判（结构） | 读三实现：单 run 与批量是否共用装配 | PASS（`_dispatch_ownerships` / `_ownership_of` / `dispatch_ownership_many` 是一段装配，单 run 只负责记账） |
| AC-01 同判（用例） | 契约用例三实现断言"批量 == 逐 run"（含未知 run = `NONE` 条目） | PASS（`test_the_batch_read_equals_the_per_run_read`；`test_an_empty_batch_reads_nothing`） |
| AC-02 不再 N+1 | 列表请求前后的 adapter call log | PASS（批量 +1、单 run 不变） |
| AC-02 反证 | 改回逐 run 读后重跑哨兵 | PASS（**1 failed / 3 passed**，红点 = 批量调用数 `0 != 1`） |
| AC-03 三态与降级 | 同页种入 `WORKER_CLAIM`/`RETRY_DISPATCH`/`NONE` 三条 run，逐行与详情比 | PASS（三态同值；`workflow=None` ⇒ 逐行 `UNKNOWN`；空页不读派发面） |
| 查询过滤是绑定参数 | 读 SQL 与参数 | PASS（SQLite `json_each(?)`、PG `= ANY(%s)`；SQL 里无拼接值） |
| AC-04 文档面 | `CONTROL_PLANE_API.md`（Fake 无过期语义 + `WORKER_CLAIM` 覆盖控制面自持租约）/ `PORTS.md`（批量读面） | PASS |
| 响应形状未变 | 契约套件（含 OpenAPI 快照） | PASS（`dispatch` 取值与 `UNKNOWN` 降级逐字不变）；快照有 **1 处** `description` 变化（列表路由加一行"整页由一次批量读回答"），已重新生成 + 契约测试实跑绿 |
| 未改判定/时钟/门禁 | `git diff` 对照 | PASS（只加读面与用例，未动 `kind`/`retry`/`holders` 取值、未动时钟源、未改门禁与断言） |
| 450 行文件硬上限 | `tests/tooling/test_python_source_limits.py` | PASS（返工后 447 行；装配搬到新模块 `adapters/postgres/workflow_dispatch.py`，**搬代码不改门禁**） |

## 反证与实测

- **反证（实跑）**：列表路径改回逐 run 读 ⇒
  `uv run --frozen --no-sync python -B -m pytest tests/api/test_run_dispatch_view_api.py -q -k list`
  ⇒ **1 failed / 3 passed / 7 deselected**，失败断言
  `assert workflow.method_calls("dispatch_ownership_many") == batch_before + 1`
  （`assert 0 == (0 + 1)`）⇒ 哨兵确实盯着"整页只读一次"；恢复后复跑绿。
- **定向套件**（DSN pin 配方）：
  `tests/api tests/contracts tests/adapters/sqlite tests/postgres tests/adapters`
  ⇒ **1425 passed / 5 skipped**（235.04s）。**未 pin 时会红 3 条**（`tests/api/test_worker_plane_composition.py`
  的 postgres 标记用例连到 operator `.env` 里另一个 DSN 口令 ⇒ 连接失败）：这是已登记的
  **DSN 注入签名**（litellm `load_dotenv` 注入 operator `.env`），不是本轮回归——pin 后
  同一条命令 **1053 passed / 2 skipped** 复现绿。
- **修一次真回归**：首轮改动后 `retry_schedule` 的旧别名调用点在引擎里漏改 ⇒
  `tests/adapters/sqlite/test_workflow_retry_schedule.py` 等 10 条红（`NameError`）；
  修的是**产品代码**（改用批量投影的单条取值），**未改断言**，复跑全绿。
- **收口门禁返工（只看事实）**：① m0 首跑 `python/product-lint` 红（新 import 未排序）；
  ② 复跑规模门禁红（PG 引擎文件 459 > 450 行）⇒ **搬代码**到新模块
  `adapters/postgres/workflow_dispatch.py`（`dispatch_ownership_impl` /
  `dispatch_ownership_many_impl`），引擎方法只剩 `_ensure_open` + 错误边界；文件 447 行，
  规模门禁 932 passed；③ 返工后**复跑**定向（DSN pin）`tests/api tests/contracts
  tests/adapters/sqlite` ⇒ **1053 passed / 2 skipped**（118.88s，无失败）。

## 告警（W）

- **W-1（EC-05 ② 未做）**：PG 的两读（重排 + 租约）仍不承诺跨表快照一致（port docstring 与
  `PORTS.md` 已如实写明）。本轮只做 ①；若将来要做 ②，判据应是"同一语句/同一快照 +
  并发写期间无撕裂读"，并给"拆回两次读 ⇒ 用例红"的反证。
- **W-2（批量读的规模边界）**：`run_ids` 一次传入整页的 id（当前列表未分页）。若将来列表
  分页或项目 run 数很大，需要给批量读加上限或分块——现在没有分页，故未引入上限。
- **W-3（Fake 的强度不同）**：Fake 的"活"= 仍在租约表里（无过期语义）⇒ 批量读在 Fake 上
  的"同判"是弱同判；过期/LOST 的强判据仍在 SQLite 注入时钟单测与 PG parity（EC-05 ① 的
  三态覆盖在 API 层用真 SQLite 引擎完成，不用 Fake）。
- **W-4（列表路径的两次读）**：一次批量读内部仍是两条 SQL（重排 + 租约），两者之间没有
  快照保证（同 W-1）。查询数从 `2N` 降到 `2`，语义未变。

## 结论

**PASS_WITH_WARNINGS**。EC-05 ① 收口：列表路径从"每条 run 一次 `dispatch_ownership`"改成
**一次批量读**，且同判是**结构性**的（单 run 读 = 批量读的一条，三实现共用装配），不是
"两边各测一遍"；三态与"读不到 ⇒ `UNKNOWN`"的边界逐行与详情一致；哨兵有反证（改回逐 run
读即红）。EC-05 的文档面（Fake 无过期语义、`WORKER_CLAIM` 也覆盖控制面自持租约）已写进
`CONTROL_PLANE_API.md`。W-1…W-4 是适用边界（② 未做、无分页上限、Fake 弱同判、两条 SQL
无快照）。

## 门禁

- 定向（DSN pin）：见「反证与实测」。
- m0 全量：见 GOAL-005 迭代日志 cycle 5 行与「状态历史」。
