---
id: PLAN-20260915-066
slug: ops-schedules-write-surface
title: ops 调度用户可见写面（EC-03）
status: IN_PROGRESS
created_at: 2026-09-16
updated_at: 2026-09-16
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 4 = EC-03（ops 调度用户可见写面）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-066-ops-schedules-write-surface.md
memory_entries:
  - MEM-20260915-041-scheduler-remains-the-executor
---

# PLAN-20260915-066 — ops 调度写面（GOAL-003 cycle 4 / EC-03）

## 目标

`GET /ops/schedules` 现在只是**只读事实**：把 composition root 里 4 个进程内守护
scheduler 的静态配置（name/interval/purpose/enabled）投影出来，并如实写着
"无用户可见创建/启停/触发 API"，console 侧 `ops/schedules` 的三个操作
（create/toggle/trigger）登记在 `disabledOperations`。

本轮把它们做成**真实写面**，且不新造第二套调度器（EC-03 口径）：

```text
GET    /ops/schedules                   现状 + 每项运行事实（last_run_at/run_count/last_outcome）
POST   /ops/schedules                   登记一条调度定义（job 取自平台词表 + interval + enabled）
PATCH  /ops/schedules/{name}            启停 / 改 interval（写面被读面消费）
POST   /ops/schedules/{name}/trigger    手动触发一次 pass（立即执行，不等下一个 tick）
```

**执行体不变**：仍是 `services/api/scheduler.py` 的守护线程；它们每一轮从
调度定义读 enabled/interval（定义变更下一轮生效），`trigger` 走同一条 pass 函数
（不是第二套执行路径）。

## 口径（这轮最容易做错的地方）

1. **不新造调度器**：不得引入 APScheduler/Celery/第二套循环；`trigger` 必须调用
   与守护线程同一个 pass 函数，并留下与定时 pass 相同的运行事实（可观察同一结论）。
2. **"登记定义"≠"立刻有执行体"**：内置 4 个守护线程是代码定义的执行体；用户新增的
   定义只能绑定到**既有 job 词表**（如 `lease_recovery` / `outbox_relay` /
   `retention` / `worker_reap`）。若某个 job 没有对应执行体（例如尚未装配 retention
   的场景），读面必须如实呈现"无执行体"，不得假装在跑。
3. **启停语义要有可证伪的读面证据**：`PATCH enabled=false` 之后，读面 `enabled` 变
   且**下一轮不再计入运行事实**（`run_count` 不再增长）；这是"写面被读面消费"的证据，
   不是响应字段的自我声明。
4. **手动触发要留下与定时相同的痕迹**：`POST .../trigger` 后 `last_run_at`/`run_count`
   /`last_outcome` 立刻更新，且 outcome 复用既有观测口径（成功/失败不伪装）。
5. **`disabledOperations` 必须收敛**：`pageSupport` 的 `ops/schedules` 项删除
   `create/toggle/trigger`，并同步 `CONSOLE_PAGE_MAP.md`；无法支持的子集要写清楚
   （例如"只能绑定既有 job 词表，不能定义新的 pass"）。

## 范围

- 新增：`packages/application/ports/schedule_store.py`（或复用/扩展 OpsStore 端口——
  derive 时先看既有 `adapters/sqlite/ops_store.py` 与 `packages/application/ports/ops.py`
  的形状再定）、`services/api/routers/ops_schedules.py`、`services/api/dto/ops_schedules.py`、
  `services/api/schedule_support.py`、`adapters/sqlite/schedule_store.py`、
  `services/api/scheduler.py` 的执行体接上定义读面（**不重写循环**）。
- 修改：`services/api/composition.py` / `pg_composition.py` / `run_fixtures.py`（装配）、
  `services/api/app.py`（路由）、`docs/api/openapi.m13.json`（重生成）、
  `docs/api/CONTROL_PLANE_API.md`、`docs/frontend/CONSOLE_PAGE_MAP.md`、
  `apps/web/src/navigation/pageSupport.ts`、console `ops/schedules` 页（写面控件）。
