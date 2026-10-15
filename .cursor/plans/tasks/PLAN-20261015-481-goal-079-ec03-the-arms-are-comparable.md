---
id: PLAN-20261015-481
slug: goal-079-ec03-the-arms-are-comparable
title: GOAL-079 cycle 3 — 臂间可比（EC-03）
status: DONE
created_at: 2026-10-15
updated_at: 2026-10-15
parent_goal: GOAL-20261015-079
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-482-goal-079-ec03-the-arms-are-comparable.md
memory_entries:
  - .cursor/memory/entries/MEM-20261015-222-four-decisions-when-a-hardcoded-value-becomes-declared.md
---

# PLAN-20261015-481 — GOAL-079 cycle 3

## 验收条件

- [x] 对比器在树（`arm_comparison.py`：纯函数，输入两臂指标 ⇒ 差值读数）
- [x] **同名列才比**；单侧指标**逐臂点名**（`missing_in_left` / `missing_in_right`）
- [x] **缺指标不折算成 0**（两向判据）
- [x] 非数值（布尔 / 字符串 / 嵌套）**排除并点名**（布尔不当 0/1）
- [x] 空对比 ⇒ `comparable is False`（没有内容 ≠ 差值为 0）
- [x] **真容器 run** 上取读面两条记录求差，判定值与算术一致且非 0
- [x] 七向按压全红且逐字节复原
- [x] 既有判据零放宽（定向套件 + 全量 m0 绿）

## 目标（本 cycle 的可独立验收主题）

**EC-03**：读面能回答「**两臂的同一个指标差多少**」——不是「两条记录都在」而已；
差异由**落库的指标值**算出（可复算），缺指标时**点名**而不是给 0。

## 设计（为什么这样接）

### 对比是**纯函数**，落在 application 层

差值不是**持久事实**（它随时可由两条记录重算）⇒ 把它写进域会让「同一份落库状态」
有两个真相。本模块输入两份指标映射、输出读数：与 `report_facts.metrics_of` 同层。

**零耦合**：不新增 DTO 字段 / 路由 / OpenAPI 快照改动 —— 读面已经给出两条记录的
`metrics`（EC-02 的产物），对比器只是**消费**它。这样 EC-03 的交付面是
「**可算**」而不是「新增一个面」。

### 三条纪律（都是**判据拒绝**的形态）

1. **同名列才比**：`left ∩ right`；只在单侧的指标**不得**产生差值条目 ——
   把「没测」当成「测出 0」会**伪造**一个很大的差值（判据两向都钉）；
2. **非数值排除**：`True - False = 1` 是算术成立、语义荒唐 ⇒ 布尔 / 字符串 / 嵌套
   **进 `not_numeric` 逐条点名**，不进差值；
3. **空对比 ≠ 0**：没有任何可比指标 ⇒ `comparable is False`（**没有结论**，
   而差值为 0 是一个**结论**）。

### 符号约定写在字段语义里

`delta = right − left`（**右臂减左臂**）—— 不打哑谜：字段注释逐字声明，
判据按该约定核对具体数值（`178.5 - 7990.0 = -7811.5`）。

## 实施清单

1. **WP-A**（产品）：`experiments/arm_comparison.py`（130 行，纯函数）。
2. **WP-B**（判据）：`tests/application/test_arm_comparison.py`（13 例）+
   e2e 增 2 例（真容器 run 的读面取数 + 布尔点名）。
3. **WP-C**（记录 + 门）：本文件 + RECHECK + GOAL 回写 / ALL_PLAN + 七向按压；m0。

## 影响报告

- **产品代码**：新增 1 个模块（130 行，纯函数）——**不改任何既有模块**。
- **读面 / DTO / 路由 / 快照**：**零改动**（对比消费既有读面载荷）。
- **判据面**：新增 1 个模块（13 例）+ e2e 增 2 例；既有判据**零放宽**。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化、无出网新增。**

## 残余与未覆盖

- EC-04（真实中转站）/ EC-05（收口）**不在本 cycle**；
- **多臂（>2）的对比**未取证（两两对比可推广，但没为三臂写判据）；
- 「哪个臂更**好**」**不做**：那要方向性判据（越小越好 / 越大越好），
  属**计划**声明的事（本 GOAL 只给**差值**这个可算事实，不下好坏结论）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| 对比判据 | **13 passed** | `… -m pytest tests/application/test_arm_comparison.py -q` |
| e2e（含真容器 run 级） | **8 passed** | `… -m pytest tests/e2e/test_two_arm_experiment_offline.py -q` |
| 真 run 读数 | 两条记录 ⇒ 差值 `178.5 - 7990.0 = -7811.5`（判据**自己算一遍**核对）；`agreement` 进 `not_numeric` | 判据 `TestTheArmsAreComparableFromTheReadFace` |
| 七向按压 | `V9-1…V9-7` 全 `BASELINE GREEN=True / 按压 RED=True / sha 复原一致=True` | `… -B scratch/goal079_press.py` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | IN_PROGRESS | cycle 3 建档（EC-03 的对比面与三条纪律）。 |
| 2026-10-15 | DONE | WP-A…WP-C 落地：纯函数对比器 + 13 例 + e2e 2 例；七向按压全红。 |
