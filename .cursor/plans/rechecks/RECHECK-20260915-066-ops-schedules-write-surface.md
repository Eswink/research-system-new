---
id: RECHECK-20260915-066
plan_id: PLAN-20260915-066
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-003-cycle4
baseline_ref: 82e3e13
checked_head: 82e3e13+worktree
---

# RECHECK-20260915-066 — ops 调度用户可见写面（GOAL-003 cycle 4 / EC-03）

## 检查范围

PLAN-20260915-066 声称的交付面：`packages/domain/schedules.py`、
`packages/application/ports/schedule_store.py` + `packages/application/ops/schedule_registry.py`、
`adapters/sqlite/schedule_store.py` + `adapters/fakes/schedule_store.py`（含 contract registry
与矩阵登记）、`services/api/scheduler.py` 的四条守护线程接上定义读面、
`services/api/{dto,routers}/ops_schedules.py` + `services/api/schedule_support.py`、
两组成装配（`composition.py`/`pg_composition.py`/`run_fixtures.py`/`conftest.py`）+
`app.py` 的 control 接线与路由注册、`tests/api/test_ops_schedules_api.py`、
`tests/application/ops/`（registry 9 + daemon 8）、OpenAPI 重生成 + 契约断言、
console 页面/表单/行内动作/7 列表格 + 有状态替身 + stub/live 用例、四份文档与
`pageSupport` 收敛、两条设计基线重生成。

