---
id: PLAN-20261008-317
slug: goal-033-ec04-self-bootstrap-closeout
title: GOAL-033 cycle 4（EC-04）：自举收口 —— 验证器进树 + 两树复检 + 判词归档 + as-is m0 23/23 + CI 台账逐提交
status: IN_PROGRESS
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261008-033
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-033 的 **EC-04**（自举收口）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：收口动作**复用既有机器**（`tools/closeout_recheck_tools`
    + `tools/closeout_recheck_assertions.standard_verdicts` + `tools/two_tree_recheck.py`），
    **标准断言集一行不重写**；`IN_SCOPE` **纯收紧**；**不改**任何既有判据的断言；
    **不得**宣称安全（`R-M1`），**不得**宣称投递语义为恰好一次（**明确否认**）。
objective: >-
    按 `MEM: goal-closeout-procedure` 完成 GOAL-033 的收口机械面：① 收口验证器进树
    （`tools/verify_goal033_closeout.py` + `tools/goal033_closeout_assertions.py`），
    复用标准断言集并**只写本轮特有断言**；② 加入 `IN_SCOPE`（**纯收紧**）并过四道门；
    ③ 两树复检（`--script-mode shared` + `--base-ref`）+ **判词归档进树**
    （`.cursor/plans/goals/evidence/`，**二进制写盘**、`CR=0`）；④ as-is m0 **23/23**
    （在**全部记录写入之后**、独占、仓库 `.venv`、不接管道）；⑤ 治理 `validate.py` 绿 +
    MAINLINE 宪章判据绿；⑥ CI 台账**逐提交**；⑦ 残余与未覆盖逐条明写。
exit_criteria:
  - id: AC-1
    criterion: >-
      **验证器进树且真的可跑**：`tools/verify_goal033_closeout.py` 复用
      `standard_verdicts`（**一行不重写**），本轮特有断言在
      `tools/goal033_closeout_assertions.py`；`--verdict-only` 输出**只有** `PASS`/`FAIL`
      行、且**不含任何树的绝对路径**（两树入口会拒绝）。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal033_closeout.py --root .
      --verdict-only` ⇒ 判词计数 + 0 FAIL（除归档两份的**首轮**预期红，见 AC-4）。
    status: PENDING
  - id: AC-2
    criterion: >-
      **`IN_SCOPE` 纯收紧**：两个新脚本加入必备清单（只增不删），并过四道门
      （`ruff check` / `ruff format --check` / `mypy` / 规模门）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_tooling_scripts_meet_product_gates.py -q` ⇒ 全绿；
      `git diff --numstat -- tests/tooling/test_tooling_scripts_meet_product_gates.py`
      ⇒ 只有新增行。
    status: PENDING
  - id: AC-3
    criterion: >-
      **两树复检 `TWO-TREE PASS`**：`tools/two_tree_recheck.py --script-mode shared`
      + `--base-ref <建档基线>` ⇒ 两路判词逐字节相同（`sha256` 相同）。
    verify: >-
      入口输出含 `TWO-TREE PASS`；两份判词 `sha256` 相同。
    status: PENDING
  - id: AC-4
    criterion: >-
      **判词归档进树**（两份，二进制写盘、`CR=0`）。**时序须如实说明**：归档由两树入口
      **写出**，而验证器又**读**它们做存在性断言 ⇒ **首轮**那两条断言必红（归档尚未生成）
      ⇒ 跑**第二轮**后归档在位、全绿（承 GOAL-032 的同一形态：「归档定稿 = TWO-TREE PASS
      后的版本」）。**不得**为了跳过首轮红而删掉那两条断言。
    verify: >-
      `.cursor/plans/goals/evidence/GOAL-20261008-033-verdict-{current,clean}.txt` 在树、
      逐字节相同、`CR=0`；第二轮 `--verdict-only` ⇒ 0 FAIL。
    status: PENDING
  - id: AC-5
    criterion: >-
      **as-is m0 23/23**（在**全部记录写入之后**、独占、仓库 `.venv`、
      `uv run --frozen --no-sync python -B`、不接管道）；终局行
      `PASS: profile=m0; 23 deterministic checks`。
    verify: >-
      m0 日志终局行 + `PASS [` 行数（24 = 23 + `release-assets-immutable`）。
    status: PENDING
  - id: AC-6
    criterion: >-
      **治理绿 + 宪章判据绿 + 记录自洽**：`validate.py` 绿；
      `tests/tooling/test_mainline_program_is_intact.py` 绿；MAINLINE 的**进展记录**行
      指向真实 RECHECK 文件。
    verify: >-
      `uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py`
      ⇒ 绿；`uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_mainline_program_is_intact.py -q` ⇒ 全绿。
    status: PENDING
  - id: AC-7
    criterion: >-
      **CI 台账逐提交**（本 GOAL 的每个 commit 一行：run 链接 + 结论；
      `cancelled` 如实登记 + 原因 + `covered_by`；**空集合 / 空字段 = 未取证**；
      自我指涉边界**明写并封闭**）。
    verify: >-
      GOAL 的「CI 台账」节逐行在位；末条提交的边界明写。
    status: PENDING
---

# PLAN-20261008-317 — GOAL-033 cycle 4（EC-04）：自举收口

## 实施清单

- [x] `tools/goal033_closeout_assertions.py`（本轮特有断言：EC-01 产品入口 / EC-02 协同 /
      EC-03 声明集下界 / MAINLINE 宪章 / 判据例数下界 / 判词归档形态）。
- [x] `tools/verify_goal033_closeout.py`（复用 `standard_verdicts` + 记录面）。
- [x] `IN_SCOPE` 纯收紧（`+3 / -0`）。
- [ ] 两树复检 + 判词归档进树。
- [ ] as-is m0 23/23。
- [ ] 治理绿 + 宪章判据绿 + CI 台账逐提交。

## 证据

（随收口完成逐条回填。）

## 影响报告

- **Domain / API / schema 变化**：无（本 cycle 零产品改动）。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：无。
- **上游版本影响**：无。
- **下一项任务**：GOAL 收口后按 MAINLINE 程序表序 2（深度轴）开下一个 GOAL。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | cycle 4 开工：验证器 + 本轮断言集进树；`IN_SCOPE` 纯收紧（门抓到两处自己的缺陷：`assertion_verdicts` 58 行超限 + 格式待排 ⇒ 已拆分/格式化）。两树 / m0 / 台账待跑。 |
