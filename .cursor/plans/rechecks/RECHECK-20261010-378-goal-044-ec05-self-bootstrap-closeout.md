---
id: RECHECK-20261010-378
slug: goal-044-ec05-self-bootstrap-closeout
title: 独立复检：GOAL-20261010-044 EC-05 自举收口（验证器 / 两树 / 归档 / 门链）
plan_id: PLAN-20261010-377
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
---

# RECHECK-20261010-378 — GOAL-20261010-044 EC-05 自举收口 独立复检

复检对象：`PLAN-20261010-377`。独立重跑下列机械面，不引用 PLAN 结论当证据。
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

**判词集覆盖本 GOAL 的 EC（逐条）**：`ec02-*`（新种类在场 / 语义写进域 / 域判据同轮钉住）/
`ec03-*`（等待模块公开面 / `AWAITING_HUMAN` 集合 / **四态全点名** / **只读**审批面 /
驱动按状态分派 / 组合根传既有实例）/ `ec04-*`（判据在树 / **两向**断言 / `WAIT` 面**逐字**被钉 /
`cited_facts` 点名审批 id）。

**两条「受判面非空」的写法**：`NAMED_FORMS` 逐条点名四态关键词；`ec03-the-approval-querier-is-read-only`
同时要求 `list_for_run` **在场**且 `replace(` / `register(` **不在场** ⇒ 判「只读」而不是判「有个函数」。

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
- **W-2（等待的处置不在本 GOAL）**：判定面**只到「可判定 + 点名」**；**不**做催办 / 升级 /
  超时取消（`V-1`）与 SLA（`V-3`）；**不**接通 D 组审批通道本身。
- **W-3（跨程序等待传播未做）**：等待按**程序**划界（`V-2`）。
- **W-4（承继残余原样保持）**：GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；
  GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；
  GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；`R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
