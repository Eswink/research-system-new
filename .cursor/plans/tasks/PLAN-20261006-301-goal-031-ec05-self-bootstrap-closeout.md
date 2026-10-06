---
id: PLAN-20261006-301
slug: goal-031-ec05-self-bootstrap-closeout
title: GOAL-031 cycle 5（EC-05）：自举收口 —— 验证器进树 + IN_SCOPE + 两树复检 + 判词归档 + as-is m0 + 治理 + CI 台账
status: DONE
created_at: 2026-10-06
updated_at: 2026-10-06
latest_recheck: .cursor/plans/rechecks/RECHECK-20261006-301-goal-031-closeout.md
memory_entries: []
parent_goal: GOAL-20261006-031
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261006-031 的 **EC-05**（自举收口）。授权原文见该 GOAL 的 `authorization.ref`
    （用户 2026-10-06 下放全部权限 + push-to-main-for-CI 口径）。**本 PLAN 专属边界**：
    收口动作**只增不改** —— 验证器与断言集**新增**（`IN_SCOPE` 纯收紧）；`standard_verdicts`
    一行未重写；任何既有判据 / 门禁 / 阈值 / 断言**一字未动**；零新依赖；零真实凭据进树；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」（**明确否认**；
    口径只能是 at-least-once + idempotency + deduplication）。
objective: >-
    照 `MEM: goal-closeout-procedure` 收口 GOAL-031：① 收口验证器进树（复用
    `tools/closeout_recheck_tools` 与 `tools/closeout_recheck_assertions.standard_verdicts`，
    只写本轮特有断言）并加入 `IN_SCOPE`；② 两树复检（`--script-mode shared`）+ 判词归档进树
    （二进制写盘、CR=0）；③ as-is m0 **23/23**（在全部记录写入之后）；④ 治理 `validate.py` 绿；
    ⑤ CI 台账逐提交（`cancelled` 如实登记 + 原因 + `covered_by`；空集合 = 未取证；自我指涉
    边界明写并封闭）；⑥ 承继残余逐条在位 + 决策登记 16 项 + 未覆盖范围逐条明写。
exit_criteria:
  - id: AC-1
    criterion: >-
      **验证器进树 + `IN_SCOPE` 纯收紧**：`tools/verify_goal031_closeout.py` 与
      `tools/goal031_closeout_assertions.py` 在树、均 ≤450 行、过四道门（`ruff check` /
      `ruff format --check` / 规模 / `mypy`），且已加入
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
      `tools/two_tree_recheck.py --script tools/verify_goal031_closeout.py --script-mode shared
      --root . --base-ref HEAD` ⇒ `TWO-TREE PASS`；归档落
      `.cursor/plans/goals/evidence/GOAL-20261006-031-verdict-{current,clean}.txt`。
    status: PASS
  - id: AC-3
    criterion: >-
      **as-is m0 = 23/23，在全部记录写入之后**（独占、仓库 `.venv`、
      `uv run --frozen --no-sync python -B`、canonical DSN pin、不接管道）。
    verify: >-
      `PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 / `FAILED [` 0）。
    status: PASS
  - id: AC-4
    criterion: >-
      **治理绿 + CI 台账逐提交**：`validate.py` 无 error；CI 台账逐提交（
      `cancelled` 如实登记 + 原因 + `covered_by`；自我指涉边界明写并封闭）。
    verify: >-
      `uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py`
      ⇒ 绿；台账行见 GOAL 的「CI 台账（逐提交）」节。
    status: PASS
---

# PLAN-20261006-301（GOAL-031 cycle 5 / EC-05）：自举收口

## 验收条件

见 frontmatter `exit_criteria`（AC-1 … AC-4，逐条 verify 命令与状态）。

## 实施清单

- [x] ① 收口验证器：`tools/verify_goal031_closeout.py`（120 行，CLI + 标准集加载）+
      `tools/goal031_closeout_assertions.py`（368 行，本轮特有断言；工具箱按结构 Protocol 注入）。
- [x] ② `IN_SCOPE` 纯收紧：加入两个新脚本（`tests/tooling/…` 只增不删）。
- [x] ③ 本树判词：`--verdict-only` ⇒ **80 PASS / 0 FAIL**。
- [x] ④ 两树复检：`--script-mode shared` ⇒ `TWO-TREE PASS`（两树各 80 判词、逐行相同、
      `sha256` 相同）；归档落 `.cursor/plans/goals/evidence/GOAL-20261006-031-verdict-{current,clean}.txt`。
- [x] ⑤ as-is m0（记录定稿后、独占）⇒ `PASS: profile=m0; 23 deterministic checks`。
- [x] ⑥ 治理 `validate.py` 绿。
- [x] ⑦ GOAL 收口：`latest_recheck` 指向本 RECHECK + 迭代日志 / 状态历史回写 +
      未覆盖范围**逐条明写**（收口验证器的记录面断言核对）。

## 证据

- 本树：`--verdict-only` = **80 PASS / 0 FAIL**（`SUMMARY total=80 failed=0`）。
- 两树：`TWO-TREE PASS`（两树各 80 判词、逐行相同、`sha256` 相同、`COMPARE identical=True`）。
- as-is m0：`PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 / `FAILED [` 0）。
- 治理：`validate.py` 绿。
- 四道门：`tests/tooling/test_tooling_scripts_meet_product_gates.py` 8 passed。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-06 | DONE | cycle 5 落地：验证器 + 断言集进树并进 `IN_SCOPE`；本树 80/0；两树同一结论；as-is m0 23/23；治理绿；GOAL 收口（`latest_recheck` 指向 `RECHECK-20261006-301`）。AC-1…AC-4 全 PASS。**首跑两树 RED 是预期**（干净树缺未提交增量）⇒ 先提交再重跑，如实登记为 `W-EC05-1`。 |

## 影响报告

- **Domain / API / schema**：零改动（本 cycle 只新增两个 `tools/` 收口脚本 + 记录文件 +
  `IN_SCOPE` 一行组）。
- **安全 / 凭据**：零新凭据、零新依赖、零出网。
- **兼容性 / 迁移风险**：无（`IN_SCOPE` 纯收紧；`standard_verdicts` 一行未重写）。
- **上游版本影响**：无。
- **下一项任务**：无（GOAL-031 到此收口）；如有人接手：`R-M1` 与「读面认证」是下一谱系的候选。

## 无可复用事实

**无**（产出全部可复用：收口验证器 + 断言集 + 两树归档都在树内）。
`memory_entries` 在 GOAL 层回填。