**未覆盖**（如实登记，见告警）：调度定义的删除/归档、cron 表达式与日历视图、
"新增自定义 pass"（EC-03 口径明确不允许）；调度写面不过 policy 求值。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 执行体没被换成第二套调度器（EC-03 核心口径） | `grep` 全仓无 AP scheduler/Celery 引入；`PeriodicDaemon` 是 `services/api/scheduler.py` 里**同一个**循环，四条守护线程都是它的子类；`serve/api/app.py` 的 `_lifespan` 用 `deps.schedule_registry` 作 `control` | PASS |
| `trigger` 与定时 pass 是**同一个函数对象** | `test_trigger_runs_the_registered_daemon_pass`：`start()` 注册后 `trigger(name)` 使守护线程自己的计数器 +1；API 侧 `test_trigger_runs_registered_pass_and_records_facts`：注入计数 pass 后 `calls == ["pass"]` | PASS |
| 写面被**执行体读面**消费（可证伪，AC-03） | `test_disable_is_consumed_by_the_daemon_loop`：真实线程 + 可控时钟，停用后 0.5s 内 `run_count` 冻结、`due()` 返回空；重新启用后继续增长。API 侧同结论（`due()` 空 + trigger 409） | PASS |
| 运行事实诚实（AC-01） | `test_read_surface_reports_executor_attachment_honestly`：未跑过的定义 `last_outcome=null`、`next_due_at=null`、`executor_attached=false`（本装配只有 lease 守护线程），没有伪造成功 | PASS |
| 取值域与冲突语义（AC-02） | API 用例：词表外 job → 422 且文本点名合法值；interval 0.5 → 422；`Bad-Name` → 422；内置名 → 409；重名 → 409。域与 registry **共用** `validate_schedule_name()`（首版两套校验会让 `"ab"` 变成 500，已修） | PASS |
| trigger 的失败不伪装（AC-04） | 失败 pass → HTTP 200（请求成功）但 `last_outcome=FAILED` + `last_error="reaper pass exploded"`；未知 name → 404；有定义无执行体 → 409（`no executor attached`） | PASS |
| 未装配 store 时的诚实边界 | `test_write_surface_is_honest_without_registry`：读面回落静态事实 + `management_available=false` + 原因、事实字段全 null；POST/PATCH/trigger 全 503 | PASS |
| 执行体韧性（计划外加固） | `test_daemon_survives_bookkeeping_failure`（`record` 抛错仍继续跑）、`test_daemon_recovers_after_read_failure`（`due` 抛错 → 不跑不退出，读面恢复后重新开跑）、`test_daemon_records_facts_when_bookkeeping_works`（正常路径按名记账） | PASS |
| console 可操作且被读面消费（AC-05） | stub `schedules-write.spec.ts` **5 passed**（登记 → `0 次 · 未运行 · UNKNOWN`；触发 → `1 次 · OK`；停用 → OFF 且触发按钮 disabled；无执行体 → disabled + 标注；409 文本落在 `schedule-create-error`）；live `live-schedules-write.spec.ts` **2 passed**（真实 uvicorn + SQLite：登记/触发/停用/409/复原/422） | PASS |
| `disabledOperations` 收敛（AC-05/AC-06） | `pageSupport` 的 `ops/schedules` 项已无 `disabledOperations`；`GAPS.schedules` 改写为"已可写 + 仍缺什么"；`CONSOLE_PAGE_MAP.md` 页面段与 G7 行同步；`CONTROL_PLANE_API.md` 新增「调度（EC-03）」段 | PASS |
| OpenAPI 写方法 + 契约（AC-06） | `tools/gen_openapi.py` 重生成（**+313 行**，仅新增三条路径与 DTO）；`test_openapi_contains_ops_schedule_write_methods` 断言路径/方法/描述里的 404·409·last_outcome；契约套件 **365 passed, 56 skipped** | PASS |
| 结构判据在真实改动上再次拦截（AC-07） | 未设 `UPDATE_OUTLINES` 跑 `design-fidelity`：**红**，`drifted=["ops-schedules"]`，节点 **170 → 260**（新 form/panel/7 列表格/note）；输出存 `scratch/cycle4-design/outline-diff.txt` | PASS |
| 像素判据同一次改动仍不报警 | 实测 **15093 px = 1.64%** < 2% 阈值（`scratch/cycle4-design/pixel-ops-ratio.json`）⇒ 与 cycle 1/3 的实测区间一致，结构判据补的正是这块盲区 | PASS（缺口已知，非本轮引入） |
| 基线重生成 + 目检 | `UPDATE_OUTLINES=1 …design-fidelity`（diff = 1 行）；`gen_linux_baseline_route.sh ops-schedules`（pinned `v1.56.1-noble`）+ 本机 `--update-snapshots` 重生成 win32；两张 PNG 目检（表单/7 列表格/执行体 chip/行内动作/口径脚注渲染正确，无溢出、无缺样式）；`verify_linux_outlines.sh` → `PASS: 33 条结构签名跨平台一致（win32 == linux）` | PASS |
| 架构边界（DTO 纯度） | 首轮 m0 判红：`test_control_plane_dto_does_not_import_domain` + `test_control_plane_api_has_no_adapter_leak_outside_composition`（同一根因）。`services/api/dto/ops_schedules.py` 曾 `from packages.domain.schedules import ScheduleJob` ⇒ `api-dto-purity` BROKEN。修法：DTO 的 `job` 改 `str`、词表校验下沉到 `ScheduleRegistry.create` 的 `_coerce_job`（未知作业 → 422 点名 `valid: ...`）。复验：`lint-imports --config .importlinter.api --no-cache` → **2 kept, 0 broken**；`tests/architecture/python/test_services_api_boundaries.py` **2 passed**。**未放宽任何断言**（那两个测试逐字未动） | PASS（修复后） |
| 全量门禁（AC-07） | stub e2e **77 passed** / live e2e **35 passed** / web 单测 **76 passed** / `pnpm lint` 0 error（1 条既有 soft warning）/ `tsc --noEmit` 通过 / 根 `eslint .` 0 error / 契约 **365 passed, 56 skipped** / `tests/architecture+api+application/ops` **447 passed** / m0 **PASS: profile=m0; 23 deterministic checks**（首轮红两处并按序修复：① mypy 2 处——unused type-ignore + `Any` 返回；② 架构门禁 2 项——DTO import domain） | PASS |
| 安全扫描（sealed） | Mimosa deep scan `scan-2026-09-16T09-58-50.302Z-c66ac1c53225`，seal `sha256:41512b605b86fb66c22651d3a0ba1aed987098a5d7dad369d58311ba593c21ef`：**36 findings（3 high / 28 medium / 5 low），182 packages，1 条离线 advisory 命中**；按路径过滤后**与本轮改动相关的命中为 0**（全部落在既有文件：`tools/probes/**`、`scratch/probe_*.py`、`examples/experiments/m12_reference_classification.py`、`packages/application/protocol_authoring/service.py`、`services/worker/__main__.py`、`artifacts/钻孔官方API_v12/**`）。计数与上一轮（cycle 3，36 条）一致 ⇒ 本轮未引入新类别 | PASS |

