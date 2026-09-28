---
id: RECHECK-20260928-236
slug: goal-024-ec04-closeout-two-tree
title: GOAL-024 EC-04 收口复检：收口验证器进树并入必备清单 + 两树逐行判词与 sha256 一致 + 终态与残余登记在位
plan_id: PLAN-20260928-235
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-28
completed_at: 2026-09-28
owners:
  - root-agent
---

# RECHECK-20260928-236 — GOAL-024 收口复检

**复检口径**：不收口验证器自己的叙述；本文件给出**可复核观察面**（命令 / 判词行 / `sha256`）。
**未实跑的不记通过**；警告逐条留位。

## 检查结果

### 1. 收口验证器进树且只写自己特有的断言（AC-1）
- `tools/verify_goal024_closeout.py`：**431 行**、最长函数 **44 行**，`ruff format --check` /
  `ruff check` = `All checks passed!`、`mypy` = `Success: no issues found`。
- 公共面**零重写**：脚本 `load_module` 后直接调用 `tools/closeout_recheck_assertions.py` 的
  `Verdict` / `emit` / `standard_verdicts`（`STANDARD` 常量指向它）；本文件只写 GOAL-024
  特有断言（EC-01…EC-04 四组）。
- 自跑：**36 PASS / 0 FAIL**（本文件定稿前如实判红 2 条 —— `latest_recheck` 为 null 与两条
  残余短语缺位 —— 补齐记录后转绿；**不是**放宽断言，是记录补齐）。

### 2. 必备清单纯收紧（AC-2）
- `IN_SCOPE` 由 3 条增到 **4 条**（加入本验证器）；`git diff` 为**一行新增**。
- 该判据实跑：`tests/tooling/test_tooling_scripts_meet_product_gates.py` **8 passed**
  （含格式 / 规模 / `mypy` / 射程分区四条），以及 `test_closeout_assertions_are_in_tree.py`
  同批全绿 —— 即**新脚本真的被四道门管住**，而非只是登记。

### 3. 两树一致（AC-3）
- 入口：`tools/two_tree_recheck.py --script-mode shared`（与 GOAL-022/023 同机器）。
- 两棵树各 **38** 条判词、逐行相同，`sha256` **均为** `cab69defa74a70a39d273ca082323e9d8100403e58edc380ec56fcc67d5fed00`，`COMPARE identical=True`、
  `TWO-TREE PASS`（日志 `scratch/goal024-c5-two-tree.log`）；**记录写入后复跑同值**
  （`scratch/goal024-c5-two-tree-rerun.log`）。
- `verify_paths ≥ 2` 路声明在位（当前树 + 干净 checkout）。

### 4. 终态与登记（AC-4）
- EC 状态：EC-01 / EC-02 / EC-03 / EC-04 **全 `PASS`**（收口验证器 `ec04-ec01-to-ec03-are-pass`
  与 `ec04-final-ec-is-pending-or-pass` 两条判词实跑通过；后者接受「`PASS` 或**未定稿态**」是**时序**
  口径 —— 本文件就是 EC-04 的判词产出者）。
- `latest_recheck` 指向本文件（仓库相对路径，可解析）；`child_plans` 5 条、`memory_entries` 2 条
  全部存在。
- 残余：承继 12 条（`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `W-4` / `W-5` / `W-6` /
  `W-10` / `W-11` / `W-12`）+ 本轮新增 6 条（`G24-1`…`G24-6`）逐条在位；未覆盖范围五条
  （读面未认证 / 多租户 / BOLA·BFLA / 部署面未验证 / `R-M1`）逐条在位。
- as-is 本机 m0（记录之后）= `PASS: profile=m0; 23 deterministic checks`（24 个 `PASS [`、
  4715 passed / 21 skipped、`EXIT=0`；日志 `scratch/goal024-c5-m0.log`；记录提交 `c493570`
  `22:56:44` → m0 日志 `23:08:51` ⇒ 门在记录之后）。

## 结论

**PASS_WITH_WARNINGS**。EC-04 的四条验收成立：验证器进树、必备清单纯收紧且四道门实跑、
两树结论逐行一致、终态与残余登记在位。**GOAL-024 收口条件达成（EC-01…EC-04 全 PASS）**。

**警告（逐条留位）**：

- `W-1` **两树同结论 ≠ 跨平台同结论**：两树都在本机 win32 跑（判据本身不依赖平台，
  但本轮**没有**在 Linux 上复跑；CI 的 ubuntu job 跑的是 m0 而不是本验证器）。
- `W-2` **收口验证器是"读树"判据**：它证明的是"记录与判据文件在位、清单未漂移"，
  **不**重新执行金丝雀取证（那些是 EC-01/EC-02 的判据面，CI 会跑）。
- `W-3` 承继残余与 `G24-1`…`G24-6` **原样保留**，本轮不消解任何一条。
- `R-M1` **仍未收口**：本次收口**不**构成任何项目安全结论。
