---
id: RECHECK-20261010-372
slug: goal-043-ec05-self-bootstrap-closeout
title: 独立复检：GOAL-20261010-043 EC-05 自举收口（验证器 / 两树 / 归档 / 门链）
plan_id: PLAN-20261010-371
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
---

# RECHECK-20261010-372 — GOAL-20261010-043 EC-05 自举收口 独立复检

复检对象：`PLAN-20261010-371`。独立重跑下列机械面，不引用 PLAN 结论当证据。
**`verify_paths` 声明：2 路**（本树 + `--base-ref` 的干净 checkout，同一份断言集）。

## 检查结果

### 1. 收口面进树与四道门（AC-1，独立重跑）

| 检查 | 读数 |
| --- | --- |
| 两个脚本在树 | `tools/verify_goal043_closeout.py` / `tools/goal043_closeout_assertions.py` |
| `ruff format --check` / `ruff check` | 全绿（2 files already formatted / All checks passed） |
| `mypy`（strict） | Success: no issues found in 2 source files |
| 规模门 | 文件 ≤ 450 行、函数 ≤ 50 行（全绿） |
| `IN_SCOPE` 纯收紧 | `+2` 行（只增不删）；判据 **8 passed** |

**判词集覆盖本 GOAL 的 EC（逐条）**：`ec02-loads-its-own-assertions-{038,039,040}`（加载面三处）/
`ec03-structure-criterion-is-in-tree` 与 `ec03-no-text-anchor-on-the-changed-signature`（崩溃面）/
`ec04-*`（机器判据三条主 **函数名** 逐条 + 两向反例在位）。

### 2. 判据自查（本轮的两处**自纠**，如实登记）

- **`ec03-no-text-anchor-on-the-changed-signature` 第一版假红**：子串搜索把
  `goal040_closeout_assertions.py` docstring 里**引述**的旧锚点当成缺陷 ⇒ 改 **AST**
  且**排除 docstring**（`_string_constants_outside_docstrings`）⇒ 转绿。
  **判散文与判调用是两件事**（与 GOAL-20261009-042 的同一课）。
- **`RESIDUAL_MARKERS` 第一版假红**：`U-2` / `T-2` 逐条匹配与 GOAL 原文的**区间写法**
  （`U-1`…`U-3`）打架 ⇒ 改取**首尾锚点**（`U-1`/`U-3`、`T-1`/`T-3`）并在判据里写明理由。

### 3. 两树复检与归档（AC-2，独立重跑）

**首轮（bootstrap 时序）**：`records-declare-existing-rechecks`（本 PLAN 的 `latest_recheck`
指向尚不存在的 RECHECK）+ 两份归档 missing ⇒ `TWO-TREE RED`。**这是 bootstrap 时序**
（记录与归档在提交之后才存在），如实登记，**不**读成「判据缺口」。

**次轮**（`--base-ref` 含归档的提交）：终局行 `TWO-TREE PASS`；两路判词数相同、
`sha256` 相同；归档两份、非空、`CR=0`（二进制写盘）。

### 4. 记录面与治理（AC-3，独立重跑）

`validate.py` 通过；`test_mainline_program_is_intact.py` 绿；本 GOAL 的 id 已在程序表**序 11**。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-5 逐条独立成立：收口面进树且过四道门、
两树 `TWO-TREE PASS`、归档定格、治理与宪章判据绿、CI 台账逐提交。

### Warnings

- **W-1（两树首轮红为时序）**：首轮 `TWO-TREE RED` 是 bootstrap 时序 —— 如实登记，
  **不得**读成「判据曾被放宽」。
- **W-2（`U-1`：不重跑历史收口复检）**：本轮让**今天**的加载面与可执行性正确并钉住形态；
  **不**重建 GOAL-038/039/040 当时的树状态重跑其收口复检，且**不**改写历史结论
  ⇒ 「**当时**那几轮里其自有断言确实没跑」这一事实登记在 `RECHECK-20261010-370` 的 `W-2`。
- **W-3（`U-2`：文本锚点未普查）**：本轮的判据只钉「加载对 / 跑得动」；**不**禁止断言集内部
  的文本锚点 ⇒ 其它历史断言集的同类脆弱性**未普查**。
- **W-4（`U-3`：`tools/` 射程外旧脚本仍无机器门）**：`ruff check tools tests` 仍有 **74** 条
  历史遗留（与既有「73 条」登记同源；本轮**未触碰**、**未新增**）。
- **W-5（承继残余原样保持）**：GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；
  GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；
  GOAL-037 的 `O-1`…`O-5`；`R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
