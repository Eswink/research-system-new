---
id: PLAN-20260915-066
slug: ops-schedules-write-surface
title: ops 调度用户可见写面（EC-03）
status: DONE
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

- [x] AC-01：`GET /ops/schedules` 在既有静态事实之外，给出每项的 `last_run_at` /
  `run_count` / `last_outcome`（无执行体时如实为 null/UNKNOWN，不伪造 0 计数）。
  ——`test_read_surface_reports_executor_attachment_honestly`：本装配只跑 lease 守护线程 ⇒
  `worker_reaper.executor_attached=false` 且 `last_outcome=null`、`next_due_at=null`；
  `lease_recovery=true`。响应另带 `jobs`（作业词表 + 用途）与 `note`（口径）。
- [x] AC-02：`POST /ops/schedules` 服务端校验：job 不在词表 → 422 点名；interval 越界
  → 422；name 重复 → 409；平台内置名保留 → 409。
  ——`test_create_validates_vocabulary_interval_and_names`：422 文本含合法词表项；0.5s → 422；
  `Bad-Name` → 422；占用内置名 → 409；重复登记 → 409。**词表校验在 `ScheduleRegistry.create`
  的 `_coerce_job`（域边界），不在 Pydantic**——DTO 层不得 import domain（架构门禁
  `api-dto-purity`，首轮 m0 因此判红，见状态历史）。
- [x] AC-03：`PATCH` 启停生效**且被读面消费**：置 `enabled=false` 后读面为 false 且
  `run_count` 不再增长（用例里用可控 pass 计数证明）；改 interval 后读面 interval 变。
  ——API 侧 `test_patch_toggle_is_consumed_by_the_executor_read_surface`（`due()` 不再授予、
  trigger 409、启用+改间隔后读面变 120 且 `due()` 重新授予）；
  执行体侧 `tests/application/ops/test_periodic_daemon.py::test_disable_is_consumed_by_the_daemon_loop`
  （真实线程：停用后 `run_count` 冻结 0.5s，重新启用后继续增长）。
- [x] AC-04：`POST .../trigger` 立即执行同一 pass 函数并更新运行事实（`run_count` +1、
  `last_run_at` 前进）；终态/未知 name → 404。
  ——`test_trigger_runs_registered_pass_and_records_facts`：失败 pass → 200 但
  `last_outcome=FAILED`+`last_error`；换成计数 pass 后 `calls == ["pass"]`（同一函数）、
  `run_count=2`、`last_outcome=OK`；未知 → 404；有定义无执行体 → 409。
- [x] AC-05：console `ops/schedules` 的三个 `disabledOperations`（create/toggle/trigger）
  消失，页面上有可操作控件，且被读面消费（stub + live 各一条链）。
  ——`pageSupport` 的 `ops/schedules` 项已无 `disabledOperations`；stub
  `schedules-write.spec.ts` 5 passed（登记后事实为 UNKNOWN、触发后 1 次·OK、停用后 OFF
  且触发禁用、无执行体禁用、409 落在面板内）；live `live-schedules-write.spec.ts` 2 passed
  （登记 → 触发 → 停用 → 409 → 复原触发到 2 次；词表外作业/越界间隔 422）。
- [x] AC-06：OpenAPI 写方法 + 契约断言；文档与 `pageSupport` 收敛（仍缺的子集写清）。
  ——`docs/api/openapi.m13.json` 重生成（相对基线 **+303 / -2**）；
  `test_openapi_contains_ops_schedule_write_methods`
  断言 `GET/POST /ops/schedules`、`PATCH /ops/schedules/{name}`、
  `POST /ops/schedules/{name}/trigger` 与描述里的 404/409/last_outcome；
  `CONTROL_PLANE_API.md` 新增「调度（EC-03）」段、`CONSOLE_PAGE_MAP.md` 的页面段与 G7 行、
  `pageSupport.GAPS.schedules` 写明"仍缺：不能新增执行路径 / 无删除归档 / 无 cron 与日历视图"。
- [x] AC-07：全量门禁（stub/live e2e、web 单测、eslint、tsc、根 eslint、全量 pytest、m0 23）
  + 设计基线重生成并目检。
  ——stub e2e **77 passed** / live e2e **35 passed** / web 单测 **76 passed** /
  `pnpm lint`+`tsc` 通过 / 根 `eslint .` 0 error（1 条既有 soft warning）/
  契约 **365 passed, 56 skipped** / `tests/postgres` **70 passed** /
  m0 **PASS: profile=m0; 23 deterministic checks**；
  结构签名判红（`ops-schedules` +90 节点）→ `UPDATE_OUTLINES=1` 重生成 1 行；
  win32/linux 像素基线各重生成一张并目检；`verify_linux_outlines.sh` → 33/33 跨平台一致。
  全量 m0 一共判红两轮（都修在代码里、没动断言）：① 架构门禁 DTO import domain；
  ② 守护线程启动抢跑（`next_wait_seconds` 的 0.1s 候选）打断 PG 用例的显式事务。