## 告警

- **W-1（计划外加固，根因未复现）**：live 首次运行时观察到一次守护线程因
  `ScheduleRegistry.record()` 抛 `KeyError('worker_reaper')` 而**退出**（读日志：`record` 内
  两次 `get_definition` 之间定义"消失"）。三次复跑均未复现；未定位到具体机制
  （`delete_definition` 无调用方、单实例单 store、`check_same_thread=False` 共享连接）。
  处置：把记账/读面调用改成 **fail-open**（`_record`/`_due_names`/`_next_wait` 各自
  try/except 退化），并补 3 条反证用例。取舍：事实可能滞后一轮，但读面可见（`last_outcome`
  停在旧值、`next_due_at` 不前进），而"自愈线程消失"是不可见的——两者相权取其轻。
  **仍未理解的部分如实登记**，不做"已修复"的断言。
  **补记（同日，W-9 定位后）**：W-9 查明首版 `next_wait_seconds` 会让**四个守护线程在
  app 启动约 100ms 后同时开跑**——那正是"启动期初始化写仍在进行、守护线程已在读同一份
  共享 store"的窗口，与 W-1 的观测（读面在两次读之间"看不到"定义）是同一类竞态。
  两个现象因此**可能同源**：W-9 的修复移除了那个窗口（只对"未预约的定义"敏感，
  不再是"所有守护线程同时抢跑"），但**没有直接复现 W-1 的 KeyError**，故不宣称 W-1 已解决。
- **W-9（已定位并修复的回归）**：首版 `ScheduleRegistry.next_wait_seconds` 对
  "尚未预约的定义"（`due_at is None`）返回 **0.1s** 作为候选 ⇒ `min(fallback, 0.1)` = 0.1，
  于是**四个守护线程在 `create_app` 后约 100ms 同时执行首个 pass**，而它们各自原本的
  首轮等待是自身 interval（relay 5s / reaper 15s / lease 30s）。后果是**真实回归**：
  `tests/postgres/test_m13_pg_run_e2e.py::test_pg_stores_run_to_succeeded` 在
  隔离工作树 HEAD `82e3e13` 上 **6/6 通过**，带该行为的工作树上 **6/6 失败**
  （`psycopg.transaction.OutOfOrderTransactionNesting`：请求线程的 `PostgresEvidenceLedger`
  事务被守护线程在**同一条共享 psycopg 连接**上打断）。另有一次合并跑把守护线程留在
  `idle in transaction`，使后续 `TRUNCATE` 永久阻塞（m0 卡在 71% 8 分钟，`pg_stat_activity`
  两条后端：一个 idle in transaction、一个等 relation 锁）。
  修法：**未预约的定义不参与候选**（`continue`），等待下界恢复为守护线程自身 interval——
  与"定义下一轮生效"的口径一致。钉子用例：
  `test_wait_seconds_never_sprints_before_the_daemons_own_interval`、
  `test_wait_seconds_ignores_disabled_definitions`、
  `test_daemon_does_not_sprint_at_startup`（0.2s 时 pass 必须仍是 0）。
  复验：`tests/postgres` **70 passed**、m13 用例 6/6 绿、`tests/application/ops` **20 passed**。
  **没有放宽任何断言**（m13 用例逐字未动）。
