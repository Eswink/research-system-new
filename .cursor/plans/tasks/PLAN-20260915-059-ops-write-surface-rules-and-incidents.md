---
id: PLAN-20260915-059
slug: ops-write-surface-rules-and-incidents
title: ops 写面（G7）：告警静音规则 CRUD + 事故 declare/assign/close
status: DONE
created_at: 2026-09-15
updated_at: 2026-09-16
parent_goal: GOAL-20260915-002
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-002 cycle 5 = EC-04（G7 ops 写面）。授权来源同 GOAL-20260915-002：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；push-to-main-for-CI 授权沿用 GOAL-001 批准口径。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-059-ops-write-surface-rules-and-incidents.md
memory_entries:
  - MEM-20260915-035-write-surface-must-be-consumed-by-read-surface
---

# PLAN-20260915-059 — ops 写面：告警规则 CRUD + 事故处置（GOAL-002 cycle 5 / EC-04）

## 目标

把 `ops/alerts` 与 `ops/incidents` 两页的诚实缺口（"规则 CRUD 无 API""无 declare/assign/close
处置工作流"）变成真实能力，并且**写面必须被读面消费**：

- `POST/PATCH/DELETE /projects/{id}/ops/alert-rules`、`/ops/alert-rules/{rule_id}` 写入的规则，
  必须让 `GET /projects/{id}/ops/alerts` 给命中的告警打 `muted=true` + `muted_by=<rule id>`
  标记（**只标记，不隐藏**）；
- `POST /projects/{id}/ops/incidents`、`/ops/incidents/{id}/assign`、`/ops/incidents/{id}/close`
  写入的事故，必须让同一读面给来源 run 的告警带上 `incident_id`，并让
  `GET /projects/{id}/ops/incidents` 区分"已登记事故"与"失败 Run 候选"。

## 背景（已核实的事实，决定了本计划的形状）

- `packages/domain/ops_view.py` 的模块注释明确写着"这些页面若引入'用户注册的告警规则'等持久实体，
  在进程内 scheduler 并不读取它们之前，就是一个**不被消费的假真相**"——本计划的第一步就是让
  "被消费"成为事实，而不是先建表再解释。
- 读面（`services/api/routers/ops_view.py`）当前完全由真实状态派生：失败 run ∪ 非健康端点 ∪
  离线/排水 worker；`incidents` 路由返回的是 FAILED run **候选**（`IncidentCandidateDto` 字段名
  是 run_id/protocol_id/state，不是事故字段）。
- 控制面配置面 store 已有一整套同侧 SQLite 实现（`_sqlite_config_stores` /
  `_pg_config_stores`），本计划沿用该模式新增 `ops_store`，不新建第二套装配路径。
- 既有先例：写面不可用时**如实 503 + 原因**（artifact store 未配置、workspace snapshot root 未配置同口径）。

## 口径（诚实边界，先写清楚再写代码）

1. **静音不是隐藏**：命中规则的告警仍出现在列表里，只是带 `muted` / `muted_by` 标记并给出
   `muted_count`；规则不可用时读面 `rules_available=false` + 原因，不伪装成"没有规则"。
2. **候选项不是事故**：失败 Run 不会自动登记为事故；`incidents`（已登记）与 `candidates`（派生）
   是两个字段、两张表、两套语义。已登记（含已关闭）的来源 run 不再出现在候选里，
   但仍留在已登记列表中可追溯。
3. **关闭是终态**：`IncidentStatus` 状态机（OPEN → ASSIGNED → CLOSED，可重复指派，OPEN 可直接关闭）
   决定 `assign`/`close` 的合法性；已关闭再处置 → 409，**不是静默 no-op**。
4. **未知枚举值 422**：`kind`（RUN_FAILED/ENDPOINT_DEGRADED/WORKER_OFFLINE）、`severity`
   （CRITICAL/WARNING/INFO）非法即 422；PATCH 空补丁（一个字段都没改）也 422。
5. **未配置 store → 503**：不伪造成功、不用内存字典冒充持久面。
6. **写面必须可被读面观察**：每条写路径都要有一个"写完再读"的用例（不是只断言 201/204）。

## 范围