- [x] AC-08：RECHECK-066 + MEM-041 + GOAL 记账；EC-03 在 AC-01~07 全绿后由未满足转为 PASS。
  ——RECHECK-20260915-066（PASS_WITH_WARNINGS）+ MEM-20260915-041 +
  GOAL-20260915-003 的 EC 表/迭代日志/状态历史。

## 实施清单

- [x] WP-A 端口与 domain（ScheduleDefinition + job 词表 + 校验）
- [x] WP-B 执行体接线（守护线程从定义读 enabled/interval；trigger 复用 pass 函数）
- [x] WP-C 路由/DTO/装配（SQLite + PG 两组成 + run_fixtures）
- [x] WP-D API 用例 + 契约/OpenAPI
- [x] WP-E console 写面 + stub/live e2e + 文案收敛
- [x] WP-F 设计基线重生成目检 + 全量门禁 + 记录

## 证据

**WP-A/B（域与执行体）**

```text
$ python -m pytest tests/application/ops/ -q
20 passed in 2.17s
# test_schedule_registry.py（11）：内置补齐幂等 / 创建取值域与保留名 / 更新与未知 /
#   删除（内置不可删）/ due reserve 与跳过停用 / record 事实 / trigger 共用 pass 与
#   失败留痕 / trigger 拒绝未知-停用-无执行体 / 停用被读面消费 /
#   **等待下界不知晓未预约定义**（回归钉子）/ 停用定义不影响等待
# test_periodic_daemon.py（9）：节奏随定义（29s 内不得再跑、31s 后必须跑）/
#   停用被守护线程循环消费 / 失败 pass 记账且线程存活 /
#   attach 后 trigger 跑同一函数 / 无 control 退化 / 记账失败不杀线程 /
#   读面恢复后重新开跑 / **启动不抢跑**（0.2s 时 pass 必须仍为 0）
```

**WP-C/D（API 与契约）**

```text
$ python -m pytest tests/api/test_ops_schedules_api.py tests/api/test_ops_view_api.py -q
9 passed
$ python -m pytest tests/contracts -q
365 passed, 56 skipped
$ python -m pytest tests/architecture tests/api tests/application/ops -q   # 架构门禁修复后
447 passed
$ python -m pytest tests/postgres -q                     # 启动抢跑回归修复后
70 passed in 26.08s
$ python -m pytest tests/postgres/test_m13_pg_run_e2e.py -q   # 对照：干净 HEAD 6/6 绿
# 修复前：本工作树 6/6 红（OutOfOrderTransactionNesting）；修复后 6/6 绿
$ lint-imports --config .importlinter.api --no-cache
Contracts: 2 kept, 0 broken.
$ python -B tools/gen_openapi.py   # docs/api/openapi.m13.json（相对基线 +303 / -2）
$ git status --short docs/api/openapi.m13.json   -> M
```

**WP-F（设计基线）**

```text
$ npx playwright test design-fidelity.spec.ts        # 未设 UPDATE_OUTLINES：结构签名判红
   drifted=["ops-schedules"]，节点 170 → 260（新 form/panel/table 7 列/note）
$ UPDATE_OUTLINES=1 npx playwright test design-fidelity.spec.ts
  design-outlines.json diff = 1 行
$ npx playwright test design-outline-guard.spec.ts    # 6 passed（反证仍会咬）
$ bash scratch/gen_linux_baseline_route.sh ops-schedules   # linux 基线重生成
$ bash scratch/verify_linux_outlines.sh
  host routes=33 linux routes=33 drifted=[] -> PASS: 33 条结构签名跨平台一致（win32 == linux）
```

像素判据同一次改动仍绿（实测 **15093 px = 1.64%** < 2% 阈值，`scratch/cycle4-design/`）——
结构判据补的正是这块盲区（见 MEM-20260915-038）。

**WP-F（全量门禁）**

