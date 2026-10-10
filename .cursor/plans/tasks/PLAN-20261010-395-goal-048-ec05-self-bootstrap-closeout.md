---
id: PLAN-20261010-395
slug: goal-048-ec05-self-bootstrap-closeout
title: GOAL-20261010-048 cycle 2（EC-05）：自举收口 —— 验证器进树 + 两树 + 归档 + 门链 + 台账
status: DONE
created_at: 2026-10-10
updated_at: 2026-10-10
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-396-goal-048-ec05-self-bootstrap-closeout.md
memory_entries: []
parent_goal: GOAL-20261010-048
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261010-048 的 **EC-05**（自举收口）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：复用既有收口机器（`tools/closeout_recheck_tools`
    + `tools/closeout_recheck_assertions.standard_verdicts`，**一行未重写**）；
    两处射程**纯收紧**（只增不删）；判词归档**二进制写盘 / `CR=0`**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 GOAL-20261010-048 收口：① 收口验证器 + 本轮断言集进树并加入 `IN_SCOPE`（纯收紧）
    **与** GOAL-043 立的射程清单；② **两树复检**（`--script-mode shared` + `--base-ref`）
    ⇒ `TWO-TREE PASS` + 判词归档进树；③ as-is m0 **23/23**（在**全部记录写入之后**）、
    治理绿、宪章判据绿；④ CI 台账逐提交；⑤ 承继残余与未覆盖范围逐条在位。
exit_criteria:
  - id: AC-1
    criterion: >-
      **收口面进树**：两个脚本在树且过**四道门**（含规模门）；`IN_SCOPE` **纯收紧**（+2 行）；
      射程分区清单**同步登记**（+1 行）；判词集**逐条**覆盖本 GOAL 的 EC
      （声明面 / 求值面 / 两向四条按压）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_tooling_scripts_meet_product_gates.py
      tests/tooling/test_closeout_verifiers_run_their_own_assertions.py -q` ⇒ 全绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **两树复检**：`tools/two_tree_recheck.py --script tools/verify_goal048_closeout.py
      --script-mode shared --base-ref HEAD` ⇒ **`TWO-TREE PASS`**；判词归档**进树**
      （两份、`CR=0`、与最终一轮同结论）。
    verify: >-
      终局行 `TWO-TREE PASS`；
      `.cursor/plans/goals/evidence/GOAL-20261010-048-verdict-{current,clean}.txt`。
    status: PASS
  - id: AC-3
    criterion: >-
      **记录面自洽**：本 PLAN + `RECHECK-20261010-396` 在位；GOAL 的 EC / 迭代日志 /
      状态历史 / `latest_recheck` / `child_plans` 回写；`ALL_PLAN` 投影一致；
      治理 `validate.py` 绿 + 宪章判据绿。
    verify: >-
      `uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py`
      ⇒ 通过；`tests/tooling/test_mainline_program_is_intact.py` 绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **as-is m0 23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）。
    verify: >-
      终局行 `PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 / `FAILED [` 0）。
    status: PASS
  - id: AC-5
    criterion: >-
      **CI 台账逐提交**（`cancelled` / `failure` 如实登记 + 原因 + `covered_by`；
      空集合 = 未取证；自我指涉边界明写并封闭）。
    verify: >-
      `scratch/poll_ci_all.sh <sha>` 遍历该 sha 全部 run + `/jobs`；台账表见 GOAL 正文。
    status: PASS
---

# PLAN-20261010-395 — GOAL-20261010-048 cycle 2（EC-05 自举收口）

> **主线归属**：`GOAL-20261010-048`（MAINLINE 程序表**序 16**）的 **EC-05**。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 收口面进树 + 四道门 + 两处射程纯收紧 | PASS |
| AC-2 | 两树 `TWO-TREE PASS` + 判词归档进树 | PASS |
| AC-3 | 记录面自洽 + 治理 + 宪章判据绿 | PASS |
| AC-4 | as-is m0 **23/23**（记录写完之后） | PASS |
| AC-5 | CI 台账逐提交 | PASS |

