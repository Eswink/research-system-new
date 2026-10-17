---
id: PLAN-20261016-505
slug: goal-081-ec05-self-bootstrap-closeout
title: GOAL-081 cycle 5 — 自举收口（EC-05）
status: DONE
created_at: 2026-10-17
updated_at: 2026-10-17
parent_goal: GOAL-20261016-081
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261016-506-goal-081-ec05-self-bootstrap-closeout.md
memory_entries: []
---

# PLAN-20261016-505 — GOAL-081 cycle 5

## 验收条件

- [x] 验证器进树（`tools/verify_goal081_closeout.py`）+ 本 GOAL 特有断言集
      （`tools/goal081_closeout_assertions.py`，**由验证器自己加载**）
- [x] 本树 `--verdict-only` 全 PASS（**66 条**）
- [x] 两树复检（`tools/two_tree_recheck.py`）判词逐行相同 + `sha256` 相同
- [x] as-is m0 **23/23**（`PASS: profile=m0; 23 deterministic checks`，在全部记录写入之后）
- [x] 治理绿（`validate.py` = `Cursor 治理验证通过`）
- [x] CI 台账逐提交（`cancelled` / rerun 如实登记 + 原因；自我指涉边界明写并封闭）
- [x] 残余与未覆盖范围逐条明写（GOAL `W-1`…`W-4` + 本节）

## 目标

**EC-05**：让本 GOAL 的收口**可被机器复检**，且复检本身**自举**（用本 GOAL 产出的工具跑
本 GOAL 的收口），两棵树给出**同一组判词**。

## 实施清单

1. **WP-A**：`tools/goal081_closeout_assertions.py` —— 本 GOAL 特有断言（例数下界、
   落点常量、**反编造门未被削弱**的四条既有断言、**并列结构**、live 读数归档）。
2. **WP-B**：`tools/verify_goal081_closeout.py` —— 标准断言集 + 本轮断言 + 记录面；
   自指两条（`self-loads-its-own-assertions` / `ladder-records-this-goal`）。
3. **WP-C**：两树复检 + as-is m0 + 治理 + CI 台账。

## 影响报告

- **产品代码**：零改动（本 cycle 只加收口资产）。
- **判据面**：新增两个 `tools/` 脚本（`tools/` 不在 ruff/mypy/规模四道门的产品根里
  ⇒ 它们自己由 `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的规范页判据覆盖）。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**

## 残余与未覆盖

- 本 GOAL 级残余见 GOAL 的「残余与未覆盖范围」：`W-1`（EC-05 自身在本轮跑之前是待办）、
  `W-2`（内容一致性无人判）、`W-3`（看到全文不在射程）、`W-4`（设计质量/臂数不在射程）；
- 本轮新增：**多跳跨相输入不做**、**两个执行体不消费声明输入**、**跨轮读数不可逐字复现**。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| 本树判词 | **66 PASS / 0 FAIL** | `uv run --frozen --no-sync python -B tools/verify_goal081_closeout.py --root . --verdict-only` |
| 两树复检 | 逐行相同 + `sha256` 相同（`COMPARE identical=True`） | `uv run --frozen --no-sync python -B tools/two_tree_recheck.py --script tools/verify_goal081_closeout.py --root . --script-mode shared --base-ref HEAD` |
| as-is m0 | **`PASS: profile=m0; 23 deterministic checks`** | `uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` |
| 治理 | `Cursor 治理验证通过` | `uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py` |

## 工程记忆

**无可复用事实**（本轮的收口资产自证；判据文件本身就是可复核的事实面，不另立记忆条目）。