```text
$ npx playwright test                     -> 77 passed (4.2m)
$ npx playwright test --config playwrightLive.config.ts -> 35 passed (46.4s)
$ npm run test                            -> 76 passed
$ npm run lint (apps/web) / npm run typecheck -> 0 error / 通过
$ npm run lint (root eslint .)            -> 0 error（1 条既有 soft warning：live-api-workflow 403 行）
$ sh scratch/run-m0-cycle12.sh            -> PASS: profile=m0; 23 deterministic checks
# 收口提交 de58a31 → CI run 35087267045：六个 job 全 success（无重跑）
```

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：cycle 3（ToolPack console 面）闭环后按 EC 表顺序取
  EC-03。derive 时的关键判断：**写面不能变成第二套调度器**——执行体是既有守护线程，
  本轮只把"定义"变成可写、可读、可触发的对象，并让 `trigger` 与定时 pass 走同一条函数；
  验收证据也因此必须落在"读面事实变化"上（AC-03/04），而不是响应体自述。
- 2026-09-16 WP-A 完成：domain `ScheduleDefinition`/`ScheduleJob` 词表/`ScheduleRuntime` +
  `ScheduleStore` 端口（SQLite + Fake 两实现，进 contract registry + 矩阵）+ `ScheduleRegistry`
  （due 的 reserve 语义、record 事实、trigger 共用 pass）。首版 `_validate` 的名字校验比
  域正则弱（`"ab"` 会穿过写面直达 dataclass 抛 `ValueError` ⇒ 500）——改为
  `validate_schedule_name()` 由域与 registry **共用同一实现**，控制面因此稳定返回 422。
- 2026-09-16 WP-B 完成：`PeriodicDaemon` 基类把"每轮问 `due(job)`、跑完 `record()`"
  变成四个守护线程的共同循环；`start()` 同时把**同一条** `_execute_pass` 注册进 registry
  （trigger 走它）。`RetentionScheduler`/`WorkerReaperScheduler` 由各自维护 `start/stop/_run`
  改为继承基类，`WorkerReaperScheduler` 的 `worker.reaper_pass` span 保留。
  **计划外加固**：live 首次运行时观察到一次 `record()` 抛 `KeyError`（定义在两次读之间
  消失/存储读瞬时缺失，两次复跑未复现）让守护线程退出——记账失败被改成 fail-open
  （`_record`/`_due_names`/`_next_wait` 各自 try/except 退化），并补 3 条反证用例
  （记账失败仍继续跑、读面故障后能恢复、正常时按名记账）。自愈线程比它写的事实更重要。
- 2026-09-16 WP-C/D 完成：`/ops/schedules` 读面从 `ops_view.py` 的静态常量迁到
  `ops_schedules.py`（定义 + 运行事实 + 词表 + note），新增三条写方法；`ApiDeps` 增加
  `schedule_store`/`schedule_registry`，SQLite 与 PG 两组成、`run_fixtures`、`conftest`
  同侧装配；lifespan 把**同一个** registry 作为 `control` 交给四个守护线程（两个实例
  会让 trigger 找不到执行体）。未装配 store 时读面回落静态事实（`management_available=false`
  + 原因）、写面 503——诚实边界用例覆盖。
- 2026-09-16 WP-E/F 完成：console 页面改成"面板 = 登记表单 + 7 列表格 + 口径脚注"，
  行内启停/触发按钮在没有执行体或已停用时禁用并给出原因；`OpsViewPage` 的 `children`
  增加 `reload` 参数（写操作成功后重载读面，让"写面被读面消费"在 UI 上也成立）。
  stub 5 + live 2 用例；`pageSupport`/`CONSOLE_PAGE_MAP`/`CONTROL_PLANE_API` 收敛。
  结构判据判红（+90 节点）而像素判据同次绿（1.64% < 2%）⇒ 重生成两条基线并目检。
- 2026-09-16 **架构门禁判红并修复**（本 cycle 最有价值的一次失败）：首轮 m0 的  `python/tests` 红在 `tests/architecture/python/test_services_api_boundaries.py` 两项——
  `services/api/dto/ops_schedules.py` 直接 `from packages.domain.schedules import ScheduleJob`，
  破了 `api-dto-purity`（"DTO must not import packages/adapters"）。修法不是放宽断言，而是
  把取值域校验挪到域边界：DTO 的 `job` 改成 `str`（并在字段 description 里指出词表权威读面
  是 `GET /ops/schedules` 的 `jobs`），`ScheduleRegistry.create` 增加 `_coerce_job()`
  把字符串收敛成枚举、未知作业 → `InvalidInputError` 点名 `valid: lease_recovery, ...`
  ⇒ 控制面仍是 422（用例断言的"422 文本含 worker_reaper"照旧成立）。验收：
  `lint-imports --config .importlinter.api` → **2 kept, 0 broken**；
  `tests/architecture + tests/api + tests/application/ops` **447 passed**；
  OpenAPI 重生成（`ScheduleCreateDto.job` 由 enum 变 string + description，
  `docs/api/openapi.m13.json` 现为 **+303 / -2**，两条删除是迁走的旧只读路由与 `ops-view` tag）。
  **教训**：定向套件（contracts/api/ops）不会覆盖 `tests/architecture`，而新写的 DTO 很容易
  为了类型好看去 import domain——m0 的全量 pytest 才是这条门禁的执行点。
