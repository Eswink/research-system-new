---
id: PLAN-20261009-363
slug: goal-041-ec05-self-bootstrap-closeout
title: GOAL-20261009-041 cycle 2（EC-05）：自举收口 —— 验证器进树 + 两树 + 归档 + 门链 + 台账
status: DONE
created_at: 2026-10-09
updated_at: 2026-10-09
latest_recheck: .cursor/plans/rechecks/RECHECK-20261009-364-goal-041-ec05-self-bootstrap-closeout.md
memory_entries: []
parent_goal: GOAL-20261009-041
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261009-041 的 **EC-05**（自举收口）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：复用既有收口机器（`tools/closeout_recheck_tools`
    + `tools/closeout_recheck_assertions.standard_verdicts`，**一行未重写**）；
    `IN_SCOPE` **纯收紧**（只增不删）；判词归档**二进制写盘 / `CR=0`**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 GOAL-20261009-041 收口：① 收口验证器 + 本轮断言集进树并加入 `IN_SCOPE`（纯收紧）；
    ② **两树复检**（`--script-mode shared` + `--base-ref`）⇒ `TWO-TREE PASS` + 判词归档进树；
    ③ as-is m0 **23/23**（在**全部记录写入之后**）、治理绿、宪章判据绿；
    ④ CI 台账逐提交；⑤ 承继残余与未覆盖范围逐条在位。
exit_criteria:
  - id: AC-1
    criterion: >-
      **收口面进树**：`tools/verify_goal041_closeout.py` + `tools/goal041_closeout_assertions.py`
      在树且过**四道门**（含规模门）；`IN_SCOPE` **纯收紧**（+2 行）；
      并含一条**自指判词** `self-loads-its-own-assertions` —— 把 GOAL-038/039/040 实测到的
      「声明自己的断言集却加载上一轮那份 ⇒ 自有断言从未运行」做成**机器可检**的事实。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_tooling_scripts_meet_product_gates.py -q` ⇒ 8 passed。
    status: PASS
  - id: AC-2
    criterion: >-
      **两树复检**：`tools/two_tree_recheck.py --script tools/verify_goal041_closeout.py
      --script-mode shared --base-ref b47bcd0` ⇒ **`TWO-TREE PASS`**（两路 **63 判词**、
      `sha256` **相同**）；判词归档**进树**（两份、`CR=0`）。
    verify: >-
      终局行 `TWO-TREE PASS`；归档 `.cursor/plans/goals/evidence/GOAL-20261009-041-verdict-{current,clean}.txt`
      ⇒ 两份 `sha256` 相同 `53b77cf6…` / 各 63 行 / `CR=0` / 0 FAIL。
    status: PASS
  - id: AC-3
    criterion: >-
      **记录面自洽**：本 PLAN + `RECHECK-20261009-364` 在位；GOAL 的 EC / 迭代日志 /
      状态历史 / `latest_recheck` / `child_plans` 全部回写；`ALL_PLAN` 投影一致；
      治理 `validate.py` 绿 + `test_mainline_program_is_intact.py` 绿。
    verify: >-
      `uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py`
      ⇒ 通过；`pytest tests/tooling/test_mainline_program_is_intact.py -q` ⇒ 8 passed。
    status: PASS
  - id: AC-4
    criterion: >-
      **as-is m0 23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、
      `uv run --frozen --no-sync python -B`、不接管道）。
    verify: >-
      终局行 `PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 / `FAILED [` 0）。
    status: PASS
  - id: AC-5
    criterion: >-
      **CI 台账逐提交**（`cancelled` 如实登记 + 原因 + `covered_by`；空集合 = 未取证；
      自我指涉边界明写并封闭）。
    verify: >-
      `scratch/poll_ci_all.sh <sha>` 遍历该 sha 全部 run + `/jobs`；台账表见 GOAL 正文。
    status: PASS
---

# PLAN-20261009-363 — GOAL-20261009-041 cycle 2（EC-05 自举收口）

