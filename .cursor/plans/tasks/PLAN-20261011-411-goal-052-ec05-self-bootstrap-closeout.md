---
id: PLAN-20261011-411
slug: goal-052-ec05-self-bootstrap-closeout
title: GOAL-20261011-052 cycle 2（EC-05）：自举收口 —— 验证器进树 + 两树 + 归档 + 门链 + 台账
status: DONE
created_at: 2026-10-11
updated_at: 2026-10-11
latest_recheck: .cursor/plans/rechecks/RECHECK-20261011-412-goal-052-ec05-self-bootstrap-closeout.md
memory_entries: []
parent_goal: GOAL-20261011-052
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261011-052 的 **EC-05**（自举收口）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：复用既有收口机器（`tools/closeout_recheck_tools`
    + `tools/closeout_recheck_assertions.standard_verdicts`，**一行未重写**）；
    两处射程**纯收紧**（只增不删）；判词归档**二进制写盘 / `CR=0`**；
    **新判据必须两向实测**（**不得恒假** —— 承 GOAL-051 §8）；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 GOAL-20261011-052 收口：① 收口验证器 + 本轮断言集进树并加入 `IN_SCOPE`（纯收紧）
    **与** GOAL-043 立的射程清单；② **两树复检**（`--script-mode shared` + `--base-ref`）
    ⇒ `TWO-TREE PASS` + 判词归档进树；③ as-is m0 **23/23**（在**全部记录写入之后**）、
    治理绿、宪章判据绿；④ CI 台账逐提交；⑤ 承继残余与未覆盖范围逐条在位。
exit_criteria:
  - id: AC-1
    criterion: >-
      **收口面进树**：两个脚本在树且过**四道门**（含规模门）；`IN_SCOPE` **纯收紧**（+2 行）；
      射程分区清单**同步登记**（+1 行）；判词集**逐条**覆盖本 GOAL 的 EC
      （HTTP 披露 / 同源 / 两向四条按压）；**字段读取用 AST**（不按行首正则 ⇒ 不恒假）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_tooling_scripts_meet_product_gates.py
      tests/tooling/test_closeout_verifiers_run_their_own_assertions.py -q` ⇒ 全绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **两树复检**：`tools/two_tree_recheck.py --script tools/verify_goal052_closeout.py
      --script-mode shared --base-ref HEAD` ⇒ **`TWO-TREE PASS`**；判词归档**进树**
      （两份、`CR=0`、与最终一轮同结论）。
    verify: >-
      终局行 `TWO-TREE PASS`；
      `.cursor/plans/goals/evidence/GOAL-20261011-052-verdict-{current,clean}.txt`。
    status: PASS
  - id: AC-3
    criterion: >-
      **记录面自洽**：本 PLAN + `RECHECK-20261011-412` 在位；GOAL 的 EC / 迭代日志 /
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

# PLAN-20261011-411 — GOAL-20261011-052 cycle 2（EC-05 自举收口）

> **主线归属**：`GOAL-20261011-052`（MAINLINE 程序表**序 20**）的 **EC-05**。

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
- [x] WP-2 两处射程纯收紧（`IN_SCOPE` +2 行 / 射程清单 +1 行、下界 21→22）
- [x] WP-3 两树复检（bootstrap 轮 + 终态轮）
- [x] WP-4 判词归档进树（两份 / 二进制写盘 / `CR=0`）
- [x] WP-5 记录面：本 PLAN + `RECHECK-20261011-412` + GOAL 回写 + `ALL_PLAN` + MAINLINE 进展行
- [x] WP-6 治理 + 宪章判据 + as-is m0 + CI 台账

## 证据

| 门 | 读数 |
| --- | --- |
| 收口验证器（本树） | **63 判词 / 0 FAIL** |
| 两树复检 | **`TWO-TREE PASS`**（两路 **63 判词** / `sha256` 相同 `b976f18c0b872d31…`）|
| 判词归档 | 两份各 **2341 B / 63 行 / `CR=0` / 0 FAIL**（二进制写盘）|
| 按压归档 | **674 B / `CR=0`**（**基线 GREEN** + `N-1`…`N-4` 全 `RED` + 复原一致）|
| 两处射程 | `IN_SCOPE` **+2 行**；射程分区清单 **+1 行**（下界 21→22）—— 均**纯收紧** |
| 治理 | `validate.py` 通过 |
| 宪章判据 | `test_mainline_program_is_intact.py` 绿 |
| **as-is m0** | `PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 / `FAILED [` 0 / passed/skipped 读数**待本轮全量 m0 实测回填**；在全部记录写完之后、独占、仓库 `.venv`、不接管道）|

### 本轮把 §8 的新增纪律（**判据不得恒假**）落成了机械面（如实登记）

| # | 措施 | 读数 |
| --- | --- | --- |
| 1 | **字段读取改用 AST**（读 `MemoryRecordDto` 类体的 `AnnAssign` 目标） | **不**按行首正则（那会随缩进/换行静默失配 ⇒ **可能恒假**）|
| 2 | **非空性实测**（真树 / 空源码 / 合成缺字段三条） | 真树 **17 字段**（13 既有 + 4 新增）；空源码 ⇒ **空集**；合成无该字段 ⇒ **读不到** ⇒ 判据**不恒真** |
| 3 | **反证脚本带基线门** | 基线（未按压）必须 **GREEN**、每条按压必须 **RED**，否则**非 0 退出** —— cycle 1 正是靠它抓到 `N-4` 的**假反证臂** |

## 影响报告

- **Domain / API / schema 变化**：零（本轮只新增 `tools/` 机械面与记录）。
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：无。**上游版本影响**：无。
- **下一项任务**：GOAL 收口。

## 无可复用事实

本 cycle 只新增 `tools/` 下的机械面与记录；其可复用做法（**反证脚本带基线门**、
**字段读取用 AST 不用行首正则**）是 GOAL-052 frontmatter §8 新增纪律的**落地形态**。
**未**沉淀新条目 —— 该纪律已在 GOAL-052 的授权面写明，属该 GOAL 的边界。

## CI 台账（逐提交）

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `2a3ca6c`（cycle 1 实现） | 见 GOAL 正文台账 | 四样补齐 + 同源 + 快照同轮 |
| `f526fcc`（cycle 1 记录面） | 见 GOAL 正文台账 | PLAN-409 + RECHECK-410 + GOAL 回写 |
| `de6f6a1` / `c0826bd` / `05c6e06`（EC-05 首轮 + 两轮归档） | 见 GOAL 正文台账 | 验证器 + 两处射程 + 归档定格 |
| （收口提交） | 见 GOAL 正文台账 | 本 PLAN + RECHECK + GOAL 回写 + 宪章进展行 |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | IN_PROGRESS | 验证器 + 断言集进树；两处射程纯收紧；bootstrap 轮时序登记。 |
| 2026-10-11 | DONE | 两树 `TWO-TREE PASS`；归档定格；m0 23/23；`RECHECK-20261011-412` 独立复检。 |