- 2026-09-16 **守护线程启动抢跑回归修复**（全量 m0 的第二个真实拦截）：`python/tests` 在
  `tests/postgres/test_m13_pg_run_e2e.py` 判红，随后 m0 卡在 71% 达 8 分钟
  （`pg_stat_activity`：一个后端 `idle in transaction` 持有 `outbox_events` 锁，另一个
  在 `TRUNCATE` 上等 relation 锁）。隔离复跑确认是**本 cycle 引入的确定性回归**：在干净
  工作树 HEAD `82e3e13` 上该用例 **6/6 通过**，带本改动的工作树上 **6/6 失败**
  （`OutOfOrderTransactionNesting`）。根因在 `ScheduleRegistry.next_wait_seconds`：
  对"尚未预约的定义"返回候选 **0.1s** ⇒ `min(fallback, 0.1)` = 0.1 ⇒ **四个守护线程在
  `create_app` 后约 100ms 同时执行首个 pass**（原本首轮要等自身 interval：relay 5s /
  reaper 15s / lease 30s），于是在请求线程使用共享 psycopg 连接时插入并发写，把请求的
  显式事务打断。修法：未预约的定义**不参与候选**（等待下界恢复为守护线程自身 interval，
  与"定义下一轮生效"口径一致），补三条钉子用例
  （registry 两条 + 守护线程一条：0.2s 时 pass 必须仍是 0）。
  复验：`tests/postgres` **70 passed**、m13 用例 **6/6 绿**、`tests/application/ops`
  **20 passed**（17 + 3）。**未改动 m13 用例一个字**。

## 影响报告

- **Domain/API/schema**：新增 `packages/domain/schedules.py`（词表 + 定义 + 运行事实）与
  `ScheduleStore` 端口（contract registry 已登记，矩阵用例含 `schedule_store`）；
  `GET /ops/schedules` 响应结构变更（**不兼容**：新增 `job/builtin/note/executor_attached/
  run_count/last_run_at/last_outcome/last_error/next_due_at/jobs/note`，`management_available`
  在装配 store 后变 `true`）+ 三条新写方法；`ScheduleCreateDto.job` 由 enum 变 **string**
  （取值域校验在服务端 `_coerce_job`，DTO 层保持不 import domain）；`docs/api/openapi.m13.json`
  重生成（+303 / -2）。
- **安全/凭据**：无凭据面变化。写面只接受既有 job 词表（不新增执行路径/不执行任意代码），
  name/interval/note 都有取值域校验；trigger 与守护线程共用 pass，不引入新的执行入口。
  策略面未改（调度不经过 policy 求值——它等价于"进程内既有守护线程的启停"，无外部副作用面）。
- **兼容性/迁移风险**：`ops_view.py` 不再暴露 `/ops/schedules`（迁到 `ops_schedules.py`），
  任何按模块名 patch 的测试需改；`SchedulesViewDto`/`ScheduleEntryDto` 从 `dto/ops_view.py`
  移到 `dto/ops_schedules.py`。SQLite 新表 `schedules`（`CREATE TABLE IF NOT EXISTS`，
  无迁移脚本需求；既有库首启自动建表并补齐 4 条内置定义）。
- **上游版本影响**：无新依赖、无版本 pin 变化（不引入 APScheduler/Celery——"不新造调度器"
  是 EC-03 的口径）。
- **下一项任务**：EC-04（worker SIGTERM 有界退出）或 EC-05（替身 harness 校验
  Idempotency-Key），以及 EC-02 剩余子句（provider 健康复核的 schema digest 漂移比对 +
  provider 凭据绑定）与 `policy.yaml` 的 `tool_pack.*` 产品决策（RECHECK-065 W-1）。

## 已知风险

- **进程内执行体的可测性**：守护线程在测试里不应真的按 interval 跑（会变慢/flaky）；
  测试用可控 pass 计数与显式 `trigger`，定时语义只做"下一轮读取定义"这一条断言。
- **PG 侧装配**：`pg_composition` 也要装配同一 store，否则写面在 PG 开发路径下 503——
  沿用既有的双组成模式（PLAN-041 起）。
- **基线重生成**：`ops-schedules` 页面必然变化 ⇒ 两个平台像素 + 结构签名都要重生成。
