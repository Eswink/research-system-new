---
id: RECHECK-20261013-456
slug: goal-073-ec01-04-write-face-routes-also-refuse-query-parameters
title: 独立复检：GOAL-20261013-073 cycle 1（EC-01…EC-04）—— 写面路由也不再静默吞掉查询参数
plan_id: PLAN-20261013-455
status: COMPLETED
result: PASS
created_at: 2026-10-13
completed_at: 2026-10-13
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: services/api/query_param_guard.py（方法闸门已去；None 只留给无法解析）
  - path: 独立重跑判据（写面 6 例 + 序 40 的 6 例 + 序 37 的 11 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261013-073-press-two-way.txt
---

# RECHECK-20261013-456 — GOAL-20261013-073 cycle 1 独立复检

复检对象：`PLAN-20261013-455`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-write-face-query-params.py` —— 四段读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 实跑（改动前） | `POST /projects?definitely_unknown=1` ⇒ **201**；`PATCH /projects/{id}?zz=1` ⇒ **200** |
| 2 | 射程清单 | **63 条**非读面路由，**声明查询参数的 0 条** |
| 3 | 影响面 | 写调用点 626；**同行带查询串 0**（如实登记为上界读数，逐条判定由全量回归承担） |
| 4 | 缺省基线 | `POST /projects` ⇒ 201（五键）；`PATCH /projects/{id}` ⇒ 200（同键） |

### 2. EC-02 写面接通（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ **665 passed**；
新模块 `tests/api/test_write_face_query_params_are_refused.py` ⇒ **6 passed**。逐条复核：

- **写面 POST/PATCH 带任何查询参数 ⇒ 422 + 点名 + 明写「不接受查询参数」**；
- **多个未知逐个点名**（`alpha` / `beta` 都在）；
- **缺省写形态逐字不变**（201/200 + 五键）；
- **读面不回归**（已声明给 known 清单；未声明的同样拒绝）；
- **非 API 路径**（GET/POST `/nope`）⇒ 404（既有语义）；
- **写面体纪律不回归**（序 39 的 `nam` typo ⇒ 422 点名在 `loc`）。

### 3. EC-03 射程如实（独立重跑）

`pytest tests/contracts tests/tooling -q` ⇒ **1999 passed / 72 skipped**；
`tests/e2e` ⇒ **307 passed / 13 skipped**；**live e2e** ⇒ **53 passed**。

- **读面判据（序 36/37/38/40）与写面体判据（序 39）全绿**；
- **四处改签已申报**（射程**扩大**，非收窄）：
  ① 序 37 判据 `test_the_guard_is_inert_for_non_read_methods` ⇒ 改名 + 改判
  「方法不影响导出面读数；`None` 只留给 route 缺位」；
  ② 序 40 判据 `test_the_write_face_is_not_in_this_scope` ⇒ 改名 + 改判（⇒ 422）；
  ③ 序 36 判据的过期注释更正；
  ④ **两处收口断言集**（`goal069` 的 read-methods-gate 判**关系**；`goal072` 的 Y-4 受判面名同步）
  —— 该改签由 `test_closeout_verifiers_run_their_own_assertions` **当场抓到红**（真红），
  修后四验证器（069/070/071/072）逐条全绿（64/62/60/61 条判词）；
- **快照零 diff**（`tools/gen_openapi.py` 后 `git diff --numstat` ⇒ 空 —— 本轮不动签名）。

### 4. EC-04 两向反证（独立重跑）

`uv run --frozen --no-sync python -B scratch/goal073_press.py`：

- **BASELINE（未按压）GREEN**（23 passed）；
- `Z-1`（写面又被静默忽略）/ `Z-2`（读面被误伤）/ `Z-3`（缺省形态被改动）/
  `Z-4`（读面未声明面被误伤）⇒ **全 RED，且首跑即全红（无假绿）** ——
  本轮判据把两侧都钉住（写面 ⇒ 422 + 读面两支各自形态 + 缺省逐字），
  未重演序 39/40 的假绿形态；
- 逐条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`；零进程泄漏（实测）；
- 归档 `.cursor/plans/goals/evidence/GOAL-20261013-073-press-two-way.txt`（二进制、`CR=0`）。

## 结论

**PASS**。EC-01…EC-04 各自有独立重跑证据；四向反证全红且字节复原（首跑即全红）；
射程如实（读面不回归、写面体不回归、快照零 diff）；四处改签**逐条申报**为射程扩大，
其中两处被门当场抓到并修复。「静默吞掉」族**五面全收口**。
**残余**：作者鉴权 / 无路由路径（404 既有语义）—— 逐条保留在 GOAL 的「残余与受限面」一节。
**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
