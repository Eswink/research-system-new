---
id: RECHECK-20261018-531
slug: goal-088-ec05-self-bootstrap-closeout
title: GOAL-088 EC-05 自举收口 —— 验证器本树 + 两树同结论 + 阶梯记账
status: COMPLETED
result: PASS
created_at: 2026-10-18
updated_at: 2026-10-18
plan_id: PLAN-20261018-529
parent_goal: GOAL-20261018-088
owners:
  - root-agent
verify_paths:
  - tools/verify_goal088_closeout.py
  - tools/goal088_closeout_assertions.py
memory_entries: []
---

# RECHECK-20261018-531 — GOAL-088 EC-05

## 检查结果

### 1. 自举：验证器进树且**加载自己那份**断言集

- `tools/verify_goal088_closeout.py` + `tools/goal088_closeout_assertions.py` 在树；
  `self-loads-its-own-assertions` 按**本文件名**推应载文件名 ⇒ 自洽；
- 两处注册表显式登记（`_VERIFIERS` 与 `IN_SCOPE`；后者仍卡在 **450 行**硬上限 ⇒
  同轮压缩 docstring 腾出空间，**未删任何条目**）。

### 2. 本树判词

- `tools/verify_goal088_closeout.py --root . --verdict-only` ⇒ **68 条全绿**。
- 覆盖：读取器九面（入口 / 性质过滤 / run 过滤 / `tool-result:` 前缀 / 缺性质点名 /
  两份设计拒绝 / 缺设计块点名 / 白名单 / **来源可归因**）、声明面六面
  （第二来源常量 / 词表 / 分派 / 缺 ledger 点名 / **`plan` 分支逐字仍在** / 与 `arms` 互斥）、
  共享解析器四面（公开入口 / `plan` 用它 / 私有别名 / 检索读取器 import 它）、
  8 条成对用例 + 例数下界 + 3 份既有判据仍在树。

### 3. 一处**如实登记**的清单修正（不是放宽）

- 验证器从模板继承的 `RESIDUAL_MARKERS` 含 `W-6`，而本 GOAL 的残余**恰为 W-1…W-5**
  （逐条在正文明写）⇒ 首轮判红 `residuals-enumerated -> W-6`。
- **处置**：把清单收窄到**本轮实际登记**的五条，并在注释里写明理由。**这不是放宽**：
  少了任何一条仍然判红（判据形态未变，只是清单与文档对齐）。改后 **68 条全绿**。

### 4. 两树复检

- `TREE current` 与 `TREE clean` 各 **68 条判词**，`sha256` **完全相同**
  （`d398d6947cd1eff3…`）；`COMPARE identical=True` / `TWO-TREE PASS`。
- **首跑真红并已修**：收口轮首次 as-is m0 判红 `python/tests` ——
  `tests/application/test_experiment_design_from_retrieval.py` 的 `_seed_retrieval` **52 行**
  （超 50 行门），而定向套件当时是绿的（我只跑了业务判据，没跑规模门）。处置：
  把证据登记拆成 `_register`（**无逻辑删除**、无判据改动）；修后 m0 **23/23**。
- 判词归档：`.cursor/plans/goals/evidence/GOAL-20261018-088-ec05-{current,clean}.txt`
  —— 二进制写盘、`CR=0`、逐字节相同。

### 5. 阶梯记账（两个面）

- 阶梯 **实验** 行：`依据 GOAL` 收录 `GOAL-20261018-088`；`下一级` 更新为
  「参数与臂可由**计划内容**派生…，也可由**本 run 的系统取得证据**派生且性质不可伪造；
  『真实 provider 的返回里带设计块』仍属 live 观察」—— **下一格仍是 live 观察**，
  如实写明（本 GOAL 补的是「来源可以是系统取回的」，不是「真实 provider 一定带设计」）。
- 宪章 `进展记录` 追加本 GOAL 一行（`RECHECK` 列指向 `RECHECK-20261018-530`）。
- 程序表新增**序 56**（轴 `质量`、能力域 `实验`）⇒ 预算 `max_goals: 60`，已用 **56**。

### 6. 静态门与全量门

| 面 | 读数 |
| --- | --- |
| 新工具 `ruff` / `format` / `mypy` | 全绿（2 份文件） |
| 两处注册表判据 | **17 passed** |
| 宪章三条判据 | **20 passed** |
| 新判据 / 既有实验判据 | **10 passed** / **40 passed** |
| 治理校验 | `Cursor 治理验证通过` |
| 凭据审计 | 四面 `offenders=0` |
| as-is m0 | **23/23**（终态 `PASS: profile=m0; 23 deterministic checks`） |

## 结论

**PASS**。验证器 68 条本树全绿、两树逐行相同且 `sha256` 一致、阶梯两个面都收录本 GOAL、
新判据与既有实验判据同时全绿 ⇒ EC-01…EC-05 全部达成，本 GOAL 收口。

**射程边界（重申，不夸大）**：本 GOAL **不声称**「真实检索 provider 的返回里一定带设计块」——
它证明的是「**设计可以从系统真的取回了什么里读出，且性质不可伪造**」这条链路成立。
