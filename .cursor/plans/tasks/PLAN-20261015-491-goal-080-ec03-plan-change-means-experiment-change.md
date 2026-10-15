---
id: PLAN-20261015-491
slug: goal-080-ec03-plan-change-means-experiment-change
title: GOAL-080 cycle 3 — 换计划 ⇒ 换实验（EC-03）
status: DONE
created_at: 2026-10-15
updated_at: 2026-10-15
parent_goal: GOAL-20261015-080
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-492-goal-080-ec03-plan-change-means-experiment-change.md
memory_entries:
  - .cursor/memory/entries/MEM-20261015-222-four-decisions-when-a-hardcoded-value-becomes-declared.md
---

# PLAN-20261015-491 — GOAL-080 cycle 3

## 验收条件

- [x] **换计划 ⇒ 换实验**：同一装配 + 两份计划 ⇒ 两套不同的臂/实验（e2e 实测）
- [x] 计划里的参数**逐键**进容器环境（对照臂无、处理臂有）
- [x] 计划驱动的臂**不撞**单臂命名空间
- [x] **来源唯一**在派发面同样成立（拒绝发生在**跑任何实验之前**）
- [x] 未声明来源 ⇒ 单臂 + 旧派生 id（零回归）且**连坏计划都不读**（路径分派可判）
- [x] 臂 id **确定性 + 换 run 会变**（哈希派生的正确判法）
- [x] 记录面（PLAN + RECHECK）与 GOAL 回写；`ALL_PLAN` 投影

## 目标（本 cycle 的可独立验收主题）

**EC-03**：**「设计因计划而不同」**在**产品派发路径**上是可判定的 —— 不是「组件在树」，
而是「同一份装配上，计划内容决定跑什么」。

## 实施清单

1. **WP-A**（e2e 判据）：`tests/e2e/test_experiment_design_from_the_plan.py`（8 例；
   真 `sandbox_experiment_runner` + 受控执行体，不出容器/不出网）。
2. **WP-B**（夹具如实化）：本文件的执行体**如实造出**制品以满足**既有**准入检查
   （不是绕过）；`_seed_plan` / `_plan_assembly` 支持指定 run（换-run 判据需要）。
3. **WP-C**（记录 + 门）：本文件 + RECHECK + GOAL 回写 / `ALL_PLAN`；m0。

## 影响报告

- **产品代码**：**零改动**（本 cycle 只加 e2e 判据与夹具能力）。
- **读面 / DTO / 路由 / 快照**：零改动。
- **判据面**：**只增**（新 e2e 文件）；`test_experiment_design_decides.py` 的 `_seed_plan`
  加一个**带缺省值的可选形参**（既有调用点逐字不变）—— 如实申报。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**

## 残余与未覆盖

- **真容器**上的这一读数（本 cycle 的执行体是替身；容器那一段由既有
  `requires_docker` 套件承担）—— 如实登记；
- live（EC-04）；自举收口（EC-05）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| e2e 判据 | **8 passed**（换计划 / 逐键参数 / 不撞命名空间 / 来源唯一派发前拒绝 / 零回归 ×2 / 确定性 ×2） | `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_experiment_design_from_the_plan.py -q` |
| 合计（含 cycle 1/2 判据） | **21 passed** | 同上 + `tests/application/test_experiment_design_decides.py` |
| 规模门 | **1278 passed**（含 `test_python_source_limits.py`；两个判据文件均 ≤ 450 行、无超 50 行函数） | `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_python_source_limits.py -q` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | IN_PROGRESS | cycle 3 建档（端到端「换计划 ⇒ 换实验」）。 |
| 2026-10-15 | DONE | 8 例 e2e 落地；替身如实造制品以满足既有准入检查；21 passed。 |