- Domain：`packages/domain/ops_control.py`（`AlertRule`、`Incident` + `IncidentStatus` 状态机）。
- Port：`packages/application/ports/ops_store.py`（`OpsStore`：规则/事故的 list/get/save/delete）。
- 适配器：`adapters/sqlite/ops_store.py`（`ops_alert_rules` / `ops_incidents` 两表 + 项目索引）。
- API：`services/api/dto/ops_view.py`（读面 DTO 扩展 + 写面 DTO）、
  `services/api/ops_control_support.py`（读写共享的呈现口径）、
  `services/api/routers/ops_control.py`（7 条写/读规则端点）、
  `services/api/routers/ops_view.py`（读面消费规则与事故）、
  `services/api/composition.py` / `pg_composition.py`（`ops_store` 装配）、`services/api/app.py`（注册）。
- 前端：`apps/web/src/api/opsControlClient.ts`（写面客户端）、`features/ops-view/OpsAlertRulesPanel.tsx`、
  `features/ops-view/IncidentActions.tsx`、`features/ops-view/OpsFields.tsx`、
  `features/ops-view/useOpsAction.ts`、`features/ops-view/OpsActions.module.css`、
  `features/ops-view/opsViewColumns.tsx`（规则/事故/候选三套列）、
  `features/alerts/AlertsPage.tsx`、`features/incidents/IncidentsPage.tsx`、
  `api/{client,types}.ts`、`navigation/pageSupport.ts`。
- 测试：`tests/api/test_ops_control_api.py`（10 用例）、`tests/api/test_ops_view_api.py`（读面口径改写）、
  `tests/api/run_fixtures.py` + `tests/api/conftest.py`（装配 ops store，live 与生产 SQLite 同侧）、
  `tests/contracts/test_openapi_snapshot.py`（路径 + 写方法断言）、
  stub e2e `apps/web/tests/e2e/ops-write.spec.ts` + `stub-routes-ops.ts`、
  live e2e `apps/web/tests/e2e/live-ops-write.spec.ts`（+ `live-specs.ts` 登记）。
- 文档/基线：`docs/api/openapi.m13.json` 重生成、`ops-alerts` / `ops-incidents` 路由的
  win32 + linux 设计基线、`docs/frontend/CONSOLE_PAGE_MAP.md`。

## 验收条件

- [x] AC-01：域状态机正确——`Incident.assigned_to()` / `close()` 的合法迁移与非法迁移
      （`InvalidTransitionError`）都有用例；`open` 语义对"从持久面解出的普通 str"也成立
      （用 `!=` 而非 `is not`）。
- [x] AC-02：API 写面——规则 CRUD 与事故 declare/assign/close 全链；
      未知枚举 422、空补丁 422、未知 id 404、已关闭 409、store 缺失 503。
      `tests/api/test_ops_control_api.py` 10 passed。
- [x] AC-03：**写面被读面消费**——规则命中只加标记不隐藏（数量守恒）、
      登记事故后来源 run 的告警带 `incident_id`、关闭后该标记消失、候选列表扣掉已登记项。
      `tests/api/test_ops_view_api.py` + 控制面用例合计 15 passed。
- [x] AC-04：OpenAPI 快照含 5 条新路径（3 条带写方法）且写方法断言单独成用例；
      契约套件全绿。
- [x] AC-05：前端 `ops/alerts` 渲染告警（含 muted/incident 标记）与规则写面（新建/启停/删除），
      `ops/incidents` 渲染已登记事故的处置（指派/关闭）与候选的一键登记；
      `pageSupport` 的 `GAPS.alerts` / `GAPS.incidents` 收敛、两条 `disabledOperations` 清空。
- [x] AC-06：stub e2e 5 用例 + live e2e 3 用例（真实 HTTP 写链）绿；
      全量 stub 套件 50 passed、live 套件 28 passed。
- [x] AC-07：`ops-alerts` / `ops-incidents` 设计基线 win32 + linux 重生成并目检；
      并量化门禁漂移（见下"已知风险"与 RECHECK-059 W-1）。
- [x] AC-08：本地 m0 = `profile=m0; 23 deterministic checks`。本地门禁共跑了 **4 次**才全绿
      （逐条如实记录，未掩盖）：① `python/format-check`（手工改过的测试文件未跑 `ruff format`）
      → ② `python/tests` 的 50 行/函数上限（`tests/contracts/test_openapi_snapshot.py` 加断言后
      52 行，拆出 `test_openapi_contains_projects_and_governance_paths` 并新增 ops 写方法用例）
      → ③ `typescript/boundaries`（`OpsAlertRulesPanel` ↔ `opsViewColumns` 循环依赖：把
      `EnabledChip` 提到独立模块）→ ④ 命名门禁（独立模块文件名必须与唯一组件导出同名，
      `OpsChips.tsx` → `EnabledChip.tsx`）→ 绿。

