---
id: PLAN-20261015-479
slug: goal-079-ec02-two-arms-with-a-control
title: GOAL-079 cycle 2 — 多臂/对照真跑（EC-02）
status: DONE
created_at: 2026-10-15
updated_at: 2026-10-15
parent_goal: GOAL-20261015-079
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-480-goal-079-ec02-two-arms-with-a-control.md
memory_entries:
  - .cursor/memory/entries/MEM-20261015-222-four-decisions-when-a-hardcoded-value-becomes-declared.md
---

# PLAN-20261015-479 — GOAL-079 cycle 2

## 验收条件

- [x] 臂声明在树（`arms.py`：两种形态 + 重复/非法点名拒绝）
- [x] 臂 id **不复用**「一 run 一实验」那条既有派生（`arm_experiment_id`）
- [x] 派发体**逐臂各跑一次**（真 runner；只换执行体）
- [x] 经**产品路径**的一次 run：两个臂各自落库、读面逐臂可读、**指标值不同**
- [x] 反证臂（只声明一个臂 ⇒ 只有一次实验）在树
- [x] 五向按压全红且逐字节复原
- [x] 既有判据零放宽（定向套件 + 全量 m0 绿）

## 目标（本 cycle 的可独立验收主题）

**EC-02**：一次 run 里**至少两个臂**（含对照）各执行一次实验，臂归属**由声明决定**
（不是按顺序猜），两臂的指标**各自的落库值可读**。

## 设计（为什么这样接）

### 建档实测的关键约束：既有派生是「**一 run 一实验**」

`experiment_run_id_of(run_id)` 只吃 run id ⇒ **两个臂会撞同一个实验 id**（实测逐字）。
⇒ 臂必须有**自己的** id 空间：`arm_experiment_id(run_id, arm)`（按 run + 臂确定性派生，
合法 UUID4 布局）。判据断言：两臂 id 不同、且都**不等于**单臂那条（否则「哪个实验属于
哪个臂」不可判）。

### 臂声明在装配面（与参数面同层）

与 EC-01 的 `parameters` 同一层理由：「这次跑什么」是装配知识。臂支持**两种声明形态**：
`{臂名: 参数}`（紧凑）与 `[{name, parameters}]`（显式、**携带顺序** —— 顺序是语义的一部分：
第一个是**主臂**，门禁按它裁决）。重复臂名 / 形态不符 ⇒ **点名拒绝**。

### 主臂代表这次「任务」，全部臂落库

门要的是**一个**裁决（`TaskExecutionResult` 就是一次任务）。多臂不是「多次任务」，
而是「**一次任务的多次运行**」⇒ 主臂代表任务，其余臂的读数在**读面**上逐条可查。
结果消息**点名全部臂**（读消息的人不必回查读面）。

### 臂参数与装配缺省**合并**（臂可只给差异）

`params = {**assembly.parameters, **arm.parameters}` ⇒ 臂覆盖装配缺省；
`control` 臂**不给参数**（脚本回落既有常量）⇒ 它就是**对照**。

## 实施清单

1. **WP-A**（产品）：`experiments/arms.py`（119 行）+ 装配面 `arms` 槽 + 派发体逐臂派发
   （`_arm_deps` / `_primary_arm_result`）+ 计划按臂派生。
2. **WP-B**（判据）：`tests/application/test_experiment_arms.py`（14 例）+
   `tests/e2e/test_two_arm_experiment_offline.py`（6 例，含**真容器**的 run 级一条）。
3. **WP-C**（记录 + 门）：本文件 + RECHECK + GOAL 回写 / ALL_PLAN 同提交；五向按压；m0。

## 影响报告

- **产品代码**：新增 1 个模块（119 行）；`experiment_support.py` 加 `arms` 槽 +
  逐臂派发 + 计划按臂派生（**未声明臂 ⇒ 逐字不变**，判据断言）。
- **判据面**：新增 2 个模块（20 例）；既有判据**零放宽**。
- **零新路由 / 零 DTO 改动 / 零快照改动 / 无 schema 迁移 / 无依赖 / 无出网新增。**

## 残余与未覆盖

- EC-03（臂间**可比**：同指标求差 + 缺指标点名）/ EC-04（真实中转站）/ EC-05（收口）
  **不在本 cycle**；
- **臂数 > 2** 未单独取证（本 cycle 的两臂形态可推广，但没为三臂以上写判据 —— 如实登记）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| 臂声明判据 | **14 passed** | `… -m pytest tests/application/test_experiment_arms.py -q` |
| e2e（含真容器 run 级） | **6 passed** | `… -m pytest tests/e2e/test_two_arm_experiment_offline.py -q` |
| run 级读数 | `state=SUCCEEDED`；读面 **2** 条实验；两臂比率 **7990.0 vs 178.5**（同指标、不同参数 ⇒ 不同读数） | 判据 `TestTheTwoArmsLandOnTheRunReadFace` |
| 五向按压 | `V9-1…V9-5` 全 `BASELINE GREEN=True / 按压 RED=True / sha 复原一致=True` | `… -B scratch/goal079_press.py` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | IN_PROGRESS | cycle 2 建档（EC-02 的臂 id 约束与派发设计）。 |
| 2026-10-15 | DONE | WP-A…WP-C 落地：臂声明 + 逐臂派发 + run 级取证；五向按压全红。 |
