---
id: RECHECK-20260915-057
plan_id: PLAN-20260915-057
attempt: 2
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-15
completed_at: 2026-09-15
reviewer: root-agent-goal-002-cycle3
baseline_ref: 29af240
checked_head: 29af240+worktree
---

# RECHECK-20260915-057 — 项目级成本预测（GOAL-002 cycle 3 / EC-02）

## 检查范围

PLAN-20260915-057 声称的交付面：项目级成本预测的纯函数口径、端点与归属规则、前端两页接线
与标注收敛、两条路由的设计基线，以及"不插值/不猜/不隐式换币"的诚实性；外加本次顺带修掉的
两处工程债（live 用例清单单一来源、命名门禁对生成产物的处置）。其它 EC 不在范围内。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 只对已计价的天外推 | `tests/application/test_cost_series_projection.py`：`USAGE_UNKNOWN`/`MONETARY_UNAVAILABLE`/`PARTIALLY_METERED`/`MIXED_PRICING` 天全部落在 `excluded_days` 且带原因；`ZERO` 天进样本（显式零≠缺失） | PASS |
| 不做插值、缺失不当 0 | 未来窗口用例：`days == []` 且 `projected_minor is None`（不填充、不外推空窗口）；排除的天不出现在金额里 | PASS |
| 跨币种不求和 | 纯函数用例：两币种样本 ⇒ `observed_minor/projected_minor` 均为 `None`，`observed_status=CURRENCY_CONFLICT` | PASS |
| 状态不撒谎 | 全 ACTUAL ⇒ `ACTUAL`；混入 ESTIMATED ⇒ `ESTIMATED`；无样本 ⇒ `NO_DATA`（纯函数用例各一条） | PASS |
| 项目归属正确 | API 用例：本项目 run 的条目进序列；**其它项目**的已知 run 明确排除（且不计入 unattributed）；归属不明的 run 计入 `unattributed_entries` 并带 `attribution_note` | PASS |
| 端点边界 | `horizon_days` 0/91 → 422；`date_from=2026/09/01` → 422；无 ledger → 503；幽灵项目 → 200 + 空序列 + `NO_VALUED_DAYS`（不 404，与 `/projects/{id}/runs` 同口径） | PASS |
| OpenAPI 快照一致 | `tools/gen_openapi.py` 重生成；契约套件 **355 passed / 56 skipped**；新增 `/projects/{project_id}/cost-forecast` 断言 | PASS |
| 页面真的渲染这些事实 | stub e2e：口径行（`MEAN_OF_VALUED_DAYS`/视野 7 天/样本 1/排除 1）、金额行（1200 → 8400）、日表里 `2026-09-13` 进样本、`2026-09-14` 显示 `USAGE_UNKNOWN` 且金额为 `—` | PASS |
| 真实装配面同性质 | live e2e：method/horizon/note/`scope_note`、`valued+excluded == days.length`、越界 422、幽灵项目 `NO_VALUED_DAYS` | PASS |
| 标注收敛 | `pageSupport`：`GAPS.costSeries` 改为项目级预测口径 + 边界；`GAPS.budgetForecast` 指向项目级端点 | PASS |
| 设计基线 | `insights-cost-analytics` 与 `govern-budget` 的 win32（本地）+ linux（pinned noble）重生成；两张 linux 基线目检：新面板在场、4 列未被裁、排除原因可见 | PASS |
| 工程债：live 清单单一来源 | 新增 `apps/web/tests/e2e/live-specs.ts` 导出 `LIVE_SPEC_PATTERN`，两份 playwright 配置改为引用它；`--list` 复核：stub **41 tests / 11 files**、live **21 tests / 5 files**（清单未漂移） | PASS |
| 前端门禁 | 根 eslint 0 error；web lint/typecheck 通过；单测 76 passed；stub e2e **41 passed**；live e2e **21 passed** | PASS |
| Python 门禁 | **首次 m0 失败**（`python/tests=1`：命名门禁把 Playwright 生成目录 `apps/web/test-results/design-fidelity-33-路由主截图（dark-normal-zh）/` 判为非法路径；另 `apps/web/tests/e2e/liveSpecs.ts` 违反"测试/夹具文件名 kebab-case"）→ 修复（改名 `live-specs.ts`；把 gitignored 的 `test-results` 加入 `IGNORED_DIRECTORIES` 并补一条回归用例）→ 复跑 m0 = `profile=m0; 23 deterministic checks` | PASS（先失败后修复） |

