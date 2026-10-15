---
id: PLAN-20261015-477
slug: goal-079-ec01-experiment-parameters-come-from-the-declaration
title: GOAL-079 cycle 1 — 实验参数由声明给出（EC-01）
status: DONE
created_at: 2026-10-15
updated_at: 2026-10-15
parent_goal: GOAL-20261015-079
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-478-goal-079-ec01-experiment-parameters-come-from-the-declaration.md
memory_entries:
  - .cursor/memory/entries/MEM-20261015-222-four-decisions-when-a-hardcoded-value-becomes-declared.md
---

# PLAN-20261015-477 — GOAL-079 cycle 1

## 验收条件

- [x] 参数面在树（`plan_parameters.py`：白名单 + 逐键 + 前缀命名空间）
- [x] 装配面接通（`SandboxExperimentAssembly.parameters` → 执行请求环境）
- [x] 脚本读声明（缺省回落既有常量；非法值**点名失败**，不静默回落）
- [x] 判据 11 例（白名单 / 传递 / 零回归 / 脚本读取 / fail-closed）
- [x] 三向按压全红且逐字节复原
- [x] 既有判据零放宽（定向套件 + 全量 m0 绿）

## 目标（本 cycle 的可独立验收主题）

**EC-01**：把「实验参数」从**脚本模块常量**变成**声明事实** —— 声明经
「装配 → 执行请求 → 容器环境」到达脚本，且**未声明时零回归**。

## 设计（为什么这样接）

### 声明点是**装配面**，不是契约

`TaskContract.experiment` 的 docstring 逐字写着「工作区、会话 id、**种子**属于装配上下文，
**不进契约**」—— 参数是「这次跑什么」的装配知识，不是「这件工作由谁执行」的契约事实。
本 cycle 因此把参数面挂在装配面（与 `--seed` 一类命令行旗标同层）。

### §9：白名单，不是转发

`ALLOWED_PARAMETERS`（`seed` / `n_items` / `duplicate_pairs`）是**声明式放行**；
白名单外的键**点名拒绝**（`UndeclaredExperimentParameterError`）——
「把调用方给的环境原样塞进容器」是**另一个**（更危险）的设计，本 cycle 明确不做。

### 前缀命名空间不相交

容器里参数键带 `EXPERIMENT_PARAM_` 前缀 ⇒ 与执行器自己的 `EXPERIMENT_RUN_ID`
**不可能相撞**（判据断言这一点：参数面覆盖不了执行器的键）。

### 脚本侧：缺省回落 + 非法点名

`_declared_int(name, default)`：**缺席** ⇒ 用既有模块常量（零回归）；**值非法** ⇒
`SystemExit` 点名（**不静默回落** —— 回落会把「声明被吞掉」伪装成「跑成功」）。

## 实施清单

1. **WP-A**（产品）：`packages/application/experiments/plan_parameters.py`（84 行）。
2. **WP-B**（装配）：`SandboxExperimentAssembly.parameters` + 请求环境合并。
3. **WP-C**（脚本）：`_declared_int` 三处参数读取。
4. **WP-D**（判据 + 记录）：`tests/application/test_experiment_parameters.py`（11 例）+
   本文件 + RECHECK + GOAL 回写 + ALL_PLAN + m0。

## 影响报告

- **产品代码**：新增 1 个模块（84 行）；`experiment_support.py` 加一个字段 + 一处环境合并
  （缺省空 ⇒ 请求环境逐字不变）；`examples/experiments/exact_match_index_benchmark.py`
  改成「读声明、回落常量」（缺省路径**实测逐字相同**：`seed=7` / `n_items=800` /
  `duplicates_expected=40`）。
- **契约面 / 协议面 / 读面**：**零改动**（参数不进契约、不进 manifest）。
- **判据面**：新增 1 个模块（11 例）；既有判据**零放宽**。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化、无出网新增。**

## 残余与未覆盖

- EC-02（多臂/对照）/ EC-03（臂间可比）/ EC-04（真实中转站）/ EC-05（收口）**不在本 cycle**；
- 参数**只支持整数**（脚本侧 `_declared_int`）—— 现有三个参数都是整数，
  加类型系统属后续（如实登记，不假装通用）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| EC-01 判据 | **11 passed** | `… -m pytest tests/application/test_experiment_parameters.py -q` |
| 缺省零回归 | `seed=7` / `n_items=800` / `duplicates_found=40`（与改动前逐字相同） | 见判据 `test_the_default_run_matches_the_module_constants` |
| 声明被尊重 | `EXPERIMENT_PARAM_SEED=11` 等 ⇒ `seed=11` / `n_items=120` / `duplicates_found=6` | 见判据 `test_the_declared_parameters_are_honoured` |
| 三向按压 | `V9-1…V9-3` 各 `BASELINE GREEN=True / 按压 RED=True / sha 复原一致=True` | `… -B scratch/goal079_press.py` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | IN_PROGRESS | cycle 1 建档（EC-01 的参数面设计与落点）。 |
| 2026-10-15 | DONE | WP-A…WP-D 落地：参数面 + 装配接线 + 脚本读取 + 11 例判据；三向按压全红。 |
