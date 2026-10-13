---
id: RECHECK-20261014-460
slug: goal-075-ec01-04-empty-values-for-declared-params-are-not-silently-treated-as-filters
title: 独立复检：GOAL-20261014-075 cycle 1（EC-01…EC-04）—— 声明参数空值形态不再静默当筛选值
plan_id: PLAN-20261014-459
status: COMPLETED
result: PASS
created_at: 2026-10-14
completed_at: 2026-10-14
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: services/api/query_param_guard.py（空值臂 + 措辞三分辨）
  - path: 独立重跑判据（空值面 6 例 + 序 37/40/42 回归 24 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261014-075-press-two-way.txt
---

# RECHECK-20261014-460 — GOAL-20261014-075 cycle 1 独立复检

复检对象：`PLAN-20261014-459`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-empty-query-values.py` —— 四段读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 空值两行为 | `?scope=` ⇒ 200 且 `records: []`（载荷含 `filtered_out` ⇒ 走「筛」支）；`?at=` / `?kind=` ⇒ 422 |
| 2 | 分界 = 类型面 | str 型静默（`endpoint_id` ⇒ 200）vs 校验型拒绝（`limit` / `date_from` / `horizon_days` ⇒ 422） |
| 3 | 影响面 | web 客户端已挡空值（`!== ""` 才 `params.set`）⇒ 统一为 422 不打断既有调用 |
| 4 | 缺省基线 | `/memory`（无参）⇒ 200 + 两键 + 1 条；`/notifications` ⇒ 200 + 两键 |

### 2. EC-02 空值臂接通（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ **672 passed**；
新模块 `tests/api/test_empty_query_values_are_refused.py` ⇒ **6 passed**。逐条复核：

- **空值 ⇒ 422 + 点名 + 明写「不接受空值」**（str 型此前静默筛 0 条）；
- **多个空值逐个点名**（`scope` / `proposed_by` 都在）；
- **缺省与已声明值逐字不变**（无参 200 + 两键 + 1 条；`?scope=project` ⇒ `filtered_out` 在）；
- **`list` 声明不在射程**（射程边界）；
- **三臂措辞分辨**（未知 `known:` / 重复 `exactly one value` / 空值 `empty value` 三者互异）；
- **前四面不回归**（未声明 / 写面 / 重复照旧）。

### 3. EC-03 射程如实（独立重跑）

`pytest tests/api tests/contracts tests/tooling -q` ⇒ **2680 passed / 76 skipped**；
`tests/e2e` ⇒ **307 passed / 13 skipped**；**live e2e** ⇒ **53 passed**。

- **四面（序 37/40/41/42）与写面体（序 39）判据全绿**；
- **快照零 diff**（`tools/gen_openapi.py` 后 `git diff --numstat` ⇒ 空 —— 本轮不动签名）。

### 4. EC-04 两向反证（独立重跑）

`uv run --frozen --no-sync python -B scratch/goal075_press.py`：

- **BASELINE（未按压）GREEN**（30 passed）；
- `V5-1`（空值又被静默当成筛选值）/ `V5-2`（`list` 声明被误伤）/ `V5-3`（缺省形态被改动）/
  `V5-4`（重复臂被误伤）⇒ **全 RED**；
- **两条锚点首跑未命中**（缩进差 / 三行锚非唯一）⇒ 按「先数命中数」纪律改用唯一锚点后全红
  —— 这是纪律的现场兑现（非缺陷）；
- 逐条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`；零进程泄漏（实测）；
- 归档 `.cursor/plans/goals/evidence/GOAL-20261014-075-press-two-way.txt`（二进制、`CR=0`）。

## 结论

**PASS**。EC-01…EC-04 各自有独立重跑证据；四向反证全红且字节复原；射程如实
（`list` 边界、缺省与已知值不变、四面不回归、快照零 diff）。
**残余**：作者鉴权 / 通配·模糊匹配 / 三维以上闸门组合 —— 逐条保留在 GOAL 的
「残余与受限面」一节。
**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
