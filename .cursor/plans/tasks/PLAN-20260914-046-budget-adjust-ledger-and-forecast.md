---
id: PLAN-20260914-046
slug: budget-adjust-ledger-and-forecast
title: budget_adjust 走 BudgetLedger + 成本预测投影（GOAL-001 cycle 6：EC-04 第一批）
status: IN_PROGRESS
created_at: 2026-09-14
updated_at: 2026-09-14
parent_goal: GOAL-20260912-001
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260912-001 cycle 6（/goal 持续循环迭代指令）；范围=EC-04 的 budget_adjust 与成本预测两项；真 pause-resume/实验队列/artifact diff/memory policy（G16）属后续 cycle"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260914-046 — budget_adjust 与成本预测（cycle 6，EC-04 第一批）

## 目标

把两个"诚实 501/缺口"的深水区语义落地为消费既有 BudgetLedger 的真实能力：

- **budget_adjust**：`POST /runs/{id}/interventions` 的 `budget_adjust` 分支从
  恒 501 改为走 BudgetLedger 正式面——调整以 **reservation 生命周期**表达：
  `release` 既有预留 + `reserve` 新额度（append-only 账本上无"原地改数"，
  与 WORKFLOW_RELIABILITY 的 non-idempotent compensation 语义一致）。
  运行中语义变更（protocol/agent 替换 → Manifest Revision/Fork）**保持 501**
  （replace_agent 不在本 cycle）。
- **成本预测投影**：`GET /runs/{id}/cost-forecast`——从 BudgetLedger snapshot
  的 reservations（已预留未消耗）与 usage entries（已消耗）推导前瞻视图：
  remaining = reserved − consumed（按 resource_type 聚合，混合币种/UNKNOWN
  诚实标注）。纯只读投影，不外推未预留的未来开销（不假装能预测未预留部分）。

## 诚实边界

- 账本 append-only：adjust 产生新的 reservation/ref 记录，不修改历史条目。
- 预测只覆盖**已预留**部分；未预留的未来用量不预测（页面如实标注）。
- UNKNOWN 成本条目按既有语义不得计 0。

## 范围

- 包含：
  - WP-A 应用层：`packages/application/run_orchestration/budget_adjust.py`
    （AdjustmentCommand + 执行函数：release+reserve、审计返回）。
  - WP-B API：`interventions` budget_adjust 分支接线（预算面合法 → 200 +
    调整摘要；预算面缺失 → 503；与状态机正交）；`GET /runs/{id}/cost-forecast`
    + DTO + openapi 再生。
  - WP-C 前端：`govern/budget` 页消费 forecast + `adjust` 动作接 budget_adjust
    （501 移除）；pageSupport/CONSOLE_PAGE_MAP G5/G12 同步。
  - WP-D 测试与收口：api/应用层用例、stub e2e、live e2e、m0、RECHECK。
- 不包含：replace_agent/Manifest Revision/Fork（保持 501）；真 pause-resume
  执行协调、实验队列、artifact diff、memory capability policy（G16）——后续 cycle。

## 架构与数据流

```
POST /runs/{id}/interventions {kind: budget_adjust, ...}
  → BudgetAdjustment.execute(budget, run_id, adjustments)
  → budget.release(old_ref) + budget.reserve(new, policy)（append-only）
  → 返回 {released: [...], reserved_ref: "..."}（审计摘要）

GET /runs/{id}/cost-forecast
  → snapshot.reservations（按 run scope）− snapshot.entries（run 内）
  → 按 resource_type 的 reserved/consumed/remaining + UNKNOWN 计数
```

## 验收条件

- [x] AC-01（WP-A）：调整执行为 release+reserve 组合；预算面 None → 显式错误。
- [x] AC-02（WP-B）：budget_adjust 200（调整摘要）/ 503（无 ledger）；
  replace_agent 仍 501；forecast 端点 UNKNOWN/混合币种诚实；openapi 零漂移。
- [x] AC-03（WP-C）：budget 页 forecast 可见 + adjust 真实生效；G5/G12 更新；
  web 门全绿。
- [ ] AC-04（WP-D）：m0 全绿 + stub/live e2e；push 后 quality-ubuntu 与
  console-frontend 全绿；RECHECK-046 回填。

## 实施清单

- [x] WP-A 应用层 budget_adjust
- [x] WP-B API 分支 + forecast 端点
- [x] WP-C 前端 budget 页 + 文档
- [ ] WP-D 测试 + 本地门 + 收口

## 证据

- WP-A：`packages/application/run_orchestration/budget_adjust.py`
  （AdjustmentCommand/AdjustmentLine/AdjustmentOutcome + execute_budget_adjustment：
  release 既有引用 → reserve 新额度，预算面 None 抛 BudgetAdjustmentError）。
- WP-B：`services/api/routers/approvals.py::_budget_adjust`（+_budget_policy/
  _adjustment_lines）、`services/api/routers/budget_forecast.py`
  （GET /runs/{id}/cost-forecast）、`packages/domain/cost_forecast.py`
  （纯投影：三态计量 + 金额完备状态 + 归属模式）、
  `LedgerSnapshot.reservations_by_ref`（ref → 预留集合，run 归属的权威来源，
  Fake/Sqlite/Postgres 三实现同步）。
- 测试：`tests/api/test_budget_forecast_api.py`（14：200/422/503/404、
  replace_agent 501、真实冻结链路 preflight 预留→调整→预测跟随）、
  `tests/domain/test_cost_forecast.py`（11：跨 run 调用方错误、NO_DATA、
  负剩余、单位不合并不跨币种求和、Decimal 时长、归属传递）。
- WP-C：`apps/web/src/features/budget/{ForecastTable,BudgetAdjustBar,
  forecastPresentation,BudgetPage}`、`api/{types,inspectionClient,runClient,client}.ts`、
  `tests/e2e/budget-adjust.spec.ts`（2）与 live 第 15 例；pageSupport G5/G12 与
  `docs/frontend/CONSOLE_PAGE_MAP.md` G5/G12、`docs/api/CONTROL_PLANE_API.md` 同步。
- 归属诚实：正式 preflight 预留作用域是 `phase:<id>`，只有冻结 manifest 登记的
  ref 能把它们归到 run；ref 不可解析时退化为 `run:<id>` 作用域匹配并在响应
  `attribution` 显式标注（不猜、不静默）。
- 夹具修正：`tests/api/run_fixtures.py` 此前 preflight/编排/ApiDeps 各持一个
  FakeBudgetLedger（生产是同一实例），预算读链在夹具里恒空；已改为共享同一实例。

## 已知风险

- FakeBudgetLedger 与 SqliteBudgetLedger 的 reserve 签名需要 policy；调整时
  policy 来源需明确（沿用 run 启动时的 project policy）。
- 前端 budget 页已有 reservations 展示；adjust 后需刷新两视图。
- budget_adjust 不发 outbox 领域事件（与 pause/resume 同侧）：持久记录是账本
  预留行 + released 标记 + 响应摘要；如需审计事件属后续 cycle。

## 状态历史

- 2026-09-14 由 GOAL cycle 6 派生，进入执行。
- 2026-09-14 WP-A/B/C 完成（本地：ruff/mypy 全绿、api+domain 25 用例、
  stub e2e 2 例、live e2e 15 例、openapi 再生零漂移）；待 m0 与 CI。

## 影响报告

（收口时填写）
