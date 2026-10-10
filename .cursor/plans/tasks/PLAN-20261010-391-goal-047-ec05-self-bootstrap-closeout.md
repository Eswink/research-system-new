---
id: PLAN-20261010-391
slug: goal-047-ec05-self-bootstrap-closeout
title: GOAL-20261010-047 cycle 2（EC-05）：自举收口 —— 验证器进树 + 两树 + 归档 + 门链 + 台账
status: DONE
created_at: 2026-10-10
updated_at: 2026-10-10
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-392-goal-047-ec05-self-bootstrap-closeout.md
memory_entries: []
parent_goal: GOAL-20261010-047
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261010-047 的 **EC-05**（自举收口）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：复用既有收口机器（`tools/closeout_recheck_tools`
    + `tools/closeout_recheck_assertions.standard_verdicts`，**一行未重写**）；
    两处射程**纯收紧**（只增不删）；判词归档**二进制写盘 / `CR=0`**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 GOAL-20261010-047 收口：① 收口验证器 + 本轮断言集进树并加入 `IN_SCOPE`（纯收紧）
    **与** GOAL-043 立的射程清单；② **两树复检**（`--script-mode shared` + `--base-ref`）
    ⇒ `TWO-TREE PASS` + 判词归档进树；③ as-is m0 **23/23**（在**全部记录写入之后**）、
    治理绿、宪章判据绿；④ CI 台账逐提交；⑤ 承继残余与未覆盖范围逐条在位。
exit_criteria:
  - id: AC-1
    criterion: >-
      **收口面进树**：两个脚本在树且过**四道门**（含规模门）；`IN_SCOPE` **纯收紧**（+2 行）；
      射程分区清单**同步登记**（+1 行）；判词集**逐条**覆盖本 GOAL 的 EC
      （注册面 / 接回面 / 两向五条按压 / 准入窄性）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_tooling_scripts_meet_product_gates.py
      tests/tooling/test_closeout_verifiers_run_their_own_assertions.py -q` ⇒ 全绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **两树复检**：`tools/two_tree_recheck.py --script tools/verify_goal047_closeout.py
      --script-mode shared --base-ref HEAD` ⇒ **`TWO-TREE PASS`**；判词归档**进树**
      （两份、`CR=0`、与最终一轮同结论）。
    verify: >-
      终局行 `TWO-TREE PASS`；
      `.cursor/plans/goals/evidence/GOAL-20261010-047-verdict-{current,clean}.txt`。
    status: PASS
  - id: AC-3
    criterion: >-
      **记录面自洽**：本 PLAN + `RECHECK-20261010-392` 在位；GOAL 的 EC / 迭代日志 /
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

# PLAN-20261010-391 — GOAL-20261010-047 cycle 2（EC-05 自举收口）

> **主线归属**：`GOAL-20261010-047`（MAINLINE 程序表**序 15**）的 **EC-05**。

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
- [x] WP-2 两处射程纯收紧（`IN_SCOPE` +2 行 / 射程清单 +1 行、下界 16→17）
- [x] WP-3 两树复检（bootstrap 轮 + 终态轮）
- [x] WP-4 判词归档进树（两份 / 二进制写盘 / `CR=0`）
- [x] WP-5 记录面：本 PLAN + `RECHECK-20261010-392` + GOAL 回写 + `ALL_PLAN` + MAINLINE 进展行
- [x] WP-6 治理 + 宪章判据 + as-is m0 + CI 台账

## 证据

| 门 | 读数 |
| --- | --- |
| 收口验证器（本树） | **70 判词 / 0 FAIL** |
| 两树复检 | **`TWO-TREE PASS`**（两路 **70 判词** / `sha256` 相同 `a2ba7fa00137c70a…`）|
| 判词归档 | 两份各 **2600 B / 70 行 / `CR=0` / 0 FAIL**（二进制写盘）|
| 按压归档 | **523 B / `CR=0`**（`H-1`…`H-5` 全 `RED` + 复原一致）|
| 两处射程 | `IN_SCOPE` **+2 行**；射程分区清单 **+1 行**（下界 16→17）—— 均**纯收紧** |
| 治理 | `validate.py` 通过 |
| 宪章判据 | `test_mainline_program_is_intact.py` 绿 |
| **as-is m0** | `PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 / `FAILED [` 0 / **5576 passed, 21 skipped**；在全部记录写完之后、独占、仓库 `.venv`、不接管道）|

