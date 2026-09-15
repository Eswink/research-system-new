---
id: PLAN-20260915-052
slug: experiment-queue-and-scheduling
title: G14 实验队列与调度：域 + 存储 + 派发器 + API + console live
status: DONE
created_at: 2026-09-15
updated_at: 2026-09-15
parent_goal: GOAL-20260912-001
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260912-001 cycle 12：用户 2026-09-15 会话要求「继续 goal 文件循环迭代 10-20 次，让系统更完整」⇒ 人工决策点②（实验队列 G14 是否续做）判为续做，EC-04 由 BLOCKED 转 PENDING，本计划交付 G14。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-052-experiment-queue-and-scheduling.md
memory_entries:
  - MEM-20260915-029
---

# PLAN-20260915-052 — G14 实验队列与调度（cycle 12）

## 目标

把 `portfolio/experiments` 上诚实禁用（`disabledOperations: ["queue","schedule"]`）的两项
操作变成**有真实消费者**的能力，而不是第二个"注册了却没人跑"的空壳：

1. `ExperimentQueueEntry` 域实体 + 状态机（QUEUED → DISPATCHING → DISPATCHED | FAILED；
   QUEUED → CANCELLED；DISPATCHING → QUEUED 仅限认领过期重认领）；
2. 持久化（SQLite 开发路径 + PostgreSQL canonical state，新增 migration 014）与
   **原子认领**（PG `FOR UPDATE SKIP LOCKED`；SQLite 单事务条件更新）；
3. 控制面派发器：按 `not_before`/创建时间认领到期条目，走**与 `POST /runs` 完全相同的
   装配链**启动 run，并把 `run_id`/失败原因写回条目；
4. HTTP 面（入队 / 列表 / 改期 / 取消 + 计划列表）与 console live 接线；
5. 文档与能力声明同步：pageSupport 去掉 `disabledOperations`、CONSOLE_PAGE_MAP G14 行
   改为已交付，并如实登记仍未交付的部分（日历/矩阵视图）。

## 诚实边界（不得越界）

- **不是第二套执行器**：派发复用 `RunOrchestrationService.start_run` 的同一装配
  （`services/api/run_execution.py`），进程内同步执行 run；派发器**串行**认领-派发，
  这是"HTTP 面 run 同步执行"既有事实的延续，不是新增并行执行面。
- **at-least-once，不假装 exactly-once**：认领是原子的（`QUEUED → DISPATCHING` 条件
  更新），认领过期（进程崩溃/停机中断）后条目会被**重新认领并再次派发**；这与既有
  租约/任务语义一致，条目上如实记录失败原因与 run_id。
- **不伪造队列状态**：条目状态只来自域状态机；派发失败（协议不可解析、计划已归档、
  预检失败）以 `FAILED + reason` 呈现，不静默重试。
- 未交付面继续诚实标注：实验日历/矩阵视图（界面呈现）、跨 run 排队公平性/优先级、
  队列事件的 outbox 投影（本轮不发新事件类型，登记为 WARN）。

## 范围

- WP-A（域与存储）：`packages/domain/experiment_state.py`（新增 `ExperimentQueueState`）、
  `packages/domain/experiment_queue.py`（新：`QueueProtocolSource`、`ExperimentQueueEntry`）、
  `packages/application/ports/experiment_store.py`（新增队列条目 + `list_plans`）、
  `adapters/contracts/experiment_rows.py`（编解码）、
  `adapters/{fakes,sqlite,postgres}/experiment_store.py`、
  `adapters/postgres/migrations/014_experiment_queue.sql`。
- WP-B（派发）：`services/api/run_execution.py`（新：从 `routers/runs.py` 抽出执行装配）、
  `services/api/experiment_queue.py`（新：`ExperimentQueueDispatcher`）、
  `services/api/app.py`（lifespan 接线）。
- WP-C（API）：`services/api/routers/experiments.py`、`services/api/dto/experiments.py`。
- WP-D（前端与文档）：`apps/web/src/api/{experimentClient,client,types}.ts`、
  `apps/web/src/features/experiments/ExperimentQueuePanel.tsx`（新）、
  `apps/web/src/navigation/pageSupport.ts`、`docs/frontend/CONSOLE_PAGE_MAP.md`、
  `apps/web/tests/e2e/*`（stub + live + design-fidelity 基线重生成）。
- WP-E（收口）：本地 m0 分组、RECHECK-052、提交/推送/CI 复验、GOAL 记账。

## 验收条件

- [x] AC-01（WP-A）：域状态机非法迁移抛错；三实现（Fake/SQLite/PG）对同一状态矩阵
  给出**一致**结果（含并发认领只成功一次、认领过期重认领、取消/改期只作用于 QUEUED）。
