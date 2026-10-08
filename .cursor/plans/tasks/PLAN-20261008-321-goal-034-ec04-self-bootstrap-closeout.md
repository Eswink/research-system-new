---
id: PLAN-20261008-321
slug: goal-034-ec04-self-bootstrap-closeout
title: GOAL-034 cycle 3（EC-04）：自举收口 —— 验证器进树 + 两树复检 + 判词归档 + as-is m0 + 台账逐提交
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-322-goal-034-ec04-self-bootstrap-closeout.md
memory_entries:
  - run-the-governance-gate-before-committing-a-new-record
parent_goal: GOAL-20261008-034
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-034 的 **EC-04**（自举收口）。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：收口动作**复用既有机器**（`tools/closeout_recheck_tools` +
    `tools/closeout_recheck_assertions.standard_verdicts` + `tools/two_tree_recheck.py`），
    **标准断言集一行不重写**；`IN_SCOPE` **纯收紧**；**不改**任何既有判据的断言；
    **不得**宣称安全（`R-M1`），**不得**宣称投递语义为恰好一次（**明确否认**）。
objective: >-
    按 `MEM: goal-closeout-procedure` 完成 GOAL-034 的收口机械面：① 收口验证器进树
    （`tools/verify_goal034_closeout.py` + `tools/goal034_closeout_assertions.py`），复用
    标准断言集并**只写本轮特有断言**（含 EC-02 的**顺序**断言：结论判断必须先于护栏判断）；
    ② 加入 `IN_SCOPE`（**纯收紧**）并过四道门；③ 两树复检（`--script-mode shared` +
    `--base-ref`）+ **判词归档进树**（二进制写盘、`CR=0`）；④ as-is m0 **23/23**
    （在**全部记录写入之后**、独占、仓库 `.venv`、不接管道）；⑤ 治理 `validate.py` 绿 +
    MAINLINE 宪章判据绿；⑥ CI 台账**逐提交**；⑦ 残余与未覆盖逐条明写。
exit_criteria:
  - id: AC-1
    criterion: >-
      **验证器进树且真的可跑**：`tools/verify_goal034_closeout.py` 复用 `standard_verdicts`
      （**一行不重写**），本轮特有断言在 `tools/goal034_closeout_assertions.py`
      （4 个分区函数，均 ≤ 50 行）；`--verdict-only` 输出**只有** `PASS`/`FAIL` 行、
      且**不含任何树的绝对路径**。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal034_closeout.py --root .
      --verdict-only` ⇒ **59 PASS / 0 FAIL**；纯度与路径无关两条契约成立。
    status: PASS
  - id: AC-2
    criterion: >-
      **`IN_SCOPE` 纯收紧**：两个新脚本加入必备清单（只增不删），并过四道门。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_tooling_scripts_meet_product_gates.py -q` ⇒ 8 passed；
      `git diff --numstat` 对该文件只有新增行。
    status: PASS
  - id: AC-3
    criterion: >-
      **两树复检 `TWO-TREE PASS`**：`tools/two_tree_recheck.py --script-mode shared`
      ⇒ 两路判词逐字节相同（`sha256` 相同）。
    verify: >-
      入口输出 `TWO-TREE PASS`；两路 59 判词、`sha256` 相同（`9b05e6d5…`）。
    status: PASS
  - id: AC-4
    criterion: >-
      **判词归档进树**（两份，二进制写盘、`CR=0`）。**时序如实说明**：归档由两树入口
      **写出**，而验证器又**读**它们做存在性断言 ⇒ **首轮**那两条必红（归档尚未生成）
      ⇒ 跑**第二轮**后全绿（承 GOAL-032/033 同款）；**不得**为跳过首轮红而删掉断言。
    verify: >-
      `.cursor/plans/goals/evidence/GOAL-20261008-034-verdict-{current,clean}.txt`
      在树、逐字节相同、`CR=0`；第二轮 `--verdict-only` ⇒ 0 FAIL。
    status: PASS
  - id: AC-5
    criterion: >-
      **as-is m0 23/23**（在**全部记录写入之后**、独占、仓库 `.venv`、
      `uv run --frozen --no-sync python -B`、不接管道）；终局行
      `PASS: profile=m0; 23 deterministic checks`。
    verify: >-
      m0 日志终局行 + `PASS [` 行数（24 = 23 + `release-assets-immutable`）+ `FAILED [` 0。
    status: PASS
  - id: AC-6
    criterion: >-
      **治理绿 + 宪章判据绿 + 记录自洽**：`validate.py` 绿；
      `tests/tooling/test_mainline_program_is_intact.py` 绿。
    verify: >-
      `uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py`
      ⇒ 绿；`uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_mainline_program_is_intact.py -q` ⇒ 全绿。
    status: PASS
  - id: AC-7
    criterion: >-
      **CI 台账逐提交**（每个 commit 一行：run 链接 + 结论；`cancelled` 如实登记 + 原因 +
      `covered_by`；**空集合 / 空字段 = 未取证**；自我指涉边界**明写并封闭**）。
    verify: >-
      GOAL 的「CI 台账」节逐行在位；末条提交的边界明写。
    status: PASS
