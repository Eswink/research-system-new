---
id: MEM-20261005-185
title: "判据的射程也要按压取证：只扫 ast.Name 会看不见属性调用式写入 ⇒ 「先判后写」在守卫被挪位后仍假绿"
status: ACTIVE
created_at: 2026-10-05
updated_at: 2026-10-05
scope: repository
confidence: 0.95
review_after: 2027-04-05
source_plans:
  - .cursor/plans/tasks/PLAN-20261005-279-goal-029-ec03-write-capability-canonical-path.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261005-280-goal-029-ec03-write-capability-canonical-path.md
supersedes: []
tags: [verdict-shape, ast-inspection, press-test, goal-029, plan-279, false-green]
---

## 做了什么

GOAL-029 EC-03 的「先判后写」判据首版是这样写的：进入 `persist_completion` 后收集
**裸名调用**（`ast.Name`）的顺序，断言 `_succeeded_run` 是第 0 个。按压（把守卫从第一条
语句挪到 `persistence.experiment_store.save_audit(truth.audit)` **之后**）时 —— **判据仍然全绿**。

根因：`save_audit` / `save_run` 这类写入是**属性调用**（`x.y.method(...)`，AST 里是
`ast.Attribute`），首版只认 `ast.Name` ⇒ **它们在扫描里根本不存在** ⇒ 守卫是不是第一步
无从判断。改为**语句级**顺序（逐语句收集 guard / write 的行号，比对 `min(guard) < min(write)`）
后，同一按压立刻判红。

## 为什么这样做

「判据写出来了」与「判据咬得住」是两件事。EC-03 的对象是**旁路风险**，而这类风险的判据
天然容易写成「看一眼源码里的调用名」—— 那对**调用形态**敏感：换个写法（属性调用、
`getattr`、包装函数、`functools.partial`）就会从射程里消失，而判据不会报错，只会**假绿**。

同族教训在本仓已有多条（`MEM-20260922-156` 受判面非空 / `MEM-20260922-159` 反证两向 /
`MEM-20260922-160` 不得靠并集掩蔽）：它们都指向同一件事 —— **判据的射程要显式，且要按压**。

## 怎么做与复现

- **扫调用点/顺序时优先按 AST 的「语句」与「完整调用表达式」判**，不要只认 `ast.Name`：
  属性调用是本仓的主流写法（`store.save_plan(...)`、`persistence.experiment_store.save_audit(...)`）。
- **每条新判据至少做一次按压**：把被测顺序/存在性**真的破坏一次**，确认判据红；再复原，
  确认 `sha256` 逐字节一致且复绿。EC-03 的按压记录在 `RECHECK-20261005-280` 的 P-1（未咬住）
  与 P-2（加固后咬住）。
- 复现：`uv run --frozen --no-sync python -B -m pytest
  tests/architecture/python/test_deliverable_write_stays_on_the_canonical_path.py -q -p no:randomly`；
  按压（把 `_succeeded_run` 移到 `save_audit` 之后）⇒ `test_the_guard_precedes_the_write` 红。

## 适用边界

本仓所有**结构判据**（AST 扫调用点 / 顺序 / 存在性）都适用，尤其是判「唯一入口」「先判后写」
「只有一处」这类**排他性**断言 —— 排他性断言对射程最敏感：扫描面漏掉一种写法，结论就反转。
**不**适用于行为判据（真跑一遍看结果的那种）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261005-279-goal-029-ec03-write-capability-canonical-path.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261005-280-goal-029-ec03-write-capability-canonical-path.md`
  （P-1 未咬住 / P-2 加固后咬住）
- 事实：`packages/application/m12_reference/persistence.py::persist_completion` 的实际调用形态