## 实施清单

- [x] WP-A Domain + Port + SQLite 适配器
- [x] WP-B 读面口径改造（alerts 消费规则与事故；incidents 拆分已登记/候选）+ 读面相应用例改写
- [x] WP-C 写面路由 + DTO + 装配（composition/pg_composition/app） + API 用例 + OpenAPI 快照
- [x] WP-D 前端面板与页面接线 + pageSupport 收敛 + stub/live e2e + live-specs 登记
- [x] WP-E 文档、设计基线（含门禁漂移量化）、RECHECK-059、GOAL/ALL_PLAN/记忆记账、m0、CI

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A | `pytest tests/api/test_ops_control_api.py -q` → **10 passed**（含 503 锁定、CRUD 生命周期、422/404/409） | PASS |
| WP-B | `pytest tests/api/test_ops_view_api.py tests/api/test_ops_control_api.py -q` → **15 passed**（静音不隐藏、事故回链、候选扣减） | PASS |
| WP-B | `pytest tests/api -q` → **336 passed**（run-ready 装配新增 ops store 后全量 API 无回归） | PASS |
| WP-C | `tools/gen_openapi.py` 重生成（+763 行）；`pytest tests/contracts -q` → **3 passed**（路径 + 写方法断言） | PASS |
| WP-D | stub e2e：`ops-write.spec.ts` 5 用例；全量 stub 套件 **50 passed** | PASS |
| WP-D | live e2e：`live-ops-write.spec.ts` 3 用例（真实 HTTP 写链：规则 CRUD → 读面 muted；事故 declare/assign/close → 409）；全量 live 套件 **28 passed** | PASS |
| WP-D | 根 `npx eslint .` = 0 error；web `tsc --noEmit` 通过；web 单测 **76 passed** | PASS |
| WP-E | 基线：`ops-alerts` / `ops-incidents` win32（本地）+ linux（pinned noble）重生成并目检；门禁漂移量化脚本 `scratch/cycle5-baseline-drift/measure.py` | PASS |
| WP-E | 本地 m0 共 **4 次**：① `python/format-check`（测试文件未格式化）→ ② `python/tests`（契约用例所属函数 52 行 > 50 上限）→ ③ `typescript/boundaries`（新面板与列定义循环依赖）→ ④ 命名门禁（独立模块名须与唯一组件导出同名）；逐条修复后 = `profile=m0; 23 deterministic checks`；RECHECK-059 = PASS_WITH_WARNINGS | PASS（先失败后修复） |

## 已知风险

- **设计门禁的容差盲区（本轮实测）**：ops 两页新增整块面板后，与旧基线按 Playwright 判据
  （pixelmatch，YIQ 阈值 0.2）只差 **1.02% / 0.93%**，低于 `maxDiffPixelRatio: 0.02` ⇒
  门禁**不会报警**（与 cycle 3 记录的 1.73% 同类）。因此"页面改动必须主动重生成基线并目检"，
  不能依赖门禁变红来发现问题；量化脚本留在 `scratch/cycle5-baseline-drift/`。
  注：早期用"任一通道像素差 ≠ 0"统计得到的 ~40% 是**误导性指标**（抗锯齿/背景微差占绝大多数），
  已在脚本注释里写清。
- 规则只做静音标记，不改变告警的派生来源（失败 run 仍会被列出）；若要真正抑制来源，
  需要阈值/去噪策略，本计划不做（登记为 RECHECK-059 W-2）。
- 事故没有 SLA/计时/升级链，`assignee` 只是自由文本（无成员校验）——登记为 W-3。
- **Windows 上的 live 装配变化**：`run_fixtures._run_ready_sqlite_stores` 增加 `ops_store` 后，
  所有走 run-ready 装配的用例（含 live harness）都具备写面；若将来某用例需要"未配置"语义，
  必须显式把它设为 `None`（`test_ops_control_api.py` 已有先例）。

## 状态历史

- 2026-09-15 创建（IN_PROGRESS）：GOAL-20260915-002 cycle 5，取 EC-04（G7）。
- 2026-09-15 WP-A/WP-B/WP-C 完成：域 + Port + SQLite store；读面消费规则与事故；
  写面 7 端点；API 15 passed（含读面口径改写），OpenAPI 快照 +763 行，契约 3 passed。
