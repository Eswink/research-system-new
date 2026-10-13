---
id: RECHECK-20261013-448
slug: goal-069-ec01-04-the-rule-covers-every-declared-route
title: 独立复检：GOAL-20261013-069 cycle 1（EC-01…EC-04）—— 未知查询参数纪律扩到每条已声明路由
plan_id: PLAN-20261013-447
status: COMPLETED
result: PASS
created_at: 2026-10-13
completed_at: 2026-10-13
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: services/api/query_param_guard.py（签名导出 + 应用级依赖注册）
  - path: 独立重跑判据（全员覆盖 11 例 + 序 36 回归 8 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261013-069-press-two-way.txt
---

# RECHECK-20261013-448 — GOAL-20261013-069 cycle 1 独立复检

复检对象：`PLAN-20261013-447`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-query-param-coverage.py` —— 五段读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 已声明查询参数的 GET | **9 条**（两个独立面交叉核对：OpenAPI `parameters[in=query]` = 68 条 GET 里的 9；逐模块 router 对象 = 67 条里的 9；**逐条相同=True**） |
| 2 | 实跑打错参数名 | `/notifications?limt=5` ⇒ 200；`/cost-forecast?horizon_day=7` ⇒ 200（**静默吞掉** —— 改动前） |
| 3 | 零命中 | 只有序 36 的两文件（守卫模块 + 记忆路由） |
| 4 | 射程分类 | GET 总数 68 / 已声明 9 / 无参数 59（无参数面本轮**不**覆盖） |
| 5 | 序 36 守卫在位 | 守卫模块在：True；记忆路由调用点 2 处 |

### 2. EC-02 全员覆盖（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ **629 passed**（含新 11 例）；
新模块 `tests/api/test_unknown_query_params_cover_every_declared_route.py` ⇒ **11 passed**。逐条复核：

- **逐条 9 条已声明路由**打错参数名 ⇒ 422 + 点名（`required` 片段保证 422 是点名而非「缺必填」）；
- 正文给出**该路由自己**的已知集（`/notifications` 的正文含 `limit` 不含 `horizon_days`）；
- **多个未知逐个点名**（`endpoint` / `endpint` 都在）；
- **已知参数逐字仍工作**（`?limit=` / `?state=` / `?kind=` / `?date_from=` / `?scope=` 全 200）；
- **缺省形态逐字不变**（`/memory` 键仍是 `['records','scope_note']`）；
- **受判面 = app 全部已声明路由**（与 `app.openapi()` 的声明面集合相等 —— 漏一条即判红）；
- **行为自证不手写清单**：**事后注册**的新路由（带全新参数名）自动受纪律（静态 + 行为两条）。

### 3. EC-03 射程如实（独立重跑）

`pytest tests/api tests/contracts tests/tooling -q` ⇒ 2635 passed；`tests/e2e tests/observability` ⇒
439 passed；`tests/application tests/adapters` ⇒ 1574 passed。

- **对照臂**：未声明参数的路由（`/projects`、`/health`、`/runs/.../events`）收到无关参数**不**被 422；
- **序 36 的记忆读面判据仍在树且全绿**（8 例，本轮**未**改它）；
- `tools/gen_openapi.py` 重生成后 `git diff --numstat` ⇒ **零 diff**（参数校验面**不进** schema ——
  如实登记为「快照不变」的**理由**，不是遗漏）；
- **一处行为变化如实登记**：`/memory?at=` 原先被序 36 的**并集**守卫放行（并集含 `at`），
  现按**该路由自己的签名**被拒（422 点名 `at`，正文给出 `proposed_by, scope`）——
  这是「已知集从签名导出」的直接后果；该参数对 `/memory` 本就不存在语义。

### 4. EC-04 两向反证（独立重跑）

`uv run --frozen --no-sync python -B scratch/goal069_press.py`：

- **BASELINE（未按压）GREEN**（19 passed）；
- `W-1`（导出面返回空集）/ `W-2`（把路径参数当查询参数）/ `W-3`（缺省形态被改动）/
  `W-4`（只覆盖记忆读面）⇒ **全 RED**；
- 逐条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`；
- 锚点替换前**逐条数命中数**（`== 1` 才替换 —— `>1` 禁止批量语义）；
- 归档 `.cursor/plans/goals/evidence/GOAL-20261013-069-press-two-way.txt`（二进制写盘、`CR=0`）。

## 结论

**PASS**。EC-01…EC-04 各自有独立重跑证据；四向反证全红且字节复原；快照零 diff；
射程如实（无参数路由不受影响；序 36 不回归）。**残余**：无参数路由的参数检查（另成一面）、
写面请求体额外字段（pydantic 既有面）—— 逐条保留在 GOAL 的「残余与受限面」一节。
**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
