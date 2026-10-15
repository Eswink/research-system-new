---
id: RECHECK-20261015-478
slug: goal-079-ec01-experiment-parameters-come-from-the-declaration
title: GOAL-079 cycle 1 复检 — 实验参数由声明给出（EC-01）
status: COMPLETED
result: PASS
created_at: 2026-10-15
updated_at: 2026-10-15
plan_id: PLAN-20261015-477
parent_goal: GOAL-20261015-079
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261015-478 — GOAL-079 cycle 1

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | 参数面在树且**白名单真的生效** | **PASS** | `plan_parameters.parameter_environment`：白名单内逐键变带前缀环境项；白名单外（`PATH` / `secret`）**点名拒绝**（`UndeclaredExperimentParameterError`，判词含该键与白名单）；`None` 值也**点名**（「空值」≠「没声明」） |
| AC-2 | **声明即传递**（装配 → 请求） | **PASS** | 用**真装配件**（`SandboxExperimentAssembly` + `_request_builder`）构造执行请求：`seed=11` ⇒ 环境里 `EXPERIMENT_PARAM_SEED == "11"`；`n_items=100` ⇒ `"100"`；执行器自己的 `EXPERIMENT_RUN_ID` 仍在 |
| AC-3 | **缺省零回归** | **PASS** | 未声明 ⇒ 请求环境**恰为** `{EXPERIMENT_RUN_ID}`（判据断言集合相等）；脚本侧缺省跑出 `seed=7` / `n_items=800` / `duplicates_expected=40`（与改动前逐字相同） |
| AC-4 | **脚本读得到**（真跑） | **PASS** | 子进程真跑脚本：`EXPERIMENT_PARAM_SEED=11` / `N_ITEMS=120` / `DUPLICATE_PAIRS=6` ⇒ `metrics` 逐项为 `11` / `120` / `6`，且 `duplicates_found=6`、`agreement=True` |
| AC-5 | 脚本侧 **fail-closed** | **PASS** | 非法值（`EXPERIMENT_PARAM_SEED=not-a-number`）⇒ 退出码非 0、stderr **点名**该变量且含 `must be an integer`（**不静默回落**） |
| AC-6 | 前缀命名空间不相交 | **PASS** | `EXPERIMENT_RUN_ID` 不以参数前缀开头；参数面产出的环境里**没有**该键（判据显式断言） |
| AC-7 | **三向按压全红** | **PASS** | `.cursor/plans/goals/evidence/GOAL-20261015-079-press-two-way.txt`（673 字节、`CR=0`）：`V9-1`（白名单恒真假）/ `V9-2`（声明不进请求）/ `V9-3`（脚本不读声明）各 `BASELINE GREEN=True / 按压 RED=True / sha 复原一致=True`，`all_red_and_restored=True` |
| AC-8 | 既有判据零放宽 | **PASS** | 既有实验链判据（`test_ec02_experiment_chain_offline` / `test_sandbox_experiment_seam` / `test_experiment_task`）未改；本 cycle 只**新增**一个判据模块 |
| AC-9 | 规模门 | **PASS** | 新增/改动文件逐个 ≤ 450 行、无超 50 行函数（`plan_parameters.py` 84 行；`experiment_support.py` 232 行；脚本 153 行；判据模块 ~200 行） |

## 警告（如实登记）

- **`W-1`**：**EC-02 / EC-03 / EC-04 / EC-05 仍未完成** —— 本 cycle 只做 **EC-01**（参数面）。
  「多臂/对照」「臂间可比」「真实中转站」「自举收口」属后续 cycle。
- **`W-2`**：参数**只支持整数**（脚本侧 `_declared_int`）。现有三个参数（seed / n_items /
  duplicate_pairs）都是整数 ⇒ 不假装通用；字符串/浮点参数属后续（`ALLOWED_PARAMETERS`
  里加键时同轮加类型读取）。
- **`W-3`**：**声明点仍是装配面**，不是**计划**（`ExperimentPlan` 仍无参数位）——
  本 cycle 证的是「参数由**声明**给出」这条**传递面**；「计划携带参数」是 EC-02 的靶子
  （多臂需要「哪个臂用哪组参数」的声明位）。**不得**把本 cycle 读成「计划驱动实验已完成」。
- **`W-4`**：`parameters` 经环境进容器 ⇒ 容器里**看得见**这些值（对沙箱内的被测代码而言
  是**可读输入**，这是本设计的目的）；参数里**不得**放凭据（本 GOAL 的 `forbidden` 面）。
- **`W-5`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。

## 未覆盖的面

- 多臂/对照（EC-02）；
- 臂间可比（EC-03）；
- 真实中转站（EC-04）；
- 自举收口（EC-05）；
- 参数的类型系统（`W-2`）与「计划携带参数」（`W-3`）。

## 无可复用事实需要另建工程记忆（本轮教训已并进既有条目）

本轮的可复用面是 `MEM-20261015-222` 的**新条目**（参数面：声明点选在**装配面**而非契约、
白名单而非转发、缺省回落而非法点名、前缀命名空间不相交）—— 它讲的是**一类**问题
（「把写死的量变成声明量」时的四个决定点），所以另立条目而非并进既有。

## 结论

**PASS。** EC-01 成立：实验参数从「脚本里的模块常量」变成**声明事实** ——
装配声明经「执行请求 → 容器环境」到达脚本（**逐键**、**白名单**、**前缀命名空间不相交**），
**未声明时零回归**（请求环境与脚本产出都与改动前逐字相同），**值非法时点名失败**
（不静默回落）。三向按压全红且逐字节复原。**本 cycle 只做参数面**；
「多臂/对照」与「计划携带参数」是下一个 cycle 的事，如实登记为 `W-3`。
