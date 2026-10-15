---
id: RECHECK-20261015-492
slug: goal-080-ec03-plan-change-means-experiment-change
title: GOAL-080 cycle 3 复检 — 换计划 ⇒ 换实验（EC-03）
status: COMPLETED
result: PASS
created_at: 2026-10-15
updated_at: 2026-10-15
plan_id: PLAN-20261015-491
parent_goal: GOAL-20261015-080
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261015-492 — GOAL-080 cycle 3

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | **换计划 ⇒ 换实验**（e2e） | **PASS** | 同一装配：计划 A（`{"only"}`）⇒ **1 次**实验（`arm_experiment_id(RUN_ID,"only")`）；计划 B（`{"a","b","c"}`）⇒ **3 次**实验（逐条对派生 id） |
| AC-2 | **计划参数逐键进容器环境** | **PASS** | 计划写 `n_items=90` ⇒ `request.environment["EXPERIMENT_PARAM_N_ITEMS"] == "90"`（处理臂有、对照臂无） |
| AC-3 | **不撞单臂命名空间** | **PASS** | 计划驱动的臂 id 无一等于 `experiment_run_id_of(RUN_ID)`（既有单臂派生保留） |
| AC-4 | **来源唯一在派发面成立** | **PASS** | 两条来源在场 ⇒ 拒绝**且** `executor.requests == []`（**跑任何实验之前**） |
| AC-5 | **零回归（未声明来源）** | **PASS** | 单臂 + **旧派生 id**（逐字）；且**连坏计划都不读**（装配不带 ledger，另存坏计划也不影响 ⇒ 路径分派可判） |
| AC-6 | **臂 id 的 run 归属可判** | **PASS** | ① 同 run 同计划 ⇒ 同 id（确定性）；② **换 run ⇒ 不同 id**（哈希派生 ⇒ 判这两条，**不**判字面包含） |
| AC-7 | **可溯源** | **PASS** | 每个请求的 `run_id` = 计划里那条臂的确定性派生（逐条 `set(ids) == set(by_arm.values())`） |
| AC-8 | **四道门 + 规模门** | **PASS** | `ruff check` / `format --check` / `mypy` 绿；**1278 passed**（含规模门：两文件 ≤ 450 行、无超 50 行函数） |

## 警告（如实登记）

- **`W-1`**：本 cycle 的 e2e **不出容器**（执行体是受控替身）—— 它判的是**派发**事实；
  「真容器里的这一读数」由既有 `requires_docker` 套件承担，本 cycle **不**声称已跑容器。
- **`W-2`**：测试替身**如实造出**结果制品以满足**既有**准入检查（`evidence_admission` 要求
  终态运行带 spec/result 与制品）—— **不是**绕过；那条检查一字未动。替身的两处约束已写进
  文件 docstring（不静默）。
- **`W-3`**：`_seed_plan` 加了一个**带缺省值**的可选形参（`run_id`）——
  该文件既有调用点逐字不变（如实申报）。
- **`W-4`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。

## 未覆盖的面

- 真容器上的同一读数（`W-1`）；live「模型写设计」（EC-04）；自举收口（EC-05）。

## 无可复用事实需要另建工程记忆

本 cycle 的教训（**准入面在带 ledger 时收紧** ⇒ 替身要如实满足它，而不是绕过）已并进
`MEM-20261015-222` 的「缺省怎么回落」家族语境；无须另立条目。

## 结论

**PASS。** EC-03 成立：**「设计因计划而不同」在产品派发路径上可判定** ——
同一装配 + 两份计划 ⇒ 两套不同的实验（逐条对派生 id 与参数）；来源唯一在派发**之前**
拒绝；未声明来源时既有语义逐字不变（且不读计划）。