## 实施清单

- [x] WP-1 验证器 + 断言集进树
- [x] WP-2 两处射程纯收紧（`IN_SCOPE` +2 行 / 射程清单 +1 行、下界 17→18）
- [x] WP-3 两树复检（bootstrap 轮 + 终态轮）
- [x] WP-4 判词归档进树（两份 / 二进制写盘 / `CR=0`）
- [x] WP-5 记录面：本 PLAN + `RECHECK-20261010-396` + GOAL 回写 + `ALL_PLAN` + MAINLINE 进展行
- [x] WP-6 治理 + 宪章判据 + as-is m0 + CI 台账

## 证据

| 门 | 读数 |
| --- | --- |
| 收口验证器（本树） | **75 判词 / 0 FAIL** |
| 两树复检 | **`TWO-TREE PASS`**（两路 **75 判词** / `sha256` 相同 `e6ead21f2ba7a89e…`）|
| 判词归档 | 两份各 **2831 B / 75 行 / `CR=0` / 0 FAIL**（二进制写盘）|
| 按压归档 | **455 B / `CR=0`**（`J-1`…`J-4` 全 `RED` + 复原一致）|
| 两处射程 | `IN_SCOPE` **+2 行**；射程分区清单 **+1 行**（下界 17→18）—— 均**纯收紧** |
| 治理 | `validate.py` 通过 |
| 宪章判据 | `test_mainline_program_is_intact.py` 绿 |
| **as-is m0** | `PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 / `FAILED [` 0 / **5585 passed, 21 skipped**；在全部记录写完之后、独占、仓库 `.venv`、不接管道）|

### 本轮实测到的**判据自身缺陷两处**（如实登记，均在本轮修好）

1. **文本计数把定义行算成调用**：`ec03-the-verdicts-are-read-once-for-both-faces` 初版用
   `runner.count("_verdicts(")` —— 而 `def _verdicts(` 那行**也**被算成一次 ⇒
   「只读一次」判成「读了两次」而**假红**（实测）。改用 **AST 调用计数**（`_count_calls`）。
   **与 `MEM-20261010-215` 同族**：判关系要用 AST 读，不用文本巧合。
2. **结论面坐标取错**（承 cycle 1）：`goal040` / `goal046` 各有一条拿 `_verdicts` 的**读取行**
   当「结论面」坐标；判词改成「读一次供两处共用」后读取行**正当**前移 ⇒ **假红**。
   两条改判**分派点**（`_after_hit`），断言仍是同一件事。

**这类缺陷的性质**：都是**判据**的问题（不是产品缺陷、不是放宽）——
GOAL-043 立的「零判负」判据把第 2 类**当场报了出来**，第 1 类由本轮的收口验证器自己在
**首跑**时报了出来。**登记为**「判据按位置 / 文本写死的既有代价」。

## 影响报告

- **Domain / API / schema 变化**：零（本轮只新增 `tools/` 机械面与记录）。
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：无。**上游版本影响**：无。
- **下一项任务**：GOAL 收口。

## 无可复用事实

本 cycle 只新增 `tools/` 下的机械面与记录；其两处可复用教训（**文本计数 ≠ 调用计数**、
**坐标要取「谁先决定」而不是某条语句的行号**）已由 `MEM-20261010-215` 的同族条目承载
（本轮是它的**第二次与第三次兑现**），**未**沉淀新条目。

## CI 台账（逐提交）

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `24c5ccf` / `b829338` / `430a63f`（EC-05 首轮 + 两轮归档） | 见 GOAL 正文台账 | 验证器 + 两处射程 + 归档定格 |
| （收口提交） | 见 GOAL 正文台账 | 本 PLAN + RECHECK + GOAL 回写 + 宪章进展行 |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | IN_PROGRESS | 验证器 + 断言集进树；两处射程纯收紧；bootstrap 轮时序登记。 |
| 2026-10-10 | DONE | 两树 `TWO-TREE PASS`；归档定格；m0 23/23；`RECHECK-20261010-396` 独立复检。 |
