---
id: RECHECK-20260915-052
plan_id: PLAN-20260915-052
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-15
completed_at: 2026-09-15
reviewer: root-agent-goal-cycle12
baseline_ref: 6e2f316
checked_head: 6e2f316+worktree
---

# RECHECK-20260915-052 — G14 实验队列与调度（cycle 12）

## 检查范围

PLAN-20260915-052 声称的交付面：`ExperimentQueueEntry` 域 + 状态机、三实现存储
（Fake/SQLite/PG + migration 014）、控制面派发器与生命周期接线、HTTP 五端点、
console live 接线、能力声明与文档同步、样例与基线。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 域状态机合法边唯一、terminal 无出边 | `tests/domain/test_experiment_queue_entity.py` 16 passed（含反证：终态对全部事件抛 InvalidTransitionError） | PASS |
| 存储三实现同契约（认领原子/到期顺序/过期重认领/取消改期只作用 QUEUED/项目内列表/计划列表） | SQLite 11 passed；PG 7 passed（真实 PostgreSQL，migration 014 已应用）；Fake 与两者同矩阵 | PASS |
| 派发器启动真实 run（不是状态翻转） | `tests/api/test_experiment_queue_api.py::test_dispatcher_starts_run_and_records_id`：`run_once()` 后条目 DISPATCHED + `run_id` 落在条目上且出现在 `GET /projects/{id}/runs`（run_ready 装配冻结 Manifest） | PASS |
| 失败可见、不静默重试 | 同文件 `test_dispatcher_fails_entry_when_plan_archived`：归档后派发 → `FAILED` + 原因含 `ARCHIVED` | PASS |
| 排期是事实 | `test_dispatcher_is_due_aware`（未到期不派发）+ `test_enqueue_with_schedule_then_reschedule`（改期往返） | PASS |
| 错误面诚实 | 未知计划 404、已归档计划 409、来源缺失/二义 422、非 UTC 时间戳 422、非 QUEUED 取消/改期 409、store 缺失 503、未知条目 404（API 10 passed + live 2 passed） | PASS |
| console live | e2e：`experiment-queue.spec.ts` 3 passed（面板渲染派发/排期条目 + 取消走 DELETE + 入队 POST 载荷）；live：`live-experiment-queue.spec.ts` 2 passed（真实 HTTP 入队→列表→改期→取消→重复取消 409；未知计划 404、来源二义 422） | PASS |
| 能力声明与代码一致 | `apps/web/src/navigation/pageSupport.ts`（去掉 queue/schedule 禁用，改 `disabledOperations: ["reproduce-run"]`）+ `docs/frontend/CONSOLE_PAGE_MAP.md` G14 行改为已交付 + 缺口（复现执行、日历/矩阵视图）保留；守卫测试 76 passed | PASS |
| 执行装配单一来源 | `services/api/run_execution.py` 承载 `POST /runs` 与派发器共用的装配；`routers/runs.py` 改为引用（无第二份启动实现） | PASS |
| 设计基线 | `portfolio-experiments` 的 win32 + linux 基线按新页面重生成（win32 本机、linux 在 pinned playwright noble 容器内），逐一目检 | PASS |
| 治理与门禁 | 全量 `tests/api+domain+adapters+postgres+contracts` 1528 passed / 4 skipped；`tests/tooling/test_python_source_limits.py` + `tests/architecture` 873 passed；web lint/typecheck/unit/build 全绿；stub e2e 39 passed；live e2e 19 passed；OpenAPI 快照重新生成后契约测试绿 | PASS |

## 收口复验补充（cycle 12 续跑，m0 23/23）

首轮本地 m0 未直接通过；逐项定位后发现 4 处**真实缺口**（3 处由本轮改动引入，1 处为既有
测试缺陷）与 1 处环境噪声，逐条修正后 `profile=m0; 23 deterministic checks` 全绿。

