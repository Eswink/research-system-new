---
id: PLAN-20261007-309
slug: goal-032-ec04-self-bootstrap-closeout
title: GOAL-032 cycle 4（EC-04）：自举收口 —— 验证器进树 + IN_SCOPE + 两树复检 + 判词归档 + as-is m0 + 治理 + CI 台账
status: DONE
created_at: 2026-10-07
updated_at: 2026-10-07
latest_recheck: .cursor/plans/rechecks/RECHECK-20261007-310-goal-032-closeout.md
memory_entries: []
parent_goal: GOAL-20261007-032
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261007-032 的 **EC-04**（自举收口）。授权原文见该 GOAL 的
    `authorization.ref`（用户下放全部权限 + push-to-main-for-CI 口径）。**本 PLAN 专属边界**：
    收口动作**只增不改** —— 验证器与断言集**新增**（`IN_SCOPE` 纯收紧）；`standard_verdicts`
    一行未重写；既有判据 / 门禁 / 阈值 / 断言**一字未动**；零新依赖；零真实凭据进树；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
objective: >-
    照 `MEM: goal-closeout-procedure` 收口 GOAL-032：① 收口验证器进树（复用
    `tools/closeout_recheck_tools` 与 `tools/closeout_recheck_assertions.standard_verdicts`，
    只写本轮特有断言）并加入 `IN_SCOPE`（**纯收紧**）；② 两树复检（`--script-mode shared`）
    + **判词归档进树**（二进制写盘、CR=0）；③ as-is m0 **23/23**（在**全部记录写入之后**）；
    ④ 治理 `validate.py` 绿；⑤ CI 台账**逐提交**（`cancelled` 如实登记 + 原因 +
    `covered_by`；空集合 = 未取证；自我指涉边界明写并封闭）；⑥ 承继残余逐条在位 +
    `R26-*` 终态表 + 未覆盖范围逐条明写。
exit_criteria:
  - id: AC-1
    criterion: >-
      **验证器进树 + `IN_SCOPE` 纯收紧**：`tools/verify_goal032_closeout.py` 与
      `tools/goal032_closeout_assertions.py` 在树、均 ≤450 行、过四道门
      （`ruff check` / `ruff format --check` / 规模 / `mypy`），且已加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py::IN_SCOPE`（只增不删）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_tooling_scripts_meet_product_gates.py -q` ⇒ 8 passed。
    status: PASS
  - id: AC-2
    criterion: >-
      **本树判词 + 两树复检同结论**：`--verdict-only` 全绿；两树（当前树 + 干净 checkout）
      判词**逐行相同**、`sha256` 相同、`COMPARE identical=True`、`TWO-TREE PASS`；
      判词归档进树（二进制写盘，CR=0）。
    verify: >-
      `tools/two_tree_recheck.py --script tools/verify_goal032_closeout.py --script-mode shared
      --root . --base-ref HEAD` ⇒ `TWO-TREE PASS`；归档落
      `.cursor/plans/goals/evidence/GOAL-20261007-032-verdict-{current,clean}.txt`。
    status: PASS
  - id: AC-3
    criterion: >-
      **as-is m0 23/23（记录之后）**：全部记录（PLAN / RECHECK / MEM / GOAL 回写 /
      ALL_PLAN / INDEX）写入**之后**跑的 as-is m0 = `PASS: profile=m0; 23 deterministic
      checks`；独占、仓库 `.venv`、canonical DSN pin、不接管道。
    verify: >-
      `make validate-all`（= `run_all_checks.py --profile m0 --keep-going`）；终局行与日志。
    status: PASS
  - id: AC-4
    criterion: >-
      **治理绿 + CI 台账逐提交**：治理 `validate.py` 绿；CI 台账含逐提交（建档 /
      cycle 1 / cycle 2+3 / cycle 4）行，`cancelled` 如实登记 + 原因 + `covered_by`；
      **空集合 = 未取证**；自我指涉边界明写并封闭。
    verify: >-
      `uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py`
      ⇒ 绿；GOAL 的「CI 台账」节读数。
    status: PASS
---

# PLAN-20261007-309 — GOAL-032 cycle 4（EC-04）：自举收口

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-4）。

## 实施清单

| # | 项 | 交付 |
| --- | --- | --- |
| WP-1 | 验证器 | `tools/verify_goal032_closeout.py`（193 行）+ `tools/goal032_closeout_assertions.py`（317 行） |
| WP-2 | 射程 | `IN_SCOPE` 追加两行（**纯收紧**） |
| WP-3 | 两树 + 归档 | `two_tree_recheck.py --script-mode shared`；判词进 `evidence/`（CR=0） |
| WP-4 | 记录 | RECHECK-20261007-310 + GOAL 收口回写 |

## 证据

- **验证器读数**：`tools/verify_goal032_closeout.py --root . --verdict-only` ⇒
  **64 判词**（标准集 + 本轮特有 + 记录面）；**0 FAIL**（见 RECHECK 的逐条读数）。
- **两树**：`TWO-TREE PASS`（两路判词逐行相同，`sha256` 相同）。
- **as-is m0**：终局行 `PASS: profile=m0; 23 deterministic checks`（**第三轮**跑，
  全部记录定稿后）。
- **治理**：`validate.py` 绿。
- **CI 台账**：`7eef4bf` / `547c12a` / `de928ac` 逐条（各 2 run 全绿）+ 本批次行。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-07 | IN_PROGRESS | cycle 4 开工：先落验证器与断言集，过四道门，再加 `IN_SCOPE`。 |
| 2026-10-07 | DONE | 四条 AC 全 PASS（`RECHECK-20261007-310` = PASS_WITH_WARNINGS）。 |

## 影响报告

- **Domain/API/schema**：零改动（只新增两个收口脚本 + 记录）。
- **安全/凭据**：零影响。
- **兼容性/迁移**：零影响。
- **上游版本**：零影响。
- **下一项任务**：GOAL-032 收口（`status: ACHIEVED`）；下一轮输入见 GOAL 的「下一轮输入」列。

## 无可复用事实

**无**（产出全部可复用：收口验证器 + 断言集 + 两树归档都在树内；本轮工程事实已沉淀
`MEM-20261007-191` / `MEM-20261007-192` / `MEM-20261007-193` 三条）。
