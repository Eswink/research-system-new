---
id: PLAN-20261016-495
slug: goal-080-ec05-self-bootstrap-closeout
title: GOAL-080 cycle 5 — 自举收口（EC-05）
status: DONE
created_at: 2026-10-16
updated_at: 2026-10-16
parent_goal: GOAL-20261015-080
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261016-496-goal-080-ec05-self-bootstrap-closeout.md
memory_entries: []
---

# PLAN-20261016-495 — GOAL-080 cycle 5

## 验收条件

- [x] 收口资产进树（`tools/goal080_closeout_assertions.py` + `tools/verify_goal080_closeout.py`）
- [x] 两处射程**纯收紧**（`IN_SCOPE` / `_VERIFIERS` 各 +2，只增不删）
- [x] 两树复检（判词归档进树、二进制写盘、`CR=0`、`sha256` 一致）
- [x] as-is m0 23/23（**在全部记录写入之后**）
- [x] 治理绿 + 凭据审计四面零命中
- [x] CI 台账**逐提交**（`cancelled` 如实登记 + 原因 + `covered_by`）
- [x] **阶梯记账**：宪章 `进展记录` 追加本行（**能力域 = 计划**）+ 「计划」域 `依据 GOAL` 收录本 GOAL
- [x] 残余与未覆盖范围逐条

## 目标（本 cycle 的可独立验收主题）

**EC-05 自举收口**：让本轮的收口复检**跑得动、跑得对**。

## 实施清单

1. **WP-A**（收口资产）：断言集（36 条）+ 验证器（加载**自己**那份）。
2. **WP-B**（记录）：本文件 + RECHECK + GOAL 回写 / `ALL_PLAN`。
3. **WP-C**（门）：两树复检 → GOAL EC-05 回填 + 阶梯记账 → m0。

## 影响报告

- **产品代码**：**零改动**（本 cycle 只改收口资产与记录）。
- **判据面**：两处射程只增不删；既有判据一条未动。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**

## 残余与未覆盖

见 GOAL-080 的「残余与未覆盖范围」一节（`W-1`…`W-4`）与 RECHECK-494 的 `W-1`…`W-6`。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| 收口复检 | 见 RECHECK-496（本树全绿 + 两树 `TWO-TREE PASS`） | `uv run --frozen --no-sync python -B tools/verify_goal080_closeout.py --root . --verdict-only` |
| 两树复检 | 判词逐行相同 + `sha256` 一致 | `uv run --frozen --no-sync python -B tools/two_tree_recheck.py --script tools/verify_goal080_closeout.py --script-mode shared --root .` |
| 规模门 | 收口两脚本均过四道门 | `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_tooling_scripts_meet_product_gates.py -q` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-16 | IN_PROGRESS | cycle 5 建档（收口资产 + 两树 + 阶梯记账）。 |
| 2026-10-16 | DONE | 断言集 36 条 + 验证器落地；两树 PASS；EC-05 回填。 |