## 结论

result: **PASS_WITH_WARNINGS**

交付面成立且可复核：外推只吃"已计价的天"，每个被排除的天都能在响应里看到原因，样本跨币种
时宁可不给金额；页面把方法、样本量、外推额与逐日原因原样呈现。

复核-修复循环里三道门都真的起了作用，且各不相同：命名门禁拦下两个真实问题（新文件命名违规 +
生成目录被误判），`ruff` 拦下回归用例里的 101 字符行。第一次 m0 因此是红的，本记录不掩盖该
失败——修复后再跑才得到 23/23。

## 告警

- W-1（方法边界）：`MEAN_OF_VALUED_DAYS` 是日均外推，不含趋势/季节性/置信区间；样本为 1 天时
  外推就是"这一天 × 视野"，噪声被放大。页面上有注记（`note`），但没有统计意义上的不确定性表达。
- W-2（窗口默认）：端点不提供默认窗口（未传 `date_from/date_to` 时样本来自全部历史，最多 400 天），
  "最近节奏"的假设因此在默认调用下不严格成立；调用方需要显式收窄。
- W-3（归属偏小）：无法归属到项目 runs 的条目只计数不猜测，序列可能偏小；`unattributed_entries`
  与 `attribution_note` 已随响应返回，但没有按项目归因的补救机制。
- W-4（两页共用面板的口径差）：预算页同时展示 run 级 `RESERVED_ONLY` 预测与项目级时序外推，
  两者口径不同（前者不外推），页面靠各自的 `scope_note` 区分，没有统一的"这是什么口径"总说明。
- W-5（生成产物与命名门禁）：本次只把 Playwright 的 `test-results` 加入忽略名单。任何**未 gitignore**
  的生成目录只要落在 `apps|services|packages|adapters|tests` 之下，仍会被同一门禁判违规——
  正解是让生成物进 `.gitignore`，而不是继续加忽略项。
- W-6（继承，未处理）：RECHECK-054 W-1（worker SIGTERM 打不断阻塞中的 HTTP 读）仍开放。

## 复现

```
# 纯函数 + 端点 + 契约
python -m pytest tests/application/test_cost_series_projection.py -q     # 7 passed
python -m pytest tests/api/test_project_cost_forecast_api.py -q          # 7 passed
python -B tools/gen_openapi.py && python -m pytest tests/contracts -q    # 355 passed
# 命名门禁（本次修复点）
python -m pytest tests/architecture/test_module_file_naming.py -q        # 30 passed
# 前端（stub 替身链路 / 真实 API 链路）
cd apps/web && pnpm exec playwright test --list                          # 41 tests in 11 files
cd apps/web && pnpm exec playwright test --list --config playwrightLive.config.ts   # 21 tests in 5 files
cd apps/web && pnpm run test:e2e && pnpm run test:e2e:live               # 41 / 21 passed
# 设计基线（两条路由；linux 在 pinned noble 容器内重生成）
rm apps/web/tests/e2e/design-fidelity.spec.ts-snapshots/{insights-cost-analytics,govern-budget}-*-win32.png
cd apps/web && pnpm exec playwright test design-fidelity --update-snapshots
bash scratch/gen_linux_baseline_route.sh insights-cost-analytics govern-budget
# 本地门
sh scratch/run-m0-cycle12.sh                                             # profile=m0; 23 deterministic checks
```