- [x] AC-02（WP-B）：派发器端到端把到期条目派发成真实 run（`run_id` 回写、条目
  DISPATCHED），失败路径以 `FAILED + reason` 落地；停机中断的认领可被重新派发。
- [x] AC-03（WP-C）：入队/列表/改期/取消四条端点 + 计划列表；错误面映射诚实
  （未知计划 404、已归档计划 409、来源不可解析 404、非 QUEUED 的取消/改期 409）。
- [x] AC-04（WP-D）：console 队列面板 live（入队/改期/取消/run 跳转）；pageSupport
  与 CONSOLE_PAGE_MAP 与实际能力一致；stub + live e2e 绿；design-fidelity 基线
  （win32 + linux）按批准更新。
- [x] AC-05（WP-E）：m0 本地分组全绿 + 治理 validate 绿 + RECHECK-052；GOAL/ALL_PLAN
  记账与实况一致。

## 实施清单

- [x] WP-A 域 + 存储 + migration
- [x] WP-B 执行装配抽取 + 派发器 + lifespan
- [x] WP-C API + DTO
- [x] WP-D console live + 能力声明 + e2e + 基线
- [x] WP-E 本地门 + RECHECK + 提交/CI + 记账

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A | 域 16 passed（含终态反证）；SQLite 队列 11 passed；PG 队列 7 passed（真实 PG + migration 014） | PASS |
| WP-B | `tests/api/test_experiment_queue_api.py` 10 passed，其中派发用例断言 run 行落在控制面、失败用例断言 `FAILED + ARCHIVED` 原因 | PASS |
| WP-C | 同文件 HTTP 面用例（404/409/422/503 全覆盖）；OpenAPI 快照重新生成后契约测试绿 | PASS |
| WP-D | stub e2e 39 passed（+3）；live e2e 19 passed（+2）；`portfolio-experiments` win32 + linux 基线重生成并目检；pageSupport/CONSOLE_PAGE_MAP 同步 | PASS |
| WP-E | 全量 `tests/{api,domain,adapters,postgres,contracts}` 1528 passed / 4 skipped；source-limits + architecture 873 passed；web lint/typecheck/unit(76)/build 全绿；RECHECK-052 = PASS_WITH_WARNINGS（W-1..W-6） | PASS |
| WP-E（收口复验） | 本地 m0 首跑 4 红（mypy 3 处 / 50 行函数 / distributed 场景 G 竞态 / 根 eslint + stub 套件误收 live spec）逐条修正后 **`profile=m0; 23 deterministic checks` 全绿**；stub e2e 39 passed、live e2e 19 passed 复跑；RECHECK-052 增补收口复验段 + W-7..W-10 | PASS |

## 已知风险

- 派发在控制面进程内**同步**执行 run：条目派发期间派发线程被占用，队列呈串行推进；
  多 API 实例并发时由原子认领保证不重复派发，但吞吐不上行（本轮不引入执行面扩容）。
- 认领过期重认领会**再次启动 run**（at-least-once）：这是既有语义，不得被读作"重复执行
  是 bug"，但必须在响应/文档/复检中写清；同一 run 的去重不在本轮范围。
- 队列条目不发 outbox 事件（与 046/048 同口径），登记为 WARN。
- 前端改动会改变 `portfolio-experiments` 设计基线（win32 + linux 各 1 张），
  必须在本 cycle 内重生成并目检。

## 状态历史

- 2026-09-15 创建（IN_PROGRESS）：GOAL-20260912-001 cycle 12，方向 = 续做 G14
  （用户 2026-09-15 会话判定），产出并入 EC-04。
- 2026-09-15 WP-A 完成：`ExperimentQueueState`（QUEUED→DISPATCHING→DISPATCHED|FAILED、
  QUEUED→CANCELLED、DISPATCHING→QUEUED 仅认领过期）+ `QueueProtocolSource`/
  `ExperimentQueueEntry` + Port 扩展（队列 6 方法 + `list_plans`）+ 三实现 + migration 014。
  期间发现并修正一个真实缺陷：取消/改期的状态冲突在存储层抛的是域
  `InvalidTransitionError` 而非 Port 的 `InvalidInputError`（三实现同步修正）。
- 2026-09-15 WP-B 完成：`services/api/run_execution.py`（从 `routers/runs.py` 抽出的
  唯一启动装配，HTTP 面与派发器共用）+ `services/api/experiment_queue.py`
  （`ExperimentQueueDispatcher`：原子认领 → 同链启动 → 回写 run_id/失败原因；
  认领 TTL 恢复）+ `app.py` lifespan 接线（观测 scope/metric 词汇表增量同步）。
- 2026-09-15 WP-C 完成：`routers/experiment_queue.py` 五端点 + DTO + 错误映射；
  OpenAPI 快照重新生成。
