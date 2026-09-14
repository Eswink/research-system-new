---
id: PLAN-20260914-048
slug: pause-resume-dispatch-coordination
title: pause/resume 真执行协调（派发暂停 + 边界观测 + 诚实续跑）
status: DONE
created_at: 2026-09-15
updated_at: 2026-09-15
parent_goal: GOAL-20260912-001
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260912-001 cycle 8（/goal 持续循环迭代指令）；范围=EC-04「pause/resume 真执行（lease+worker 协调）」一项；实验队列与 memory capability policy（G16）属后续 cycle"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-048-pause-resume-dispatch-coordination.md
memory_entries:
  - MEM-20260915-025-pause-dispatch-coordination
---

# PLAN-20260914-048 — pause/resume 真执行协调（cycle 8，EC-04 第三批）

## 目标

把 `pauseResume: "pause/resume 仅状态迁移，不证明实际暂停/恢复执行"` 这一诚实缺口，
换成**真实可见的执行协调**：

- **派发暂停**：run 状态为 `PAUSED` 时，它的未完成任务**不再被 worker 认领**
  （`claim_next` 过滤），在途租约不被撤销（协作式，不制造孤儿）。
- **边界观测**：执行器在 phase 组边界读取暂停信号；已暂停则**不执行任何任务**，
  把剩余 specs 交回并给出 `PAUSED` 结果（不是"跑完再说"）。
- **诚实续跑**：resume 只有在**本进程持有暂停上下文**时才继续剩余 specs；
  没有上下文时只解除暂停（派发恢复）并在响应里明说 `continuation`，不伪造续跑。

## 诚实边界

- **进程内 run 是同步执行**：`POST /runs` 在请求内跑完整条链（阻塞式 handler），
  因此 HTTP 层**无法在 run 执行中途插入 pause**。本 cycle 不声称"可抢占"：
  能被观测到的暂停只有两种来源——(a) 派发面（worker/队列）收到 pause 后停止认领，
  (b) 执行器自己在下一次边界读取到信号（pause 在边界前已被记录）。
- **不撤销在途租约**：已 `LEASED` 的任务按租约完成或由既有
  `recover_expired_leases` 收敛；暂停不产生 orphan，也不伪造"已停止"。
- **跨进程续跑不伪造**：暂停上下文（剩余 specs）是进程内的；重启后
  `continuation=NONE`，resume 只解除暂停。
- 暂停不发布新的 outbox 事件类型（与 budget_adjust 同侧已知边界，记 WARNING）。

## 范围

- 包含：
  - WP-A 派发面：`WorkflowEngine` 新增 `run_state(run_id)` 只读视图；
    `claim_next` 在 SQLite / PostgreSQL / Fake 三个实现里跳过 `PAUSED` run 的任务。
  - WP-B 执行器：`PhaseRunnerDeps.pause_requested` + `execute_phases` 组边界检查 →
    `PAUSED` outcome + 剩余 specs 经 `on_pause` 交回（零任务执行、不发 RUN_COMPLETED）。
  - WP-C 编排/API：service 注入暂停谓词、暂存暂停上下文、`resume_paused`；
    `POST /runs/{id}/pause|resume` 与 `interventions` 分支给出真实语义字段
    （`dispatch_held` / `continuation` / `execution_context`）。
  - WP-D 收口：应用层/adapter/API 用例、前端 tooltip 与 pageSupport、文档、
    m0、RECHECK-048。
- 不包含：实验队列（域内排队/调度）、memory capability policy（G16）、
  抢占式暂停（撤销租约）、跨进程暂停上下文持久化。

## 架构与数据流

```
POST /runs/{id}/pause
  → run.transition(PAUSE)（仅 RUNNING）+ save_run（canonical）
  → 派发面：claim_next 跳过 run_json.state = 'PAUSED' 的 run（SQLite json_extract / PG ->>）
  → 执行器（若本进程正在执行）：下一次组边界读到 pause_requested()=True
      → outcome PAUSED + on_pause(剩余 specs)（service 暂存）
POST /runs/{id}/resume
  → run.transition(RESUME)（仅 PAUSED）+ save_run（派发恢复）
  → 有暂停上下文：继续剩余 specs（真续跑，冻结 manifest 校验不变）
  → 无暂停上下文：continuation=NONE（只解除暂停，不伪造）
```

## 验收条件

- [x] AC-01（WP-A）：三个实现的 `claim_next` 在 run 处于 `PAUSED` 时返回 None；
  resume 后同一任务重新可认领；在途租约不受影响；`run_state` 对未知 run 返回 None。
- [x] AC-02（WP-B）：`pause_requested` 为真时 `execute_phases` 零任务执行、返回
  `PAUSED`、剩余 specs 经 `on_pause` 交回、不发 `RUN_COMPLETED`。
- [x] AC-03（WP-C）：pause 仅 RUNNING 可达（否则 409）；resume 有上下文时真续跑、
  无上下文时 `continuation=NONE`；响应字段与文档一致；web 门全绿。
- [x] AC-04（WP-D）：m0 全绿 + API/adapter 用例；push 后 quality-ubuntu 与
  console-frontend 全绿；RECHECK-048 回填。

