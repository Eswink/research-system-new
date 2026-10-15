---
id: RECHECK-20261015-488
slug: goal-080-ec01-the-design-source-is-declared-and-run-scoped
title: GOAL-080 cycle 1 复检 — 计划派生的设计读取器（EC-01）
status: COMPLETED
result: PASS
created_at: 2026-10-15
updated_at: 2026-10-15
plan_id: PLAN-20261015-487
parent_goal: GOAL-20261015-080
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261015-488 — GOAL-080 cycle 1

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | **读取器在树且三条纪律逐条成立** | **PASS** | `packages/application/experiments/design_from_plan.py`（193 行）：确定性（只读 `ArtifactStore`，AST 扫**零**传输层名字）/ run 作用域（`evidence.run_id` 过滤）/ fail-closed（六态点名） |
| AC-2 | **run 作用域真的在过滤** | **PASS** | 两条判据：他 run 登记 ⇒ 本 run 视角「nothing is registered」；两 run 都在场 ⇒ 读到的**必须**是本 run 那份（`["mine"]`） |
| AC-3 | **fail-closed 判词互不相同** | **PASS** | 六条点名各自独立（无登记 / 无制品 / 无设计块 / 畸形 / 空臂 / 多制品）—— 六条 `match=` 各不相同 |
| AC-4 | **白名单就是参数面那一份** | **PASS** | 自检用例断言点名里含 `ALLOWED_PARAMETERS` 每个键；越界键点名 |
| AC-5 | **三向按压全 RED 且逐字节复原** | **PASS** | `scratch/goal080c1_press.py`：V10-1/2/3 `BASELINE GREEN=True 按压 RED=True sha 复原一致=True`；归档 `evidence/GOAL-20261015-080-ec01-press-two-way.txt`（743 B、`CR=0`） |
| AC-6 | **受影响套件零回归** | **PASS** | `tests/application` + `test_two_arm_experiment_offline.py` **1056 passed, 1 skipped** |
| AC-7 | **规划期实测更正在档** | **PASS** | GOAL 的 cycle 0 行 + PLAN-487 都记着：原设计（`inputs:` 声明）与 `test_declared_input_sources.py` 的判据**不相容** ⇒ 改走执行期 run 作用域读，**一条既有判据未动** |
| AC-8 | **四道门** | **PASS** | `ruff check` / `ruff format --check` / `mypy` 全绿；193 / 276 行均 ≤ 450 |

## 警告（如实登记）

- **`W-1`**：本 cycle 只做「**读**」（来源可声明 + 读取器）；「**谁写**设计块」与
  「设计的**效果**（换计划 ⇒ 换实验）」是 EC-02 / EC-03，**不在本 cycle**。
- **`W-2`**：读取器**未接线**到装配面（本 cycle 判的是读取器本体与它的属性）；
  接线是 EC-02 的事 —— 如实登记，避免把「组件在树」读成「产品路径已用」。
- **`W-3`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。

## 未覆盖的面

- 设计块由**模型**写出的形态（EC-02/EC-04）；
- 装配接线与端到端「换计划 ⇒ 换实验」（EC-02/EC-03）。

## 无可复用事实需要另建工程记忆

本轮教训（`inputs:` 的既有口径与「phase 间产物引用」不相容 ⇒ 走执行期读）**已并进**
`MEM-20261014-221` 的「声明但从未构造是死缝」家族语境（同一判断手法：先读既有判据
**实际断言什么**，再决定新面挂在哪）；无须另立条目。

## 结论

**PASS。** EC-01 成立：设计的**来源可声明**，且读是**确定性、run 作用域、fail-closed** 的。
三条承重件（run 过滤 / 白名单 / 空臂）各被按压一次、都咬住且逐字节复原。

**本 cycle 最有价值的读数**是规划期那次实测更正：原设计想复用 `phase.inputs`，
而**既有判据**（`test_declared_input_sources.py`）与**既有口径**
（「只声明外部供应，不解析 phase 间产物引用」）都把它排除 ⇒ 改走执行期读 ——
**没有为让新目标成立而改任何既有判据**。
