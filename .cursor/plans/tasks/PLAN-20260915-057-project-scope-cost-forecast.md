---
id: PLAN-20260915-057
slug: project-scope-cost-forecast
title: 项目级成本预测（G12）：只对已计价的天取日均外推，排除项随响应返回
status: DONE
created_at: 2026-09-15
updated_at: 2026-09-15
parent_goal: GOAL-20260915-002
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-002 cycle 3 = EC-02（G12 跨 run 时序成本预测）。授权来源同 GOAL-20260915-002：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；push-to-main-for-CI 授权沿用 GOAL-001 批准口径。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-057-project-scope-cost-forecast.md
memory_entries:
  - MEM-20260915-033-series-projection-valued-days-only
---

# PLAN-20260915-057 — 项目级成本预测（GOAL-002 cycle 3 / EC-02）

## 目标

把 `insights/cost-analytics` / `govern/budget` 的 G12 缺口（"跨 run 时间序列预测无 API"）
变成真实能力：`GET /projects/{project_id}/cost-forecast` 在**项目 runs** 的已记录用量上
给出日序列 + **已计价日均外推**，并把口径（方法、视野、样本天数）、排除项（逐日原因）、
归属（无法归属的条目计数）全部随响应返回——不插值、UNKNOWN 不当 0、跨币种不给金额。

## 背景（要解决的是"诚实外推"，不是"画曲线"）

仓库已有的两条成本读面都不做外推：`GET /cost/daily` 明说"绝不预测"，run 级
`GET /runs/{id}/cost-forecast` 的口径是 `RESERVED_ONLY`（只做预留-消耗，不外推未预留开销）。
于是前端只能写"跨 run 时间序列预测不绘制"。本计划补的是**控制面自己给出可复核的外推**：

- 外推只用**已计价**的天：`ACTUAL`/`ESTIMATED`/`ZERO` 且金额非空；
- `USAGE_UNKNOWN` / `MONETARY_UNAVAILABLE` / `NO_DATA` / `CURRENCY_CONFLICT` /
  `PARTIALLY_METERED` 与**混合定价**的天一律排除，并逐日给出 `exclusion_reason`；
- 样本跨币种 → 不给金额（`CURRENCY_CONFLICT`），不做隐式换算；
- 方法/样本量/注记随结果返回（`MEAN_OF_VALUED_DAYS`；"extrapolation, not a commitment"）。

## 范围

- 领域/应用（纯函数）：`packages/application/cost/series_projection.py`。
- API：`services/api/mappers/project_cost_forecast.py`（项目归属 + 日序列 + 外推装配）、
  `services/api/routers/project_cost_forecast.py`、`services/api/dto/operations.py`
  （`ProjectCostDayDto`/`ProjectCostProjectionDto`/`ProjectCostForecastDto`）、
  `services/api/app.py` 注册；`services/api/mappers/cost_daily.py` 的
  `_parse_day`/`_note` 提升为公开 `parse_day`/`note_for_unattributed` 供复用。
- 前端：`apps/web/src/features/cost-analysis/ProjectCostForecastPanel.tsx`（两个页面共用）、
  `CostAnalyticsPage.tsx` 与 `BudgetPage.tsx` 接线、`apps/web/src/api/{types,operationsClient,client}.ts`、
  `apps/web/src/navigation/pageSupport.ts`（GAPS.costSeries / budgetForecast 收敛）。
- 测试：`tests/application/test_cost_series_projection.py`（7 用例）、
  `tests/api/test_project_cost_forecast_api.py`（7 用例）、
  `tests/contracts/test_openapi_snapshot.py`（新增路径断言）、stub e2e
  `apps/web/tests/e2e/project-cost-forecast.spec.ts`、live e2e
  `apps/web/tests/e2e/live-project-cost-forecast.spec.ts`；
  新增 `apps/web/tests/e2e/live-specs.ts`（live 清单单一来源，替代两份配置里各写一遍正则）。
- 文档/基线：`docs/api/openapi.m13.json`（重生成）、`docs/frontend/CONSOLE_PAGE_MAP.md`、
  `insights-cost-analytics` 与 `govern-budget` 两条路由的 win32 + linux 设计基线。

