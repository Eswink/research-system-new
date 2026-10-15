---
id: PLAN-20261015-485
slug: goal-079-ec05-self-bootstrap-closeout
title: GOAL-079 cycle 5 — 自举收口 + 修掉一处收口资产同族缺陷（EC-05）
status: DONE
created_at: 2026-10-15
updated_at: 2026-10-15
parent_goal: GOAL-20261015-079
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-486-goal-079-ec05-closeout-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20261015-222-four-decisions-when-a-hardcoded-value-becomes-declared.md
  - .cursor/memory/entries/MEM-20261015-223-closeout-assets-need-ownness-not-just-self-consistency.md
---

# PLAN-20261015-485 — GOAL-079 cycle 5

## 验收条件

- [x] **同族缺陷修复**：`verify_goal078_closeout.py` 自洽地加载上一轮断言集 ⇒ 改回自己那份
- [x] 家族判据加**第三项对拍**（实载 == 自己那份）+ 一条反向反例
- [x] 按压 `V9-8` 两处红 + 逐字节复原（判词归档进树、`CR=0`）
- [x] 本 GOAL 的收口资产进树（断言集 + 验证器）
- [x] 两处射程**纯收紧**（`IN_SCOPE` / `_VERIFIERS`）
- [x] GOAL 补「残余与未覆盖范围」一节（验证器的 `residuals-enumerated` 判词驱动）
- [x] 两树复检（判词归档进树、二进制写盘、`CR=0`、`sha256` 一致）
- [x] as-is m0 23/23（**在全部记录写入之后**）+ 治理绿 + 凭据审计四面零命中
- [x] 阶梯记账（宪章 `进展记录` 追加本行 + 「实验」域依据面收录本 GOAL）

## 目标（本 cycle 的可独立验收主题）

**EC-05 自举收口**：让本轮的收口复检**跑得动、跑得对**——验证器进树、两树同结论、
m0 在记录之后、阶梯记账成立。

## ★ 本 cycle 抓到的**真缺陷**（读收口资产时实测出来的）

**症状**：`tools/verify_goal078_closeout.py` 的 `ASSERTIONS` 常量与 `_load_assertions()`
**双双**写着 `goal077_closeout_assertions.py`。

**后果（三条，逐条实测）**：

1. 「声明 == 实载」**成立** ⇒ 首版家族判据放行；
2. `goal078_closeout_assertions.py` 的 **29 条自有断言从未运行** —— 在 GOAL-078 的
   收口复检归档（73 条判词）里这些名字**零命中**；
3. 该验证器自己的 `self-loads-its-own-assertions` 判词**恒绿**：它问的是
   「`'goal077_closeout_assertions.py"'` 这个串在不在加载函数里」，而写的名字**恰好就是
   当时实载的那个**。

这是 GOAL-038/039/040 那条历史缺陷的**第二例**（形态不同：那一轮是「声明自己的、
加载别的」，本轮是「**自洽地**加载上一轮」）。

**处置（三处，都不放宽任何既有判据）**：① 两个位置都改回自己那份（现在真跑 29 条，
本树 0 判负）；② 自指判词**按本文件名推**应载文件名（写死的那版在构造上不可能再通过）；
③ 家族判据加第三项对拍 + 反向反例。

## 实施清单

1. **WP-A**（修缺陷）：`verify_goal078_closeout.py` 两处 + 家族判据 + `V9-8` 按压归档。
2. **WP-B**（本轮收口资产）：`tools/goal079_closeout_assertions.py` +
   `tools/verify_goal079_closeout.py` + 两处射程登记 + GOAL 残余节 + 本记录 + `ALL_PLAN`。
3. **WP-C**（收口）：两树复检 → GOAL EC-05 回填 + 状态历史 + 阶梯记账（进展行 + 归档最早一条）。

## 影响报告

- **产品代码**：**零改动**（本 cycle 只改收口资产与判据）。
- **读面 / DTO / 路由 / 快照**：零改动。
- **判据面**：家族判据**加强**（加第三项对拍 + 反向反例，既有断言一条未删）；
  两处射程**纯收紧**（只增不删）。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**

## 残余与未覆盖

- 旧一代验证器（`LEGACY_INLINE`：断言内联、无外部断言集）没有可对拍面 ⇒
  是否存在同族问题**未普查**（GOAL `W-6`，如实登记）；
- 本 GOAL 其余残余见 GOAL 的「残余与未覆盖范围」一节（`W-1`…`W-6`）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| 缺陷修复 | 078 验证器现在真跑 29 条自有断言、本树 0 判负；**73 → 68** 是**旧归档**的读数（那份归档跑的是上一轮断言集） | `uv run --frozen --no-sync python -B tools/verify_goal078_closeout.py --root . --verdict-only` |
| 家族判据 | **9 passed**（含新反例） | `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_closeout_verifiers_run_their_own_assertions.py -q` |
| 按压 `V9-8` | 家族判据**红** + 该验证器 `self-loads-its-own-assertions` **FAIL**；`sha 复原一致=True` | `uv run --frozen --no-sync python -B scratch/goal079c5_press.py` |
| 本 GOAL 收口复检 | 见 RECHECK-486（两树 `TWO-TREE PASS`） | `uv run --frozen --no-sync python -B tools/two_tree_recheck.py --script tools/verify_goal079_closeout.py --script-mode shared --root .` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | IN_PROGRESS | cycle 5 建档（EC-05 收口 + 已实测到的同族缺陷修复）。 |
| 2026-10-15 | DONE | 三处修复落地；按压 `V9-8` 两处红且逐字节复原；本 GOAL 收口资产进树；两树 PASS。 |
