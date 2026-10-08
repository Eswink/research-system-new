---
id: MEM-20261008-209
title: "执行期要读「本 run 的程序归属」⇒ run 行必须先落库（程序面起 run 的写序与 HTTP 面相反）"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.95
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-341-goal-037-ec03-cross-run-knowledge-read-in.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-342-goal-037-ec03-cross-run-knowledge-read-in.md
supersedes: []
tags: [run-chain, write-order, program, goal-037]
---

## 做了什么

`research_state.read`（读本 run 所属程序内**前序 run** 的结论）的执行入口是 `run_id`
（`run_id_argument=True`，执行期注入）—— 它要先 `runs.get_run(run_id)` 反查出本 run 的
`program_id`。在程序面起 run 时我沿用了 HTTP 面的写序（**执行完再落行**），实测即刻红：

```
KeyError: "run not found: '610b8a57-…'"    # adapters/sqlite/run_store.py:66
```

原因：工具在**执行期**回读本 run 的行，而那一刻行还没写。

## 为什么这样做

两条路径的写序**必须**不同，因为消费者的时机不同：

- **HTTP 面**（`POST /projects/{id}/runs`）：没有执行期回读本 run 的消费者 ⇒ 执行后落行
  是最小改动（既有行为，**不动**）；
- **程序面**（`POST /programs/{id}/advance`）：读链工具在**执行期**要「本 run 的程序归属」
  这件事实 ⇒ **先落行**（`ResearchRun(id, project_id, protocol_id, program_id,
  program_index)`，状态 `DRAFT`）再执行，执行完再以真实终态覆盖。

**为什么先落行是「落 canonical」而不是「提前登记」**：`program_id` / `program_index` 本来
就要与 run 的写入同一次落库（GOAL-037 EC-01 的硬约束）；先落只是把**同一次写入**提到
执行之前，行本身仍是唯一真相（没有第二套状态）。

判据侧的取值口径（同轮实测）：读面给的是 `ReviewFinding.verdict` 的**值**（`PASS`），
不是逐字判词行（后者是 `findings` 数组，由 `review.read` 承载）—— 两条读面口径不同是
**有意**的。

## 怎么做与复现

```bash
# 复现（程序面起 run 的写序）：
uv run --frozen --no-sync python -B -m pytest \
  tests/e2e/test_cross_run_knowledge_on_the_run_path.py -q
# 不先落行 ⇒ 第 1 轮 execute 时 KeyError；先落行 ⇒ 6 passed
```

写新读链工具的清单（这次踩到的三条）：① 它的入口参数**在执行期**从哪来？
② 那个来源依赖的 canonical 行/事实**在那个时刻**已经落库了吗？③ 若没有 —— 是改工具
（换入口）、还是改写序（提前落行，且**不引入第二套状态**）？

## 适用边界

- 适用于**任何「执行期回读本 run（或本实体）自身行」**的能力 / 钩子。
- 不适用于「读的是别的实体」的情形（那里它的行本来就已经存在）。
- 反方向也要看：若把 HTTP 面也改成先落行，会改变既有行为（既有判据在**执行后落行**上
  取样）⇒ 除非有同样强的理由，否则**只改需要它的那条路径**并写明理由。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-341-goal-037-ec03-cross-run-knowledge-read-in.md`
- `.cursor/plans/rechecks/RECHECK-20261008-342-goal-037-ec03-cross-run-knowledge-read-in.md`