---

# PLAN-20261008-321 — GOAL-034 cycle 3（EC-04）：自举收口

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-7，全部 PASS）。

## 实施清单

- [x] `tools/goal034_closeout_assertions.py`（本轮特有断言：EC-01 声明面与懒展开 /
      EC-02 **顺序** / EC-03 读面 / 判据例数下界 / 归档形态）。
- [x] `tools/verify_goal034_closeout.py`（复用 `standard_verdicts` + 记录面）。
- [x] `IN_SCOPE` 纯收紧（`+2` 行）。门抓到 `assertion_verdicts` 77 行 > 50 行上限 ⇒ 拆 4 区。
- [x] 两树复检 + 判词归档进树。
- [x] as-is m0 23/23（全部记录写入之后）。
- [x] 治理绿 + 宪章判据绿 + CI 台账逐提交。

## 证据

### 收口读数（本树）

| 项 | 读数 |
| --- | --- |
| 验证器 `--verdict-only` | **59 判词 / 0 FAIL** |
| 两树复检 | **`TWO-TREE PASS`**（两路 59 判词、`sha256` 相同 `9b05e6d5…`） |
| 判词归档 | 两份 / 2039 B / 59 行 / **CR=0** / 逐字节相同 |
| as-is m0 | 见迭代日志「cycle 3」行（在全部记录写入之后） |
| 工具门 | `tests/tooling/test_tooling_scripts_meet_product_gates.py` 8 passed |
| 治理 | 绿 |

### bootstrap 时序（如实登记）

| 轮次 | base-ref | 读数 |
| --- | --- | --- |
| 首轮 | `b136cc8` | 两路判词**逐字节相同**（`e395107e…`），红项**仅**两份归档缺失 |
| 次轮 | `HEAD`（含归档） | **`TWO-TREE PASS`**（两路 `sha256` 相同 `9b05e6d5…`） |

### 一次返工（我自己的缺陷）

门抓到 `assertion_verdicts` **77 行** > 50 行上限 ⇒ 拆 4 个分区函数（**断言一条未改**，
纯搬迁）。

## 影响报告

- **Domain / API / schema 变化**：无（本 cycle 零产品改动）。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：无。
- **上游版本影响**：无。
- **下一项任务**：GOAL 收口后按 MAINLINE 程序表序 3（质量轴）开下一个 GOAL。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | DONE | cycle 3 落地：验证器 + 断言集进树（59 PASS / 0 FAIL）+ `IN_SCOPE` 纯收紧 + 两树 `TWO-TREE PASS` + 归档进树（CR=0）+ as-is m0 23/23 + 治理绿 + 台账逐提交。`latest_recheck` = `RECHECK-20261008-322`。 |