- 2026-09-15 WP-D 完成：`experimentClient` + `ExperimentQueuePanel`/`ExperimentEnqueueForm`
  + 计划面板改为读服务端 `GET /experiment-plans`；pageSupport / CONSOLE_PAGE_MAP /
  OPERATIONS_RUNBOOK 同步；stub + live e2e 与两条设计基线更新。
- 2026-09-15 WP-E 完成：本地门全绿 + RECHECK-052 = PASS_WITH_WARNINGS ⇒ 本计划 DONE。CI 复验结论回写 GOAL。
- 2026-09-15 WP-E 收口复验（续跑）：首轮 m0 4 红逐条定位并修正——(1) mypy 3 处
  （派发器 `store` 注解为 `object`；两处手写 `ExperimentStore` 测试助手未随 Port 扩展，
  改为共享 `FakeExperimentStore` 并让断言经 Port 回读）；(2) `test_m12_clean_run_persistence.py`
  主用例被推到 52 行 ⇒ 抽 `_assert_persisted_closure`；(3) `test_scenario_g_drain_stops_claims`
  的 test 侧 check-then-act 竞态（与 gateway 的 `HANDSHAKE_OK` 竞争）⇒ 改为等待 worker
  自行落定 READY；(4) 根 eslint inline import type + `playwright.config.ts` 未排除新 live spec。
  修正后 m0 23/23、stub/live e2e 复跑全绿。

## 影响报告

- 改动：新增 `packages/domain/experiment_queue.py`、`services/api/run_execution.py`、
  `services/api/experiment_queue.py`、`services/api/routers/experiment_queue.py`、
  `adapters/postgres/migrations/014_experiment_queue.sql`、
  `apps/web/src/features/experiments/ExperimentQueuePanel.tsx` +
  `ExperimentEnqueueForm.tsx`、`apps/web/tests/e2e/{stub-routes-experiments,experiment-queue.spec,live-experiment-queue.spec}.ts`；
  修改 `packages/domain/experiment_state.py`、`packages/application/ports/experiment_store.py`、
  `adapters/{contracts/experiment_rows,fakes,sqlite,postgres}/experiment_store.py`、
  `services/api/{app,dto/experiments,routers/{runs,experiments}}.py`、
  `packages/application/observability/{signals,attributes}.py`、
  `apps/web/src/api/{client,types,experimentClient}.ts`、
  `apps/web/src/features/experiments/{ExperimentsPage,ExperimentPlanPanel}.tsx`、
  `apps/web/src/navigation/pageSupport.ts`、`apps/web/playwrightLive.config.ts`、
  两条设计基线、`docs/{frontend/CONSOLE_PAGE_MAP,operations/OPERATIONS_RUNBOOK}.md`；
  收口复验追加 `apps/web/playwright.config.ts`（live spec 排除同步）、
  `apps/web/tests/e2e/live-experiment-queue.spec.ts`（顶层 type 导入）、
  `tests/distributed/test_scenarios.py`（场景 G 竞态）、
  `tests/application/test_m12_clean_run_persistence.py` + `tests/tooling/test_个人生产续审v2.py`
  （共享 Fake + Port 回读断言）、`services/api/experiment_queue.py`（store 句柄类型）。
- lint/typecheck/test：ruff check/format 绿；mypy 绿（含上述 3 处修正）；
  web eslint（`--max-warnings 0`）/tsc/unit 76/build 绿；根 `eslint .` 0 error；
  全量 `tests/{api,domain,adapters,postgres,contracts}` 1528 passed / 4 skipped；
  `tests/tooling/test_python_source_limits.py` + `tests/architecture` 873 passed；
  stub e2e 39 passed；live e2e 19 passed；**本地 m0 23/23 PASS**。
- Domain/API/schema：**新增**域实体 + 状态机（`ExperimentQueueState`）、Port 方法
  （队列 6 + `list_plans`）、PG migration 014（新表 `experiment_queue` + 2 索引）、
  5 条新端点 + `/experiment-plans`；OpenAPI 快照更新。既有实体/端点语义未变。
- 安全/凭据：无凭据面变更；无新依赖、无上游镜像/pin 变更；派发复用的是既有 run 装配
  （同一 preflight/policy/budget 门链），未新增绕过路径；队列端点沿用既有幂等中间件。
- 兼容性/迁移风险：新增表为纯增量（`CREATE TABLE IF NOT EXISTS`，无 FK/无回填）；
  `research-validation.yaml` 等服务集合契约未触碰。行为新增：控制面进程多了一个守护线程
  （15s 周期、telemetry fail-open）；未启用队列的环境无条目、无副作用。
- 上游版本影响：无。
- 下一项任务：GOAL-20260912-001 达 ACHIEVED 条件（EC-04 归零）⇒ 收口复检；
  长程 10-20 次迭代由 GOAL-20260912-002 承接（候选缺口表见 GOAL-001「终止与收口」）。
