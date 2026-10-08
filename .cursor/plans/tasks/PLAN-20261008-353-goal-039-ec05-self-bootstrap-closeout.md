---
id: PLAN-20261008-353
slug: goal-039-ec05-self-bootstrap-closeout
title: GOAL-039 cycle 2（EC-05）：自举收口 —— 验证器进树 + 两树复检 + 判词归档 + as-is m0 + 治理 + 台账
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-354-goal-039-ec05-self-bootstrap-closeout.md
memory_entries: []
parent_goal: GOAL-20261008-039
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-039 的 **EC-05**（自举收口）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**不改**任何既有判据 / 门禁 / 阈值；
    `IN_SCOPE` **纯收紧**；判词行**不含**任何树的绝对路径；**不读**两树写出的判词做一致性
    断言；**不得**为让首轮变绿而删掉存在性断言（bootstrap 时序如实登记）；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 GOAL-039 收口成**可机械复核**的终态：验证器 + 本轮断言集进树并进 `IN_SCOPE`
    （**纯收紧**）；两树复检 + 判词归档进树（二进制写盘、`CR=0`）；as-is m0 **23/23**
    （在全部记录写入之后）；治理 + 宪章判据绿；CI 台账逐提交；承继残余与本轮 `Q-1`…`Q-3`
    逐条定格。
exit_criteria:
  - id: AC-1
    criterion: >-
      **验证器进树且复用标准断言集**：`tools/verify_goal039_closeout.py` 调用
      `standard_verdicts(root)`（一行不重写），本轮断言收在
      `tools/goal039_closeout_assertions.py`；`--verdict-only` 只有 `PASS` / `FAIL` 前缀
      且不含任何树的绝对路径。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal039_closeout.py --root .
      --verdict-only` ⇒ 逐行判词；非判词行 0、路径行 0。
    status: PASS
  - id: AC-2
    criterion: >-
      **`IN_SCOPE` 纯收紧**：本轮两个新脚本进清单（只增不删）并过四道门。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_tooling_scripts_meet_product_gates.py -q` ⇒ 全绿（8 passed）。
    status: PASS
  - id: AC-3
    criterion: >-
      **两树复检 + 归档进树**：`--script-mode shared --base-ref` ⇒ `TWO-TREE PASS`；
      归档在树、非空、`CR=0`；bootstrap 时序如实登记。
    verify: >-
      入口两轮读数 + 归档形态读数。
    status: PASS
  - id: AC-4
    criterion: >-
      **as-is m0 23/23（在全部记录写入之后）**：终局行
      `PASS: profile=m0; 23 deterministic checks`；`PASS [` 24 / `FAILED [` 0。
    verify: >-
      m0 日志终局行 + `passed/skipped` 读数。
    status: PASS
  - id: AC-5
    criterion: >-
      **治理 + 宪章判据**：`validate.py` 绿；`test_mainline_program_is_intact.py` 绿
      （本 GOAL 的 id 在程序表序 7、进展记录行指向真实 RECHECK 文件）。
    verify: >-
      两条命令的终局输出。
    status: PASS
  - id: AC-6
    criterion: >-
      **承继残余与未覆盖逐条明写**：GOAL-038 的 `P-1`…`P-3` / GOAL-037 的 `O-1`…`O-5` /
      `R26-*` 终态 / 未覆盖范围逐条在位；本轮 `Q-1`…`Q-3` 逐条定格。
    verify: >-
      验证器 `residuals-enumerated` / `prior-residuals-kept` / `uncovered-scope-enumerated`。
    status: PASS
  - id: AC-7
    criterion: >-
      **CI 台账逐提交**（`cancelled` 如实登记 + 原因 + `covered_by`；自我指涉边界明写封闭）。
    verify: >-
      GOAL「CI 台账」节的逐提交行 + 边界行的封闭说明。
    status: PASS
---

# PLAN-20261008-353 — GOAL-039 cycle 2（EC-05）自举收口

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 验证器进树（复用标准断言集一行未重写；判词纯且与路径无关） | PASS |
| AC-2 | `IN_SCOPE` 纯收紧 + 两脚本过四道门 | PASS |
| AC-3 | 两树复检 `TWO-TREE PASS` + 判词归档进树（`CR=0`） | PASS |
| AC-4 | as-is m0 23/23（在全部记录写入之后） | PASS |
| AC-5 | 治理 + 宪章判据绿 | PASS |
| AC-6 | 承继残余与未覆盖逐条（`P-1`…`P-3` + 本轮 `Q-1`…`Q-3`） | PASS |
| AC-7 | CI 台账逐提交 | PASS |

## 实施清单

- [x] `tools/verify_goal039_closeout.py` + `tools/goal039_closeout_assertions.py`。
- [x] `tests/tooling/test_tooling_scripts_meet_product_gates.py`：`IN_SCOPE` **纯收紧** +2 行。
- [x] `.cursor/plans/goals/evidence/GOAL-20261008-039-verdict-{current,clean}.txt`。
- [x] 记录面：本 PLAN、`RECHECK-20261008-354`、GOAL 收口面、MAINLINE 进展行、`ALL_PLAN`。

## 证据

| 门 | 读数 |
| --- | --- |
| 规模（450 行 / 函数 50 行） | 断言集 **227** 行 / 验证器 **~205** 行（函数均 ≤ 50） |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | **8 passed** |
| `--verdict-only`（起草中间态） | **70 PASS / 3 FAIL**（EC-01 未翻 + 本轮两份记录未写）⇒ 收口态 **73 判词 / 0 FAIL** |
| 两树复检 | 首轮 bootstrap 红（读数见 `RECHECK-20261008-354`）；次轮 **`TWO-TREE PASS`** |
| as-is m0 | 读数见 GOAL 迭代日志 cycle 2 行 |

## 影响报告

- **Domain / API / schema 变化**：零（本轮只新增 `tools/` 机械面与记录）。
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：无。**观测隐私**：无新出口。
- **下一项任务**：收口后**立即开下一个 GOAL**。

## 无可复用事实

本 cycle 只新增 `tools/` 下的机械面与记录；收口机器的可复用事实已由
`MEM-20261008-203` / `MEM-20261008-206` 承载。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | 两脚本进树 + `IN_SCOPE` 纯收紧 + 判据 8 passed；中间态 70 PASS / 3 FAIL（预期时序）。 |
| 2026-10-08 | DONE | 两树次轮 `TWO-TREE PASS`、归档进树（`CR=0`）、治理 + 宪章判据绿、CI 台账逐提交。`RECHECK-20261008-354` 独立复检。 |
