---
id: RECHECK-20261013-454
slug: goal-072-ec01-04-routes-without-declared-query-params-also-refuse-them
title: 独立复检：GOAL-20261013-072 cycle 1（EC-01…EC-04）—— 未声明查询参数的路由也不再静默吞掉
plan_id: PLAN-20261013-453
status: COMPLETED
result: PASS
created_at: 2026-10-13
completed_at: 2026-10-13
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: services/api/query_param_guard.py（空集支改拒绝；None 支一字不动）
  - path: 独立重跑判据（未声明面 6 例 + 序 36 的 8 例 + 序 37 的 11 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261013-072-press-two-way.txt
---

# RECHECK-20261013-454 — GOAL-20261013-072 cycle 1 独立复检

复检对象：`PLAN-20261013-453`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-undeclared-query-params.py` —— 四段读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 实跑（改动前） | `/projects?definitely_unknown=1` ⇒ **200**；`/health?zz=1` ⇒ **200** |
| 2 | 射程清单 | **58 条**未声明查询参数的 GET 路由（逐条） |
| 3 | 影响面 | 17 处命中逐条分类：12 处已声明路由 / 2 处 false positive / **2 处真受判面**（序 36/37 的对照臂） |
| 4 | 缺省基线 | `/projects` ⇒ 200（list[1]）；`/health` ⇒ 200（`['composition','pricing_degraded','status','version']`） |

### 2. EC-02 未声明面接通（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ **653 passed**；
新模块 `tests/api/test_undeclared_query_params_are_refused.py` ⇒ **6 passed**。逐条复核：

- **未声明读面收到任何查询参数 ⇒ 422 + 点名**（4 条跨模块样本，正文明写
  `this route accepts no query parameters`）；
- **多个未知逐个点名**（`alpha` / `beta` 都在）；
- **缺省形态逐字不变**（`/projects` 200 + list；`/health` 200 + 四键）；
- **非 API 路径**（`/nope?zz=1`）⇒ 404（与本纪律无关）；
- **已声明面照旧**（给**该路由的** known 清单，非「不接受」措辞）；
- **写面不在射程**（**带查询参数**的写请求 ⇒ 201；`None` 支一字不动）。

### 3. EC-03 射程如实（独立重跑）

`pytest tests/contracts tests/tooling -q` ⇒ **1999 passed / 72 skipped**；
`tests/e2e` ⇒ **307 passed / 13 skipped`；**live e2e** ⇒ **53 passed**。

- **已声明面（序 37/38）不回归**（11 例全绿）；
- **写面（序 39）不回归**（`test_write_body_typos_are_named.py` 6 例全绿）；
- **两处对照臂改签已申报**：序 36 的 `test_the_range_is_the_two_memory_gets_only` 与
  序 37 的 `test_routes_without_declared_parameters_are_untouched` —— 原断言
  「未声明读面不被打断」**正是序 40 要改变的行为** ⇒ 改签为「未声明读面同样 422」
  （含语义变化注释）。**如实登记为射程扩大**（非收窄、非强度不变）；
- **快照零 diff**（`tools/gen_openapi.py` 后 `git diff --numstat` ⇒ 空 —— 本轮不动签名）。

### 4. EC-04 两向反证（独立重跑）

`uv run --frozen --no-sync python -B scratch/goal072_press.py`：

- **BASELINE（未按压）GREEN**（25 passed）；
- `Y-1`（未声明面又被静默忽略）/ `Y-2`（已声明面被误伤）/ `Y-3`（缺省形态被改动）/
  `Y-4`（非读面被误伤：射程越界）⇒ **全 RED**；
- `Y-4` **首跑 GREEN**（判据面缺口：写面**带**查询参数的对照臂缺位 ⇒ 射程越界会假绿）
  ⇒ 补断言后 RED —— **同签名 1 次修复，未超 `fix_policy`**（`same_signature_retries: 2`）；
- 逐条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`；零进程泄漏（实测）；
- 归档 `.cursor/plans/goals/evidence/GOAL-20261013-072-press-two-way.txt`（二进制、`CR=0`）。

## 结论

**PASS**。EC-01…EC-04 各自有独立重跑证据；四向反证全红且字节复原；射程如实
（`None` 支一字不动、已声明面与写面不回归、快照零 diff）；两处改签**逐条申报**为射程扩大。
**残余**：非读面的查询参数检查（另一族，登记在案）—— 逐条保留在 GOAL 的「残余与受限面」一节。
**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