## 验收条件

- [x] AC-01：纯函数口径正确——只对已计价的天外推；排除项逐日给原因；UNKNOWN/ZERO 语义
      （0 是"显式零"进样本，UNKNOWN 绝不进）；跨币种不给金额；`observed_status` 只在
      全为实测时才是 ACTUAL。`tests/application/test_cost_series_projection.py` 7 passed。
- [x] AC-02：端点交付——项目归属（其它项目的已知 run 明确排除、归属不明的条目只计数）、
      窗口/视野参数（`date_from`/`date_to` 非法 422、`horizon_days` ∈ [1,90]）、
      未知项目返回空序列 + `NO_VALUED_DAYS`（与 `/projects/{id}/runs` 同口径，不 404）、
      无 ledger 503。`tests/api/test_project_cost_forecast_api.py` 7 passed。
- [x] AC-03：OpenAPI 快照含 `/projects/{project_id}/cost-forecast`（快照重生成 + 契约断言）。
- [x] AC-04：前端两页（成本分析 / 预算）渲染口径、样本/排除计数、外推额与逐日原因；
      `pageSupport` 两条 reason 收敛；stub e2e 与 live e2e 各 1 用例绿。
- [x] AC-05：设计基线（两条路由 × win32/linux）重生成并目检。
- [x] AC-06：本地 m0 = `profile=m0; 23 deterministic checks`。

## 实施清单

- [x] WP-A 领域纯函数 + 单测
- [x] WP-B 端点/DTO/装配 + API 用例 + OpenAPI 快照
- [x] WP-C 前端面板与两页接线 + 交互/直播用例 + live 清单单一来源
- [x] WP-D 设计基线与文档
- [x] WP-E 本地 m0 + RECHECK-057 + GOAL-002/ALL_PLAN/记忆记账 + CI
- [x] WP-F 门禁修复（m0 首跑红）：`liveSpecs.ts` → `live-specs.ts`（测试/夹具须 kebab-case）；
      `tests/architecture/module_file_naming.py` 忽略 gitignored 的 Playwright 生成目录
      `test-results`（目录名取自中文用例标题），并补回归用例

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A | `pytest tests/application/test_cost_series_projection.py -q` → **7 passed**（含"排除项逐日原因""跨币种不给金额""ZERO 是显式零""ESTIMATED 不冒充 ACTUAL""金额缺失的已计价天也不进样本"） | PASS |
| WP-B | `pytest tests/api/test_project_cost_forecast_api.py -q` → **7 passed**（外推值 1000×7/3×7、排除 UNKNOWN、项目隔离 + unattributed 计数、幽灵项目空序列、参数 422、truncated 透传） | PASS |
| WP-B | `tools/gen_openapi.py` 重生成快照（+305 行）；`pytest tests/contracts -q` → **355 passed, 56 skipped** | PASS |
| WP-C | stub e2e：`project-cost-forecast.spec.ts` 通过（口径行/金额行/日表"进样本=是/排除=USAGE_UNKNOWN"）；全量 stub 套件 **41 passed** | PASS |
| WP-C | live e2e：`live-project-cost-forecast.spec.ts` 通过（真实装配面：method/horizon/note/scope_note、`valued+excluded == days.length`、horizon 越界 422、幽灵项目 NO_VALUED_DAYS）；全量 live 套件 **21 passed** | PASS |
| WP-C | 根 `pnpm exec eslint .` = 0 error；`--filter web lint/typecheck` 通过；web 单测 76 passed | PASS |
| WP-D | 基线：`insights-cost-analytics` / `govern-budget` 的 win32（本地）与 linux（pinned noble 容器，脚本支持多路由）重生成，两张 linux 基线目检含新面板且列未被裁 | PASS |
| WP-E | 本地 m0 首跑 **FAIL**（`python/tests=1`：生成目录 + 新文件命名），修复后复跑 = `profile=m0; 23 deterministic checks`；RECHECK-057 = PASS_WITH_WARNINGS | PASS |

