---
id: RECHECK-20261018-525
slug: goal-086-ec05-self-bootstrap-closeout
title: GOAL-086 EC-05 自举收口 —— 验证器本树 + 两树同结论 + 阶梯记账
status: COMPLETED
result: PASS
created_at: 2026-10-18
updated_at: 2026-10-18
plan_id: PLAN-20261018-523
parent_goal: GOAL-20261018-086
owners:
  - root-agent
verify_paths:
  - tools/verify_goal086_closeout.py
  - tools/goal086_closeout_assertions.py
memory_entries: []
---

# RECHECK-20261018-525 — GOAL-086 EC-05

## 检查结果

### 1. 自举：验证器进树且**加载自己那份**断言集

- `tools/verify_goal086_closeout.py` + `tools/goal086_closeout_assertions.py` 都在树；
- `self-loads-its-own-assertions` 按**本文件名**推应载文件名（不写死）⇒ 自洽；
- 两处注册表**显式登记**（m0 的既有判据会判红）：
  `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的 `_VERIFIERS`
  与 `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`
  （后者恰好卡在 **450 行**硬上限 ⇒ 同轮压缩 docstring 腾出空间，**未删任何条目**）。

### 2. 本树判词

- `tools/verify_goal086_closeout.py --root . --verdict-only` ⇒ **66 条全绿**。
- 覆盖：分组键两档（`PHASE` / `TASK` 都必须在位）、`phase_id` 落库六面
  （端口 / 搬运 / 空串视同缺席 / sqlite 列 + `ALTER` / PG 读与写 / 迁移 `029`）、
  读面两键（`phase_id` 与 `scope`）、**9 条成对用例逐条在位**、3 份文件例数下界、
  3 份既有判据仍在树。

### 3. 阶梯记账（两个面）

- 宪章 `科研能力阶梯` 的**复检**行：`依据 GOAL` 已收录 `GOAL-20261018-086`；
  `下一级` 更新为「…+『同 phase 的评审者聚成一个小组、射程可读』；尚无判据证明两个模型在
  **同一个上游产物**上给出**不同判词**」——**下一格没动**（本 GOAL 补的是它的**前提**，
  不是它本身），如实写明。
- 宪章 `进展记录` 追加本 GOAL 一行，`RECHECK` 列指向本文件的 **cycle 1** 兄弟记录
  `RECHECK-20261018-524`。
- 程序表新增**序 54**（`GOAL-20261018-086`，轴 `质量`，能力域 `复检`）——
  预算 `max_goals: 55`，已用 **54**，**未触顶**。

### 4. 静态门与全量门

| 面 | 读数 |
| --- | --- |
| 新工具 `ruff check` / `ruff format --check` / `mypy` | 全绿（2 份文件） |
| 两处注册表判据 | **17 passed** |
| as-is m0 | **23/23**（终态行 `PASS: profile=m0; 23 deterministic checks`） |
| `tests/application tests/contracts tests/api` | **2411 passed, 77 skipped** |
| `tests/e2e` | **360 passed, 17 skipped** |
| 治理校验 | `Cursor 治理验证通过` |
| 凭据审计 | 四面 `offenders=0` |

### 5. 如实登记的一处**真红**（不掩盖）

首次 as-is m0 **判红两处**（`framework/validate` + `python/tests`）：一处是本 PLAN 的
「EC-05 不在本 cycle 射程」用了 `- [ ]`（治理判据要求 DONE 无未勾选项）；另一处是
GOAL-085 收口断言集的**两个文本锚点**随本轮代码形态迁移而失配。

第二处的处置已在本 GOAL 的 cycle 1 记录里**逐条申报**（`RECHECK-20261018-524`）：
两条锚点指向的**事实都仍然成立**，只是形态变宽；新锚点**更紧或更多**
（PG 只认 INSERT 段；分组键从 1 条拆成 2 条、两档都必须位在），判据条数 67 → **68**，
**只增不减**。⇒ 这是判据资产维护，**不是**放宽判据换绿。

## 结论

**PASS**。验证器 66 条本树全绿、阶梯两个面都收录本 GOAL、全量门 23/23 与宽面零回归
同时成立。EC-01…EC-05 全部达成 ⇒ 本 GOAL 收口。

**射程边界（重申，不夸大）**：本 GOAL **不声称**「两个模型在同一个上游产物上给出了不同判词」
（那仍是阶梯 `下一级`）；它证明的是**那个判据的前提今天成立** —— 同 phase 的评审者真的被
聚成一个小队，且射程在读面上可区分。
