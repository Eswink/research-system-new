---
id: PLAN-20261015-489
slug: goal-080-ec02-the-design-content-decides-the-experiment
title: GOAL-080 cycle 2 — 设计内容真正决定实验（EC-02）
status: DONE
created_at: 2026-10-15
updated_at: 2026-10-15
parent_goal: GOAL-20261015-080
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-490-goal-080-ec02-the-design-content-decides-the-experiment.md
memory_entries:
  - .cursor/memory/entries/MEM-20261015-222-four-decisions-when-a-hardcoded-value-becomes-declared.md
---

# PLAN-20261015-489 — GOAL-080 cycle 2

## 验收条件

- [x] 装配面新增 `design_source`（缺省 `None` ⇒ 既有语义逐字不变）
- [x] `design_source="plan"` ⇒ 臂从**本 run** 的计划产物内容读出（执行期解析）
- [x] **来源唯一**：计划来源与装配面声明的臂**互斥**，冲突时点名拒绝
- [x] **未认得的来源名点名拒绝**（不静默回落）
- [x] 判据成对（正向 / 来源唯一 / fail-closed / 零回归）+ 例数下界
- [x] 三向按压全 RED + 逐字节复原（归档进树、`CR=0`）
- [x] 记录面（PLAN + RECHECK）与 GOAL 回写；`ALL_PLAN` 投影

## 目标（本 cycle 的可独立验收主题）

**EC-02**：设计**内容**（不是装配常量）决定实验的臂与参数 —— 且来源**唯一**。

## 实施清单

1. **WP-A**（装配面）：`SandboxExperimentAssembly.design_source` + `_arms_for(assembly, task)`
   （唯一解释点：缺省 ⇒ 装配声明；`"plan"` ⇒ 执行期读计划产物；两条并存 / 未知名 ⇒ 点名）。
2. **WP-B**（判据）：`tests/application/test_experiment_design_decides.py`（11 例）。
3. **WP-C**（记录 + 门）：本文件 + RECHECK + GOAL 回写 / `ALL_PLAN`；按压归档；m0。

## 影响报告

- **产品代码**：`services/api/experiment_support.py` —— 新增一个装配字段 + 一个解释函数
  （**纯新增**；既有 `declare_arms` 单臂/臂路径逐字不变）。
- **读面 / DTO / 路由 / 快照**：**零改动**。
- **判据面**：**只增**；既有判据一条不动（含 GOAL-079 的参数 / 臂 / 对比三条判据面）。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**

## 残余与未覆盖

- 「**换计划 ⇒ 换实验**」的端到端读数（含真容器）是 EC-03；
- 「设计块由**模型**写出」是 EC-04（live）；
- 其余见 GOAL-080 的「残余与未覆盖范围」一节。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| 判据 | **11 passed**（正向 ×2 / 来源唯一 ×4 / fail-closed ×2 / 零回归 ×3） | `uv run --frozen --no-sync python -B -m pytest tests/application/test_experiment_design_decides.py -q` |
| 按压 | V10-4…V10-6 **全 RED** + `sha 复原一致=True`；归档 804 B、`CR=0` | `uv run --frozen --no-sync python -B scratch/goal080c2_press.py` |
| 受影响套件 | **1064 passed, 1 skipped** | `uv run --frozen --no-sync python -B -m pytest tests/application tests/api/test_sandbox_experiment_seam.py -q` |
| 规模门 | `experiment_support.py` 361 行；无超 50 行函数 | `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_python_source_limits.py -q` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | IN_PROGRESS | cycle 2 建档（把 cycle 1 的读取器接进产品面 + 来源唯一）。 |
| 2026-10-15 | DONE | 装配面 `design_source` + `_arms_for` 落地；11 例判据；三向按压全 RED 且逐字节复原。 |