### 本轮实测到的**两处真红**（如实登记）

1. **CI 在 `f4e8f34` 上判红**（`quality-ubuntu-latest` / `quality-windows-latest`）：逐字
   `test_every_named_assertion_set_reports_no_negative_on_this_tree` 报
   `["goal044_closeout_assertions.py: ['ec03-the-approval-querier-is-read-only']",
   "goal046_closeout_assertions.py: ['ec03-the-approval-face-is-read-only']"]`
   —— **成因**：我把**有副作用**的注册实现放进了序 12/14 的**只读判定面**
   （`program_waiting.py`），而那两个既有断言集各有一条把它钉成「不得出现写方法」。
   **处置**（`819f51f`）：按仓里 `phase_pause.py` 之于 `phase_runner.py` 的**同一手法**
   把注册单列成模块，只读判定面复原（实测 `register(` / `replace(` **各 0**）。
   **判据是对的、实现是错的** —— 这正是 GOAL-043 立那条判据的用途（第三次兑现）。
2. **规模门两处抽查**：`_evaluate` 曾到 **51 行**、`program_runner.py` 曾到 **453 行**
   ⇒ 搬迁 `claimed_but_missing` → `program_retry.py`、闸门求值 → `_declared_gate_evaluation`；
   现 runner **443 行**、函数全 ≤ 50。

**另一处如实登记（搬迁撞红既有判据，承 `MEM-20261010-215`）**：`goal046` 的
`_gate_precedes_conclusion_face` 原先钉 `declared_gate_verdict` 的**定义行**，搬迁后假红
⇒ 改为判**求值顺序**（认调用点，两种形态都认），断言仍是**同一件事**。

## 影响报告

- **Domain / API / schema 变化**：零（本轮只新增 `tools/` 机械面与记录）。
- **安全 / 凭据变化**：无（准入分支的窄性由 `tests/api/test_approvals_api.py` 成对断言钉住）。
- **兼容性 / 迁移风险**：无。**上游版本影响**：无。
- **下一项任务**：GOAL 收口。

## 无可复用事实

本 cycle 只新增 `tools/` 下的机械面与记录；其可复用事实已由 `MEM-20261010-216` 承载
（且本轮实测到它的**第二次兑现**：既有断言集把「只读面被塞进写方法」当场报出来）。

## CI 台账（逐提交）

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `ef4807c`（replan + 序 15 建档） | 见 GOAL 正文台账 | 序 15 新增 + 预算核算 15→20 |
| `189edc2` / `b3a569d` / `f4e8f34`（cycle 1） | `38046351732` **M0 failure**（**真红**，见上）⇒ 由 `819f51f` 修好；`38046351537` **CodeQL success** | 实现 / 判据 / 记录 |
| `491c063` / `dce124a`（EC-05 首轮 + 归档） | 见 GOAL 正文台账 | 验证器 + 两处射程 |
| `819f51f`（真红修复 + 搬迁 + 两处判据按关系修正） | 见 GOAL 正文台账 | 只读判定面复原 |
| `8a0ea91`（归档重定格 = 本批 HEAD） | 见 GOAL 正文台账 | 两树 70 判词 / `a2ba7fa0…` |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | IN_PROGRESS | 验证器 + 断言集进树；两处射程纯收紧；bootstrap 轮时序登记。 |
| 2026-10-10 | DONE | 真红修复（注册面单列）+ 两树 `TWO-TREE PASS` + 归档定格 + m0 23/23；`RECHECK-20261010-392` 独立复检。 |