- 测试：`tests/api/test_ops_schedules_api.py`（新）、`tests/application/`（调度定义与
  执行体联动）、`apps/web/tests/e2e/stub-routes-schedules.ts` + `schedules-write.spec.ts`、
  `apps/web/tests/e2e/live-schedules-write.spec.ts`（+ `live-specs.ts` 登记）。
- **设计基线**：`ops-schedules` 页面会真实变化 ⇒ 重生成结构签名 + win32/linux 像素基线
  并目检（沿用 cycle 3 的脚本：`gen_linux_baseline_route.sh` / `verify_linux_outlines.sh`）。

## 验收条件

- [ ] AC-01：`GET /ops/schedules` 在既有静态事实之外，给出每项的 `last_run_at` /
  `run_count` / `last_outcome`（无执行体时如实为 null/UNKNOWN，不伪造 0 计数）。
- [ ] AC-02：`POST /ops/schedules` 服务端校验：job 不在词表 → 422 点名；interval 越界
  → 422；name 重复 → 409；平台内置名保留 → 409。
- [ ] AC-03：`PATCH` 启停生效**且被读面消费**：置 `enabled=false` 后读面为 false 且
  `run_count` 不再增长（用例里用可控 pass 计数证明）；改 interval 后读面 interval 变。
- [ ] AC-04：`POST .../trigger` 立即执行同一 pass 函数并更新运行事实（`run_count` +1、
  `last_run_at` 前进）；终态/未知 name → 404。
- [ ] AC-05：console `ops/schedules` 的三个 `disabledOperations`（create/toggle/trigger）
  消失，页面上有可操作控件，且被读面消费（stub + live 各一条链）。
- [ ] AC-06：OpenAPI 写方法 + 契约断言；文档与 `pageSupport` 收敛（仍缺的子集写清）。
- [ ] AC-07：全量门禁（stub/live e2e、web 单测、eslint、tsc、根 eslint、全量 pytest、m0 23）
  + 设计基线重生成并目检。
- [ ] AC-08：RECHECK-066 + MEM-041 + GOAL 记账；EC-03 由 PENDING → PASS（若 AC-01~07 全绿）。

## 实施清单

- [ ] WP-A 端口与 domain（ScheduleDefinition + job 词表 + 校验）
- [ ] WP-B 执行体接线（守护线程从定义读 enabled/interval；trigger 复用 pass 函数）
- [ ] WP-C 路由/DTO/装配（SQLite + PG 两组成 + run_fixtures）
- [ ] WP-D API 用例 + 契约/OpenAPI
- [ ] WP-E console 写面 + stub/live e2e + 文案收敛
- [ ] WP-F 设计基线重生成目检 + 全量门禁 + 记录

## 证据

（WP 完成后回填：命令 + 真实输出）

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：cycle 3（ToolPack console 面）闭环后按 EC 表顺序取
  EC-03。derive 时的关键判断：**写面不能变成第二套调度器**——执行体是既有守护线程，
  本轮只把"定义"变成可写、可读、可触发的对象，并让 `trigger` 与定时 pass 走同一条函数；
  验收证据也因此必须落在"读面事实变化"上（AC-03/04），而不是响应体自述。

## 影响报告

（完成后回填）

## 已知风险

- **进程内执行体的可测性**：守护线程在测试里不应真的按 interval 跑（会变慢/flaky）；
  测试用可控 pass 计数与显式 `trigger`，定时语义只做"下一轮读取定义"这一条断言。
- **PG 侧装配**：`pg_composition` 也要装配同一 store，否则写面在 PG 开发路径下 503——
  沿用既有的双组成模式（PLAN-041 起）。
- **基线重生成**：`ops-schedules` 页面必然变化 ⇒ 两个平台像素 + 结构签名都要重生成。