| 复验项 | 事实 | 处置 |
| --- | --- | --- |
| mypy（`python/typecheck`） | 3 处：派发器 `store` 句柄被注解成 `object`（无法证明 Port 方法存在）；`tests/application/test_m12_clean_run_persistence.py` 与 `tests/tooling/test_个人生产续审v2.py` 的手写 `_ExperimentStore` 未覆盖扩展后的 Port | 派发器改为返回 `ExperimentStore | None`（并让三个调用点复用同一属性）；两处测试改为共享 `adapters.fakes.experiment_store.FakeExperimentStore`（删掉手写 fake），断言改为**经 Port 回读**（未知 id 抛错，比原 `in dict` 更强） |
| 50 行函数上限（`tests/tooling/test_python_source_limits.py`） | 上述断言改写把 `test_reference_run_persists_restorable_truth_closure` 推到 52 行 | 抽 `_assert_persisted_closure` 助手（断言强度不变） |
| `tests/distributed/test_scenarios.py::test_scenario_g_drain_stops_claims` | 真实竞态：测试读到 `REGISTERING` 后自行补 `HANDSHAKE_OK`，但 gateway 的 register 路径在同一窗口内也会迁移 ⇒ 输家抛 `InvalidTransitionError(READY, HANDSHAKE_OK)`（全量跑复现，首轮 m0 红） | 删除与 gateway 竞争的重复迁移，改为等待 worker 自行落定 `READY` 再 drain（前置条件更严格）；隔离复跑 5/5 绿，随后全量 `python/tests` 绿 |
| `typescript/lint`（根 eslint，覆盖 `apps/web/tests/e2e`） | `live-experiment-queue.spec.ts` 使用 inline import type；`playwright.config.ts` 的 `testIgnore` 未包含新增 live spec ⇒ **stub 套件把 live 用例一并收进来**（无 live 服务必失败） | 改为顶层 `import type { Page }`；`testIgnore` 补 `experiment-queue` 并注明「新增 live spec 时两处必须同步」；重跑 stub 39 passed / live 19 passed |
| `framework/run_cursor_framework_evals`（环境噪声，非缺陷） | 首跑 `evolution_gate.py` 的 `atomic_json` 在 `os.replace` 处报 `WinError 5 拒绝访问`（`.cursor/runtime/evolution_state.json` 被同机并发进程占用） | 单项复跑 PASS；全量复跑 PASS。属框架自身，本轮只登记（见 W-10） |

## CI 与安全面（收口提交 629f757）

| 项 | 事实 |
| --- | --- |
| CI | run `34952933291`（M0 Quality Gates，head 629f757）：**六个 job 全 success** —— quality-ubuntu-latest / quality-windows-latest / console-frontend / container-quality / eval-gate / collector-quality。collector-quality 继 cycle 11 修复后本轮再次 success（runs #61–#69 的持续失败未复现）。 |
| 安全扫描 | Mimosa 密封深扫 `scan-2026-09-15T09-33-06.821Z-d2729fe03dd7`，seal `sha256:e09328e1634f381eb4bb8f4aad8894f8240906c2493e01fac3c02af9db7be384`，36 findings / 182 packages / 1 matched advisory；**逐条比对后确认与 PA-1R 已处置清单为同一集合**（`tools/probes/*`、gitignored 的 `scratch/probe_*.py` 与 `artifacts/钻孔官方API_v12/*`、`examples/experiments/m12_reference_classification.py`、`packages/application/protocol_authoring/service.py`、`services/worker/__main__.py`），**本轮改动零新增 finding**。证据边界 `static_only_no_runtime_execution`、`verdictEffect: none` —— 本记录**不宣称项目安全**。 |

## 结论

result: **PASS_WITH_WARNINGS**

交付面成立：队列有真实消费者、状态只来自域状态机、认领原子、失败可见、排期是
事实、错误面诚实、console live、能力声明与文档同步。以下为如实登记的告警（不构成
阻塞，但必须随本记录保留）。

## 告警

