---
id: RECHECK-20261018-528
slug: goal-087-ec05-self-bootstrap-closeout
title: GOAL-087 EC-05 自举收口 —— 验证器本树 + 两树同结论 + 阶梯记账
status: COMPLETED
result: PASS
created_at: 2026-10-18
updated_at: 2026-10-18
plan_id: PLAN-20261018-526
parent_goal: GOAL-20261018-087
owners:
  - root-agent
verify_paths:
  - tools/verify_goal087_closeout.py
  - tools/goal087_closeout_assertions.py
memory_entries: []
---

# RECHECK-20261018-528 — GOAL-087 EC-05

## 检查结果

### 1. 自举：验证器进树且**加载自己那份**断言集

- `tools/verify_goal087_closeout.py` + `tools/goal087_closeout_assertions.py` 在树；
  `self-loads-its-own-assertions` 按**本文件名**推应载文件名 ⇒ 自洽；
- 两处注册表显式登记：`_VERIFIERS` 与 `IN_SCOPE`（后者恰好卡在 **450 行**硬上限 ⇒
  同轮压缩 docstring 腾出空间，**未删任何条目**）。

### 2. 本树判词

- `tools/verify_goal087_closeout.py --root . --verdict-only` ⇒ **60 条全绿**。
- 覆盖：声明面（`review_panel` 键 + 唯一取值 + 视图属性 + **两个既有值仍在**）、
  接线（`record_rejection` / `panel_rejection` / `panel_plan` 门）、可见性
  （平票 `dissent` + 逐条点名 + `verdict` 参数）、**射程隔离**（组末只认本模块记账的判负 +
  `CONTINUE` 容忍语义未动）、3 条成对用例在位 + 例数下界 + 3 份既有判据仍在树。

### 3. 两树复检

- `TREE current` 与 `TREE clean` 各 **60 条判词**，`sha256` **完全相同**
  （`0ede4637d72de5ed…`）⇒ `COMPARE identical=True` / `TWO-TREE PASS`。
- 判词归档：`GOAL-20261018-087-ec05-{current,clean}.txt` 各 **2422 bytes / CR=0 / 60 行**，
  二进制写盘、逐字节相同。

### 4. 阶梯记账（两个面）

- 阶梯 **复检** 行：`依据 GOAL` 收录 `GOAL-20261018-087`；`下一级` 更新为
  「…+『一位判负不取消同批、分歧逐票可读』；尚无判据证明两个模型在**同一个上游产物**上
  给出**不同判词**」—— 下一格**没动**（本 GOAL 补的是它的**第二个前提**），如实写明。
- 宪章 `进展记录` 追加本 GOAL 一行（`RECHECK` 列指向 cycle 1 的 `RECHECK-20261018-527`）。
- 程序表新增**序 55**（轴 `质量`、能力域 `复检`）⇒ 预算 `max_goals: 55`，已用 **55**，
  **本轮触顶**（宪章规则：触顶即做战役级核算 —— 已在交付报告里登记）。

### 5. 静态门与全量门

| 面 | 读数 |
| --- | --- |
| 新工具 `ruff check` / `format` / `mypy` | 全绿（2 份文件） |
| 两处注册表判据 | **17 passed** |
| 宪章三条判据 | **20 passed** |
| as-is m0 | **23/23**（终态行 `PASS: profile=m0; 23 deterministic checks`） |
| `tests/application tests/contracts tests/api` | **2411 passed, 77 skipped** |
| `tests/e2e` | **363 passed, 17 skipped** |
| 治理校验 | `Cursor 治理验证通过` |
| 凭据审计 | 四面 `offenders=0` |

### 6. 如实登记的两处**真红**（不掩盖）

1. **cycle 1 首轮**：组末判定误把 `on_task_failure: CONTINUE` 的被容忍失败算成判负 ⇒
   `test_failure_policy_consumer.py` 的**三处**既有用例同时变红。已按「只认本模块记账的
   判负」修正（`RECHECK-20261018-527` 逐条登记）。
2. **收口轮首跑**：`python/tests` 判红 —— `phase_runner._run_group_task` 涨到 **54 行**
   （超 50 行门）。处置：把成功记账搬进 `review_panel_judging`（与判负、组末判定同处），
   `phase_runner` 回到 **440 行**、无超长函数；**未删任何逻辑、未改任何判据**。

## 结论

**PASS**。验证器 60 条本树全绿、两树逐行相同且 `sha256` 一致、as-is m0 **23/23**、
宽面零回归同时成立。EC-01…EC-05 全部达成 ⇒ 本 GOAL 收口。

**射程边界（重申，不夸大）**：本 GOAL **不声称**「两个模型真的给出了不同判词」——
它证明的是那个判据的**第二个前提**今天成立：一位评审者判负**不再**让同批其他人不跑，
分歧因此**可以出现**，并且**逐票可读**（含平票）。
