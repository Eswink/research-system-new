---
id: RECHECK-20261015-490
slug: goal-080-ec02-the-design-content-decides-the-experiment
title: GOAL-080 cycle 2 复检 — 设计内容真正决定实验（EC-02）
status: COMPLETED
result: PASS
created_at: 2026-10-15
updated_at: 2026-10-15
plan_id: PLAN-20261015-489
parent_goal: GOAL-20261015-080
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261015-490 — GOAL-080 cycle 2

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | **设计内容真的决定臂** | **PASS** | `_seed_plan` 种一份计划 ⇒ `_arms_for` 返回的臂**就是**计划里那些（含参数逐键 `n_items: 50`）；同一装配 + **两份不同计划** ⇒ **两套不同臂**（`["only_arm"]` vs `["control","treatment"]`） |
| AC-2 | **来源唯一**（两条来源并存 ⇒ 拒绝） | **PASS** | 计划来源 + 装配声明臂同时在场 ⇒ `InvalidInputError` 含 `would be undecidable` 且**点名**已声明臂 |
| AC-3 | **未认得的来源点名拒绝** | **PASS** | `design_source="from_the_ether"` ⇒ `unknown experiment design source`；**即使同时声明了臂也拒绝**（不退化成「有臂就照跑」） |
| AC-4 | **计划来源 fail-closed** | **PASS** | 无计划 ⇒ `ExperimentDesignUnreadableError`；有计划但无设计块 ⇒ 点名 `carries no` —— **不**回落装配常量 |
| AC-5 | **零回归**（未声明来源） | **PASS** | 三条：无声明 ⇒ 空臂；声明臂 ⇒ 照用；**且不读计划**（种一份坏计划也不影响 —— 读取器根本不被调用） |
| AC-6 | **三向按压全 RED 且逐字节复原** | **PASS** | `scratch/goal080c2_press.py`：V10-4/5/6 `BASELINE GREEN=True 按压 RED=True sha 复原一致=True`；归档 `evidence/GOAL-20261015-080-ec02-press-two-way.txt`（804 B、`CR=0`） |
| AC-7 | **受影响套件零回归** | **PASS** | `tests/application` + `tests/api/test_sandbox_experiment_seam.py` **1064 passed, 1 skipped** |
| AC-8 | **四道门** | **PASS** | `ruff check` / `ruff format --check` / `mypy` 全绿；`experiment_support.py` 361 行、无超 50 行函数（规模门 **1267 passed**） |

## 警告（如实登记）

- **`W-1`**：本 cycle 判的是「臂**来自**计划」这一事实；**「哪个臂更好」**与「设计是否真的
  更合理」**无人判**（承 GOAL-079 `W-2` / 本 GOAL `W-2`）。
- **`W-2`**：`design_source` 只认 `"plan"` **一个取值**；将来加别的来源（如「来自人写的
  配置文件」）必须**同轮**加判据（未知来源今天是点名拒绝 —— 这条保证新来源不会被静默接受）。
- **`W-3`**：本 cycle 的读数在**受控装配**上（`_seed_plan` 手种计划产物）；「**真实模型**
  写出的计划块驱动实验」是 EC-04。
- **`W-4`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。

## 未覆盖的面

- 端到端「换计划 ⇒ 换实验」读数（EC-03）；
- live（EC-04）；自举收口（EC-05）。

## 无可复用事实需要另建工程记忆

本 cycle 的可复用面（「来源唯一 ⇒ 两条来源并存必须点名」）**已并进** `MEM-20261015-222`
的「五个决定点」家族（第 2 点「白名单还是转发」的同一手法：**别让「哪个说了算」不可判定**）；
无须另立条目。

## 结论

**PASS。** EC-02 成立：设计的**内容**真正决定实验 —— `design_source="plan"` 时臂从
**本 run 的计划产物**读出（执行期解析），两条来源并存 / 未认得的来源 / 计划不可读
**三条都点名拒绝**（**不**静默回落），未声明来源时既有语义**逐字不变**（且不读计划）。

三条承重件（来源互斥 / 未知来源 / 计划真读）各被按压一次、都咬住且逐字节复原。