- W-1（at-least-once 的可见代价）：认领过期（进程崩溃/停机中断）会**再次启动 run**；
  条目上的 `run_id` 是最近一次结果，两个 run 之间没有去重。文档与 `dispatch_note`
  写明这是刻意语义（与租约/任务一致），但运维需要知道"同一排期可能对应两次启动"。
- W-2（无 outbox 事件）：队列入队/派发/取消不发新的 outbox 事件类型（与 PLAN-046/048
  同口径），队列状态变化只能轮询 `GET /projects/{id}/experiment-queue` 观测。
- W-3（派发串行）：派发在控制面进程内同步执行 run，因此队列串行推进、吞吐与 API 侧
  run 同阶；多 API 实例并发由原子认领保证不重复认领，但不提升吞吐（本轮不引入执行面
  扩容）。停机不打断在途 run（留给认领 TTL 恢复）。
- W-4（设计基线容差）：本轮页面改动落在首屏之下 + 描述文案，`--update-snapshots` 在
  2% 容差下**未自动重写**基线（`git status` 为空）；因此两条基线均按"删除后重生成"
  强制刷新以保证基线反映当前页面。该现象说明 `maxDiffPixelRatio: 0.02` 对首屏之下的
  改动不敏感，作为门禁灵敏度事实登记（未改门禁参数）。
- W-5（计划无项目归属）：`ExperimentPlan` 域无 `project_id`，`GET /experiment-plans`
  因此是全局列表；队列条目自身带 `project_id`（派发按它解析项目设置）。与
  `GAPS.multiProject` 既有诚实标注一致，未在本轮扩展计划域。
- W-6（WS1 遗留未动）：`infra/compose/research-validation.yaml` 的证据目录供给缺口
  （RECHECK-20260915-051 W-1）本轮仍未处理，与 G14 无关。
- W-7（结构型 fake 的漂移代价）：Port 扩展后，两处**手写** `ExperimentStore` 测试助手立刻
  失去结构兼容（mypy 捕获）。已统一到共享 `FakeExperimentStore`；教训是"测试替身必须
  来自单一实现"，否则 Port 每次演进都要人工追平（本轮真发生过）。
- W-8（distributed 场景同族模式）：G 场景的 check-then-act 已修，但「读注册状态 → 条件
  迁移」这一模式在其它 distributed 场景仍可能存在（本轮只修了复现到的那一处，未做全量
  模式扫描）。
- W-9（双 playwright 配置的人工同步点）：stub 配置的 `testIgnore` 与 live 配置的 `testMatch`
  是两份手工列表，新增 live spec 时若漏改，stub 套件会静默收进 live 用例（本轮已发生，
  已修 + 加注）。更彻底的做法（统一 `live-*.spec.ts` 约定 glob 或共享常量）未做。
- W-10（框架自身的并发写）：`.cursor/hooks/evolution_gate.py` 的 `atomic_json` 在 Windows
  上遇到被占用的 `evolution_state.json` 会以 `WinError 5` 失败，令 `framework/run_cursor_framework_evals`
  偶发红（本轮首跑即如此，单项复跑 PASS）。门禁因此对同机并发敏感，属框架侧，未改。

## 复现

```
# 本地 m0（DSN 固化；PATH 需含 .venv/Scripts）
sh scratch/run-m0-cycle12.sh          # profile=m0; 23 deterministic checks
# 域 + 存储
python -m pytest tests/domain/test_experiment_queue_entity.py \
  tests/adapters/sqlite/test_experiment_queue_sqlite.py -q
RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os \
  python -m pytest tests/postgres/test_experiment_queue_pg.py -q
# 派发 + HTTP 面
python -m pytest tests/api/test_experiment_queue_api.py -q
# distributed 场景（修复后稳定性）
RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os \
  python -m pytest tests/distributed/test_scenarios.py -q -k drain_stops_claims
# console（stub 与 live 两套配置都必须显式排除/包含新 spec）
cd apps/web && pnpm run test:e2e && pnpm run test:e2e:live
# 契约快照
python tools/gen_openapi.py && python -m pytest tests/contracts/test_openapi_snapshot.py -q
```
