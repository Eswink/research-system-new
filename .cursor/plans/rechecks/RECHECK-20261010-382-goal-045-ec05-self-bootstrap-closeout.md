---
id: RECHECK-20261010-382
slug: goal-045-ec05-self-bootstrap-closeout
title: 独立复检：GOAL-20261010-045 EC-05 自举收口（验证器 / 两树 / 归档 / 门链）
plan_id: PLAN-20261010-381
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
---

# RECHECK-20261010-382 — GOAL-20261010-045 EC-05 自举收口 独立复检

复检对象：`PLAN-20261010-381`。独立重跑下列机械面，不引用 PLAN 结论当证据。
**`verify_paths` 声明：2 路**（本树 + `--base-ref` 的干净 checkout，同一份断言集）。

## 检查结果

### 1. 收口面进树与四道门（AC-1，独立重跑）

| 检查 | 读数 |
| --- | --- |
| 两个脚本在树 | `tools/verify_goal044_closeout.py` / `tools/goal044_closeout_assertions.py` |
| `ruff format --check` / `ruff check` | 全绿（2 files already formatted / All checks passed） |
| `mypy`（strict） | Success: no issues found in 2 source files |
| 规模门 | 文件 ≤ 450 行、函数 ≤ 50 行（全绿） |
| `IN_SCOPE` 纯收紧 | `+2` 行（只增不删）；判据 **8 passed** |

**判词集覆盖本 GOAL 的 EC（逐条）**：`ec02-*`（提案可声明两字段 / **三适配器各自** `commit` 都带上（逐条点名）/ 可选且缺省不变）/
`ec03-*`（读面逐条披露 / 点名冲突 / `[]` 分支返回空串 / 理由带标注）/ `ec04-*`（判据在树 /
SQLite 往返被断言 / 冲突**点名** / 未声明**不得**出现「冲突」/ PG 硬编码**不在树**）。

**两条「受判面非空」的写法**：`EC-02` 按 **三个适配器逐个**点名（`ec02-<adapter>-commit-carries-both`）
——**一个漏就红**（这正是本轮实测到的形态）；`ec04-the-pg-hardcoding-is-gone` 判**旧字面量不在树**
（而不是判「有个新写法」）。

### 2. 两树复检与归档（AC-2，独立重跑）

**首轮（bootstrap 时序）**：两份归档 missing（归档由本次调用写出、尚在提交之前）⇒
`TWO-TREE RED`；**两路已 `identical`**（证明差异**只**在归档项）。**次轮**（`--base-ref` 含归档的提交）：
终局行 `TWO-TREE PASS`；两路判词数相同、`sha256` 相同；归档两份、非空、`CR=0`（二进制写盘）。

### 3. 记录面与治理（AC-3，独立重跑）

`validate.py` 通过；`test_mainline_program_is_intact.py` 绿；本 GOAL 的 id 已在程序表**序 12**。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-5 逐条独立成立：收口面进树且过四道门、
两树 `TWO-TREE PASS`、归档定格、治理与宪章判据绿、CI 台账逐提交。

### Warnings

- **W-1（两树首轮红为时序）**：首轮 `TWO-TREE RED` 是 bootstrap 时序（归档在提交之后才存在）
  —— 如实登记，**不得**读成「判据曾被放宽」。
- **W-2（冲突的自动处置不在本 GOAL）**：本轮只到「可声明 / 可落库 / 可点名」；**不**自动挑一方 /
  删除 / 降权（`W-1`）；**不**做冲突**检测**算法（`W-2`）；`supersedes` 的判定面**不动**（`W-3`）。
- **W-4（承继残余原样保持）**：GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；
  GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；
  GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；`R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