- 2026-09-15 WP-D 完成：前端规则面板 + 事故处置 + 候选登记；stub 5 用例、live 3 用例绿；
  全量 stub 50 / live 28。
- 2026-09-15 WP-E 首跑：m0 连续被**四道**门禁拦下（格式 / 50 行函数 / 循环依赖 / 命名），
  逐条修复后才 23/23——全部如实记录，未跳过任何一道；其间定位并量化了设计门禁对
  "整块新增面板"的容差盲区（1.02% / 0.93%）。
- 2026-09-16 收口：RECHECK-059 = PASS_WITH_WARNINGS（W-1 门禁容差、W-2 规则只做标记、
  W-3 assignee 无成员校验、W-4 DTO 形状变更、W-5 m0 四连红的教训）。

## 影响报告

- 改动：新增 `packages/domain/ops_control.py`、`packages/application/ports/ops_store.py`、
  `adapters/sqlite/ops_store.py`、`services/api/ops_control_support.py`、
  `services/api/routers/ops_control.py`、`apps/web/src/api/opsControlClient.ts`、
  `apps/web/src/features/ops-view/{OpsAlertRulesPanel.tsx,IncidentActions.tsx,OpsFields.tsx,
  useOpsAction.ts,OpsActions.module.css}`、`apps/web/tests/e2e/{ops-write.spec.ts,
  live-ops-write.spec.ts,stub-routes-ops.ts}`、`tests/api/test_ops_control_api.py`；
  修改 `services/api/dto/ops_view.py`、`services/api/routers/ops_view.py`、
  `services/api/{composition,pg_composition,app}.py`、`tests/api/{conftest,run_fixtures}.py`、
  `tests/api/test_ops_view_api.py`、`tests/contracts/test_openapi_snapshot.py`、
  前端 `api/{client,types}.ts`、`features/alerts/AlertsPage.tsx`、
  `features/incidents/IncidentsPage.tsx`、`features/ops-view/opsViewColumns.tsx`、
  `navigation/pageSupport.ts`、`tests/e2e/{stub-routes.ts,live-specs.ts,live-api-workflow.spec.ts}`、
  `docs/api/openapi.m13.json`、`ops-alerts` / `ops-incidents` 基线 ×2 平台。
- lint/typecheck/test：Python m0 全量 = `profile=m0; 23 deterministic checks`（本地共跑 4 次：
  格式 → 50 行函数 → 循环依赖 → 命名门禁逐条拦下并修复，全部如实记录）；
  API 336 passed；契约 3 passed；前端 eslint 0 error、`tsc --noEmit` 通过、
  单测 76 passed、stub e2e 50 passed、live e2e 28 passed；depcruise 0 violation。
- Domain/API/schema 变化：**新增 7 条端点**（`GET/POST /projects/{id}/ops/alert-rules`、
  `PATCH/DELETE /ops/alert-rules/{rule_id}`、`POST /projects/{id}/ops/incidents`、
  `POST /ops/incidents/{id}/assign`、`POST /ops/incidents/{id}/close`）；读面 DTO 扩展
  （`AlertItemDto` 增 `muted`/`muted_by`/`incident_id`，`AlertsViewDto` 增
  `rules_applied`/`muted_count`，`IncidentsViewDto` 增 `candidates`，`IncidentItemDto` 改为
  真实事故字段）。新增两张 SQLite 表（`ops_alert_rules` / `ops_incidents`，`create` 幂等建表，
  无破坏性迁移）。
- 安全/凭据变化：无新凭据面；写面沿用既有 `Idempotency-Key` 中间件（mutating 方法缺 key → 422）
  与 policy/preflight 门链；无宿主调用、无外发动作。
- 兼容性/迁移风险：`IncidentsViewDto.incidents` 的**元素形状变更**（由候选行改为事故行）——
  旧前端会渲染出空字段；本仓前后端同版本发布，契约由 OpenAPI 快照固定；外部消费者需按新 schema 升级。
  其它读面字段为纯增量。
- 上游版本影响：无。
- 下一项任务：GOAL-20260915-002 cycle 6 = EC-05（G15 tool-provider 管理写面：注册/更新/健康复核），
  子 PLAN 编号 = PLAN-20260915-060。
