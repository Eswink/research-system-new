---
id: RECHECK-20261018-522
slug: goal-085-ec05-self-bootstrap-closeout
title: 复检 — GOAL-085 EC-05：自举收口（两树同结论 + m0 23/23 + 记录面自洽）
status: COMPLETED
result: PASS
created_at: 2026-10-18
updated_at: 2026-10-18
plan_id: PLAN-20261018-520
parent_goal: GOAL-20261018-085
reviewer: root-agent
owners:
  - root-agent
verify_paths:
  - 本树判词（`tools/verify_goal085_closeout.py --root . --verdict-only`）
  - 干净 checkout 判词（同一脚本、同一解释器、`tree` 模式）
  - as-is 全量 m0（静止工作树，终态行）
memory_entries: []
---

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| EC-05a | **验证器进树且自举** | **PASS** | `tools/verify_goal085_closeout.py` + `tools/goal085_closeout_assertions.py`；`self-loads-its-own-assertions` 按**本文件名**推出应载的那份并断言源码引用一致 |
| EC-05b | **本树判词全绿** | **PASS** | `--root . --verdict-only` ⇒ **67 条 `PASS`、0 条 `FAIL`**（`EXIT=0`） |
| EC-05c | **两树同结论** | **PASS** | `tree` 模式（脚本按各自树根解析 ⇒ 同时证明干净树**真的有**这些文件）；`COMPARE identical=True` / `TWO-TREE PASS` |
| EC-05d | **as-is m0** | **PASS** | 静止工作树、记录写完之后：**`PASS: profile=m0; 23 deterministic checks`** |
| EC-05e | **治理** | **PASS** | `validate.py` ⇒ `Cursor 治理验证通过` |
| EC-05f | **凭据四面** | **PASS** | `tools/credential_audit.py` ⇒ 四面 `offenders=0` |
| EC-05g | **阶梯记账（两个面）** | **PASS** | 宪章「复检」域的 `依据 GOAL` 收录本 GOAL；「进展记录」有本 GOAL 一行且 `RECHECK` 列指向 `RECHECK-20261018-521`（`ladder-*` / `progress-*` 判词钉住） |
| EC-05h | **CI 台账逐提交** | **PASS** | `941752a1` 八 job 全 `success` + 三条 CodeQL `success`，`run_attempt=1`、零 `cancelled`、零 rerun |

## 判词面（本轮特有的断言）

`tools/goal085_closeout_assertions.py` 的断言分三组：

- **EC-01 归因**（11 条）：域字段 / 门签名 / 运行链调用点**真的传了** / 归因取自
  `endpoint.id` 与 `model.model_name` / **拒拼半个目标** / 落库链搬运 / 读面暴露 /
  sqlite 列 / postgres 列 / 迁移 `028`；
- **EC-02/EC-03 聚合与独立性**（7 条）：`aggregate_panel` 入口 / **单评审早退** /
  **不夺真相权**（模块内无 `Decision(` / `decided_by`）/ 目标形态 / **同目标点名词** /
  读面 `panels` / 分组键 `(task_id, contract_id)`；
- **成对用例与例数下界**（6 + 3 条）：异目标 / 同目标 / 按压翻转 / 单评审不聚合 /
  读面单评审无 panel / 不跨任务混票；三份判据文件的例数下界 **10 / 13 / 6**。

## 两树复检的形态（逐条）

| 项 | 读数 |
| --- | --- |
| 解释器 | 两侧都是**主树 `.venv`** |
| 模式 | **`tree`（缺省）** —— 脚本按**各自树根**解析；先建**持久化 worktree** 逐条确认两棵树都含 `tools/verify_goal085_closeout.py` 与 `packages/application/evaluation/panel_verdict.py`（同一 HEAD）再跑 |
| 判词数 | 两侧 **67 / 67** |
| 结论 | `COMPARE identical=True` / `TWO-TREE PASS` |
| 归档 | `.cursor/plans/goals/evidence/GOAL-20261018-085-ec05-current.txt` / `…-clean.txt`（二进制写盘、CR=0） |

**首轮两树是 RED，且那次红是真的**：当时 `latest_recheck` 已指向 `RECHECK-20261018-522`，
而该文件**还没写** ⇒ `records-declare-existing-rechecks` 两树**同时**判负
（`TWO-TREE RED`，两棵树的退出码都是 1）。补写本文件后重跑才转绿 —— **不是**放宽判据、
**不是** rerun 掩蔽。

## 警告（如实登记）

- **`W-1`**：EC-05 的判词就在本文件产出的那一轮里 —— 时序上 GOAL 的 EC-05 在本复检**之前**
  是待办，所以验证器接受「达成 ∪ 待办」两种取值。**这是时序，不是放宽**。
- **`W-2`**：多数票不等于「对」；本 GOAL 判**可归因与可聚合**，不判「哪一票更对」。
- **`W-3`**：只判模型**身份是否相同**，不判两个模型是否**同质化**。
- **`W-5`**：两个评审实例的 `task_id` 必须相同才会被聚成一票 ⇒ 「跨任务的评审小组」不在射程。
- **`W-6`**：`panels` 里没有「哪一票来自哪个 phase」这一格。
- **`R-M1` 未收口** ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」（**明确否认**）。

## 未覆盖的面

- **读面认证**、**多租户·RBAC·BOLA·BFLA**、**部署面验证**、**D 组审批通道** —— 均未做；
- 默认 runtime 仍是 Fake（§11）；
- 「两个不同模型在**同一个上游产物**上给出**不同判词**」是阶梯的**下一级**，不在本 GOAL 射程。

## 结论

**PASS**。EC-01…EC-05 全部达成：本树 **67 条判词全绿**、两树判词逐行相同、
as-is m0 **23/23**、治理通过、凭据四面 `offenders=0`、CI 八 job 全绿。
首轮两树 RED（`latest_recheck` 指向尚未写入的文件）已如实登记并补写后转绿。