- **W-2（范围）**：本面不提供 DELETE（自定义定义只能停用）、不支持 cron 表达式与日历视图、
  不支持新增自定义 pass（EC-03 口径就是"不新造执行路径"）。这三项已写进
  `pageSupport.GAPS.schedules` 与 `CONSOLE_PAGE_MAP.md`，不藏在代码里。
- **W-3（替身与真后端的差异）**：`stub-routes-schedules.ts` 里只有 `lease_recovery` 带执行体
  （镜像测试装配），且 trigger 只是"写回运行事实"而不是真的跑一遍 pass；替身的作用是让
  console 状态机（启用/停用/无执行体/错误呈现）可测。**"trigger 真的执行了 pass"这一条
  由后端用例（同一函数对象 + 计数器）与 live 套件证明**，不由替身证明。
- **W-4**：`run_count`/`last_run_at`/`last_outcome` 是**本进程观测**（进程重启归零），
  不是持久事实；读面字段名与文案按此写（"运行事实"），`CONTROL_PLANE_API.md` 亦注明。
  若后续要"跨重启的运行历史"，那是另一个存储面（本轮不做）。
- **W-5（语义）**：定义名与 job 名是**两个维度**——内置定义与 job 同名，但用户可以为同一个
  job 登记多条定义（如 `outbox_relay_fast` 挂 `outbox_relay`），此时守护线程每轮会对该 job
  触发**多次** pass。当前只在 `note` 与页面文案里说明；界面没有"该 job 已有多条定义"的提示。
- **W-6（策略面）**：调度写面**不过 policy 求值**（等价于启停进程内既有守护线程，无外部
  副作用面），因此没有新增 capability 词表项，也不受 `examples/config/policy.yaml` 的
  `default_effect: DENY` 影响。若产品要求"调度变更也走审批"，需要新增 `schedule.*` 能力
  并接 policy——登记为后继候选，不在本轮范围。
- **W-7**：`apps/web/tests/e2e/live-api-workflow.spec.ts` 因本轮断言更新达到 **403 行**
  （既有 soft limit 300 的警告，本轮 +3 行）；根 `eslint .` 只报警告不失败，但该文件已接近
  拆分阈值。
- **W-8（架构代价，已接受）**：为守住 `api-dto-purity`，`ScheduleCreateDto.job` 由域枚举变成
  字符串 ⇒ **OpenAPI 里不再有 enum 列表**，客户端无法只凭 schema 发现词表；补偿是把词表的
  权威读面写成字段 description（"可选值见 `GET /ops/schedules` 的 `jobs` 字段"），
  且 422 消息点名合法值。这是"DTO 不 import domain"的直接代价——**不重复词表**（重复即漂移）
  优先于 schema 自解释。

## 结论

result: **PASS_WITH_WARNINGS**

EC-03 的交付面成立，且核心口径（**执行体仍是既有守护线程**、`trigger` 复用同一条 pass、
启停被执行体读面消费）由三组独立证据支撑：registry 单测（语义）、daemon 真实线程用例
（消费）、API/live 用例（HTTP 边界与真实 SQLite）。未装配 store 的诚实边界、未跑过的定义
的诚实事实、pass 失败的诚实留痕都被证伪式地覆盖。两条设计基线与跨平台一致性照旧全绿，
结构判据在第二次真实改动上再次先于像素判据报警（1.64% < 2%）。

W-1 是**计划外加固**且根因未复现——它改变了失败模式（记账失败不再杀死自愈线程），
但不改变对外语义；其余告警都是范围/语义登记，无隐藏缺口。

**本轮门禁真正发挥作用的一次**：全量 m0 的 `python/tests` 判红于架构边界两项
（`services/api/dto/ops_schedules.py` 直接 import domain 的枚举）。定向套件
（contracts / api / application.ops）全绿也遮不住它——`tests/architecture` 只在全量跑里。
修复方式是**把校验下沉到域边界**（DTO `job: str` + `ScheduleRegistry._coerce_job`），
而非放宽断言；两个架构测试逐字未动，复验 `2 kept, 0 broken`。