## 实施清单

- [x] WP-A 派发面（port + sqlite + postgres + fake）
- [x] WP-B 执行器边界观测
- [x] WP-C service + API 语义
- [x] WP-D 测试 + 前端 + 文档 + 收口

## 证据

- 2026-09-15 WP-A：`WorkflowEngine` 新增 `run_state(run_id)` 只读视图；
  `claim_next` 在 SQLite（候选扫描内 `NOT EXISTS ... json_extract(run_json,'$.state')`）、
  PostgreSQL（两条静态 SQL 变体各加同一 `NOT EXISTS ... run_json ->> 'state'` 过滤）与
  Fake（`set_run_state` 注入的 run 状态视图）三处跳过 PAUSED run 的任务。契约套件
  `tests/contracts/test_pause_dispatch_contract.py` 3 用例 × 3 实现 = 9 passed：
  未知 run → None、PAUSED 不派发且解除后可派发、暂停不撤销已持租约（heartbeat 仍成功）。
- 2026-09-15 WP-B：`PhaseRunnerDeps.pause_requested` + `_pause_if_requested`——
  组边界读到暂停信号即**零任务执行**返回 PAUSED，剩余 specs（含当前组）经 `on_pause`
  交回；`tests/application/test_pause_coordination.py` 5 passed（恒真→零执行+全部交回；
  第一组后翻转→仅首组执行+只交回第二组；恒假→正常 SUCCEEDED 的对照）。
- 2026-09-15 WP-C：service 注入 `pause_requested`（读 canonical run state，未知 run
  → False，不靠进程内标志）、新增 `has_paused_context` / `resume_paused`；API
  `POST /runs/{id}/pause|resume` 与 `interventions` 分支共用 `_transition_or_409` /
  `_pause_payload` / `_resume_payload`，响应带 `dispatch` / `execution_context` /
  `continuation` / `note`；`tests/api/test_pause_resume_api.py` 5 passed（暂停后
  claim 为 None、恢复后可认领；409/404 守卫；interventions 与专用端点同语义）。
  夹具 `tests/api/run_fixtures.py` 补 `runs_store`（与生产 composition 同侧）——
  否则派发面读不到 run 行、暂停协调在夹具中是空断言。
- 2026-09-15 WP-D：前端 run 操作 tooltip 与 `pageSupport`（`run/timeline` →
  partial + `GAPS.pauseResume` 改写）同步；`docs/api/CONTROL_PLANE_API.md` 与
  `docs/frontend/CONSOLE_PAGE_MAP.md` G6 改写为已交付口径；openapi 快照随 docstring
  再生（2 处 description）。门禁：m0 23/23 PASS；全量 pytest 3319 passed/6 skipped/
  0 failed；web lint/typecheck/unit(73) 绿；stub e2e 34/34；live e2e 17/17；
  ruff check/format + mypy 绿。

## 已知风险

- `runs` 表只有 `run_json`（无独立 state 列）：SQLite 用 `json_extract`、PG 用 `->>`
  读状态；SQLite 侧 JSON1 需可用（已实测 Python 内置 sqlite3 支持）。
- `claim_next` 的 SQLite 候选扫描是 Python 侧过滤：暂停过滤必须作用在**候选集**
  而不是扫描之后，否则会饿死其他 run 的任务。
- `claim_next` 在 PG 侧有两条静态 SQL（带/不带 partition 过滤），两处都要加过滤。
- 执行器 outcome 的定价引用由 service 回填（`_execute_with_context`），新增
  PAUSED 分支不能绕过该回填。

## 状态历史

- 2026-09-15 由 GOAL cycle 8 派生（EC-04 第三批），进入执行。
- 2026-09-15 WP-A/WP-B/WP-C/WP-D 完成，本地门全绿，进入复检。

## 影响报告

- **改动**：Port `WorkflowEngine.run_state`；三实现 `claim_next` 的暂停过滤；
  `phase_runner` 边界暂停；service 暂停谓词/上下文/续跑；API pause/resume 语义与
  响应字段；夹具补 `runs_store`；前端 tooltip + pageSupport；docs 三处；openapi 再生；
  新增测试 19（应用层 5 / 契约 9 / API 5）。
- **lint/typecheck/test**：ruff check/format 绿；mypy（含新测试）Success；
  全量 pytest 3319 passed/6 skipped/0 failed；m0 23/23 PASS；web lint/typecheck/unit
  绿；stub e2e 34/34；live e2e 17/17。
- **Domain/API/schema 变化**：无新表、无迁移（暂停事实 = 既有 `runs` 行的 canonical
  state）；Domain 无改动；API 行为增强（原 pause/resume 仅状态迁移）。
- **安全/凭据变化**：无。
- **兼容性/迁移风险**：`claim_next` 语义收紧（PAUSED run 不再派发）——对既有 run 无
  影响（未暂停时行为不变）；SQLite `runs` DDL 收敛到 `db.SCHEMA_SQL` 单一来源，
  run_store 复用（`IF NOT EXISTS`，无破坏性）。
- **上游版本影响**：无。
- **下一项任务**：cycle 9 = EC-04 剩余（实验队列 / memory capability policy G16）。