## 已知风险

- 外推是**线性日均**（`MEAN_OF_VALUED_DAYS`）：不含趋势/季节性/置信区间；样本 < 2 天时
  日均即单日值，噪声会被放大——注记里已说明"按近期节奏外推"，但读者仍需自行判断。
- 项目归属按 `run_id` / `task→run` 解析：归属不明的条目只计数（不猜项目）；若某项目
  大量条目无法归属，序列会偏小——`unattributed_entries` + `attribution_note` 已随响应返回。
- 日序列窗口无默认值（全量 400 天上限）：调用方要自己传 `date_from/date_to` 才能收窄
  窗口，否则样本来自全部历史——对"最近节奏"的假设而言这是个口径弱点，登记为 W。
- 页面两处共用同一面板：预算页的 run 级指标与项目级外推并列，读者需注意两者口径不同
  （run 级 = 预留-消耗；项目级 = 时序外推）。

## 状态历史

- 2026-09-15 创建（IN_PROGRESS）：GOAL-20260915-002 cycle 3，取 EC-02（G12）。
- 2026-09-15 WP-A/WP-B 完成：纯函数 + 端点 + 7+7 用例绿；OpenAPI 快照重生成。
- 2026-09-15 WP-C 完成：面板接入成本分析与预算两页；stub 41 passed、live 21 passed；
  live 清单改为单一来源（`tests/e2e/live-specs.ts`）。
- 2026-09-15 WP-D 完成：两条路由设计基线重生成并目检。
- 2026-09-15 WP-E 首跑红（WP-F）：m0 的命名门禁拦下 `liveSpecs.ts`（测试文件须 kebab-case）
  与 Playwright 生成目录 `test-results/<中文用例标题>/`；改名 + 忽略 gitignored 生成目录 +
  回归用例后复跑 m0 = 23/23。RECHECK-057 = PASS_WITH_WARNINGS。

## 影响报告

- 改动：新增 `packages/application/cost/series_projection.py`、
  `services/api/mappers/project_cost_forecast.py`、`services/api/routers/project_cost_forecast.py`、
  `apps/web/src/features/cost-analysis/ProjectCostForecastPanel.tsx`、
  `apps/web/tests/e2e/live-specs.ts`、两组测试；修改
  `services/api/dto/operations.py`、`services/api/mappers/cost_daily.py`（两个私有函数改为公开）、
  `services/api/app.py`（注册路由）、前端 cost-analytics/budget 两页与 api/navigation 接线、
  `playwright{,.Live}.config.ts`（live 清单单一来源）、`docs/api/openapi.m13.json`、
  `docs/frontend/CONSOLE_PAGE_MAP.md`、两条路由的设计基线 PNG ×2 平台；
  门禁侧修改 `tests/architecture/module_file_naming.py` + `test_module_file_naming.py`
  （忽略 gitignored 的 Playwright 生成目录 + 回归用例）。
- lint/typecheck/test：Python m0 全量 23/23（首跑红于命名门禁，修复后复跑通过；
  含 mypy 818 文件、ruff、源码上限）；新增单测 7 + API 7；契约 355 passed；
  前端 lint/typecheck 通过、单测 76 passed、stub e2e 41 passed、live e2e 21 passed。
- Domain/API/schema 变化：**新增只读端点** `GET /projects/{project_id}/cost-forecast`
  （`ProjectCostForecastDto`）。无数据库迁移；`/cost/daily` 与 run 级 cost-forecast
  的响应形状未变（仅内部辅助函数由私有改公开）。
- 安全/凭据变化：无（只读投影 + 纯函数外推；无新凭据面、无外部调用）。
- 兼容性/迁移风险：无破坏性变更；`/cost/daily` 的 `attribution_note` 文案函数改名
  （`_note` → `note_for_unattributed`）属内部符号，响应不变。
- 上游版本影响：无。
- 下一项任务：GOAL-20260915-002 cycle 4 = EC-03（G8 workspace 文件树 + 文件级快照 Diff，
  或产出 Accepted ADR 收敛标注）。
