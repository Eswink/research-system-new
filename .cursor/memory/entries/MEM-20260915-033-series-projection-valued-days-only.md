---
id: MEM-20260915-033
title: 成本时序外推只对"已计价的天"取日均；排除项与原因随响应返回
status: ACTIVE
created_at: 2026-09-15
updated_at: 2026-09-15
scope: repository
confidence: 0.90
review_after: 2027-09-15
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-057-project-scope-cost-forecast.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-057-project-scope-cost-forecast.md
supersedes: []
tags:
  - cost
  - forecast
  - honesty-boundary
  - console
---

# 成本时序外推的样本口径

## 做了什么

`packages/application/cost/series_projection.py`（纯函数）+ `GET /projects/{id}/cost-forecast`：
把项目 runs 的已记录用量按 UTC 日投影成序列后，**只对已计价的天**（`ACTUAL`/`ESTIMATED`/`ZERO`
且 `minor_units` 非空）取日均，外推 = 日均 × `horizon_days`（1~90）。每个未进样本的天都带
`exclusion_reason`（`USAGE_UNKNOWN`/`MONETARY_UNAVAILABLE`/`NO_DATA`/`CURRENCY_CONFLICT`/
`PARTIALLY_METERED`/`MIXED_PRICING`），样本跨币种时 `projected_minor=null` +
`unavailable_reason=CURRENCY_CONFLICT`。

## 为什么这样做

- 仓库既有的两条成本读面都不外推：`/cost/daily` 明说"绝不预测"，run 级
  `/runs/{id}/cost-forecast` 是 `RESERVED_ONLY`（只算预留减消耗）。前端因此只能写
  "跨 run 时间序列预测不绘制"。
- 外推一旦把"没有计价依据的天"当成 0 或做插值，就会**系统性低估**（很常见：中转站没上报
  金额的天、跨定价表的天）。把口径写成"已计价日均"并逐日给原因，读者才能复核这笔外推是
  从哪些天算出来的。
- 跨币种不求和是本仓既有铁律（`CostAmount` 的 `CURRENCY_CONFLICT`）：外推同样不例外。

## 怎么做与复现

```
python -m pytest tests/application/test_cost_series_projection.py -q   # 7 passed
python -m pytest tests/api/test_project_cost_forecast_api.py -q        # 7 passed
cd apps/web && pnpm run test:e2e && pnpm run test:e2e:live            # 41 / 21 passed
```

判据要点：`valued_days + excluded_days == days.length`；UNKNOWN 天绝不进样本（0 是"显式零"，
进样本）；`observed_status` 只在全为实测时才是 `ACTUAL`；`horizon_days` 越界 422；
未知项目 200 + 空序列（`NO_VALUED_DAYS`）而不是 404。

## 适用边界

- 方法是**日均**，不含趋势/季节性/置信区间；样本少时噪声会被放大（注记里写明
  "extrapolation, not a commitment"）。
- 归属按 `run_id` / `task→run` 解析；归属不明的条目只计数（`unattributed_entries`）不猜项目，
  所以序列可能偏小。
- 窗口无默认值（全量最多 400 天）：要收窄"最近节奏"必须显式传 `date_from/date_to`。
- 想让预测更准，先让计量更全（中转站上报金额、定价表覆盖模型），而不是改进外推公式。

## 来源

- PLAN-20260915-057 / RECHECK-20260915-057（GOAL-20260915-002 cycle 3 / EC-02）。
- 相关：[[MEM-20260914-023]]（BudgetLedger 预留归属）、[[MEM-20260915-032]]（同一"没有记录面
  就如实说"的思路用在血缘上）。