> **主线归属**：`GOAL-20261009-041`（MAINLINE 程序表**序 9**）的 **EC-05**。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 收口面进树 + 四道门 + `IN_SCOPE` 纯收紧（含自指判词） | PASS |
| AC-2 | 两树 `TWO-TREE PASS` + 判词归档进树（`CR=0`） | PASS |
| AC-3 | 记录面自洽 + 治理 + 宪章判据绿 | PASS |
| AC-4 | as-is m0 **23/23**（记录写完之后） | PASS |
| AC-5 | CI 台账逐提交 | PASS |

## 实施清单

- [x] WP-1 `tools/verify_goal041_closeout.py` + `tools/goal041_closeout_assertions.py` 进树
- [x] WP-2 `IN_SCOPE` 纯收紧（+2 行，只增不删）
- [x] WP-3 两树复检 3 轮（首轮/次轮为 bootstrap 时序红，第 3 轮 `TWO-TREE PASS`）
- [x] WP-4 判词归档进树（两份 / 二进制写盘 / `CR=0`）
- [x] WP-5 记录面：本 PLAN + `RECHECK-20261009-364` + GOAL 回写 + `ALL_PLAN` + MAINLINE 进展行
- [x] WP-6 治理 + 宪章判据 + as-is m0 + CI 台账

## 证据

| 门 | 读数 |
| --- | --- |
| 收口验证器（本树） | **63 PASS / 0 FAIL**（`--verdict-only`） |
| 两树复检 | **`TWO-TREE PASS`**（两路 63 判词；`sha256` 相同 `53b77cf6…`） |
| 判词归档 | 两份各 **2323 B / 63 行 / `CR=0` / 0 FAIL**（二进制写盘） |
| `IN_SCOPE` 判据 | 8 passed（纯收紧：只增两条） |
| 治理 | `validate.py` 通过 |
| 宪章判据 | 8 passed |
| **as-is m0** | `PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 / `FAILED [` 0 / **5278 passed, 228 skipped**；在**全部记录写入之后**、独占、不接管道） |

### 两树首轮的**预期时序红**（如实登记，不淡化）

- 第 1 轮（`--base-ref 7c9b35c`）：`DIFF 第 42 行`（`scope-declares-this-rounds-scripts`，
  干净树尚无 `IN_SCOPE` 的两条）+ 两份归档 missing ⇒ `TWO-TREE RED`；
- 第 2 轮（`--base-ref dfcdb56`）：干净树已含 `IN_SCOPE` ⇒ 只剩**归档** missing
  （归档提交在其后）⇒ `TWO-TREE RED`；
- 第 3 轮（`--base-ref b47bcd0`，含归档）⇒ **`TWO-TREE PASS`**。

**这是 bootstrap 时序**（干净 checkout 逐提交推进），不是判据缺口 —— 与 GOAL-040 同款并如实登记。

## 影响报告

- **Domain / API / schema 变化**：零（本轮只新增 `tools/` 机械面与记录）。
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：无。**上游版本影响**：无。
- **下一项任务**：GOAL 收口。

## 无可复用事实

本 cycle 只新增 `tools/` 下的机械面与记录；其可复用事实（决策自然键的单调 tie-breaker）
已由 `MEM-20261009-211` 承载。

## CI 台账（逐提交）

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `dfcdb56`（cycle 2 提交 A = EC-05 首轮） | 见 GOAL 正文台账（与收口提交同批） | 验证器 + 断言集 + `IN_SCOPE` |
| `b47bcd0`（cycle 2 提交 B = 归档） | 见 GOAL 正文台账（与收口提交同批） | 两份判词归档进树 |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-09 | IN_PROGRESS | 验证器 + 断言集进树；`IN_SCOPE` 纯收紧；两树首轮/次轮红（bootstrap 时序）。 |
| 2026-10-09 | DONE | 两树第 3 轮 `TWO-TREE PASS`（63 判词 / sha256 相同）；归档定格；治理 + 宪章判据绿；`RECHECK-20261009-364` 独立复检。 |
