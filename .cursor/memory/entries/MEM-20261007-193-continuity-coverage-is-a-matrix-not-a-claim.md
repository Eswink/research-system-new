---
id: MEM-20261007-193
title: "研究连续性是一条**覆盖度矩阵**，不是一句「能续跑」：处理面写在既有判据里，不处理面要自己补读数（死信不被捞回 = 与人工恢复的交界）"
status: ACTIVE
created_at: 2026-10-07
updated_at: 2026-10-07
scope: repository
confidence: 0.9
review_after: 2027-04-07
source_plans:
  - .cursor/plans/tasks/PLAN-20261007-307-goal-032-ec03-research-continuity-coverage.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261007-308-goal-032-ec03-research-continuity-coverage.md
supersedes: []
tags: [research-continuity, resume, coverage-matrix, dead-letter-boundary, goal-032, plan-307]
---

## 做了什么

`services/api/run_resume.py::rebuild_and_resume` 是 **run 级**入口。GOAL-032 cycle 3 把它的
覆盖度落成一张**八行矩阵**（每行都有判据），其中四行是**既有判据已经承载的"处理面"**，
四行是**必须自己补的边界读数**：

| 面 | 谁承载 |
| --- | --- |
| 自包含重建 / 来源依赖重建 / 两类早退拒绝 / digest 与语义漂移拒绝 | **既有**判据（`test_restart_rebuild_resume.py` / `test_rebuild_readiness.py`） |
| 重启后重排到期 ⇒ **自动派发** | 新增（跑 `RetryDispatchScheduler.run_once`） |
| 租约过期（**任务级**，不属本入口） | 新增（`recover_expired_leases` ⇒ `QUEUED`） |
| **死信任务** ⇒ **不处理**（点名拒绝） | 新增（续跑必经的 `acquire_lease` 拒它） |
| 已成功任务 ⇒ **不重跑** | 新增（`attempt` 与契约交付计数的直接读数） |

## 为什么这样做

- 「能续跑」是一句**关于处理面**的话；运维真正要问的是**边界**：「哪些情形**不会**被它
  处理？」—— 边界不写出来，故障时就会把「应该人工处置」误读成「系统会自己好」。
- **别把"处理面"再写一遍**：既有四个 e2e 判据已经把四条处理路径钉死；重复实现只会造出
  第二个会漂移的真相。**引用 + 补边界**才是互补。
- **「不处理」的最佳代表是死信**：`_remaining_specs` 只跳过 `SUCCEEDED` 一条 ⇒ 结构上其余
  状态都进 `remaining` 并交给 `acquire_lease` 判 —— 死信恰好是"进得了 remaining、
  但过不了交付面"的那一类（`terminal()` 守卫）。它与 EC-01 的**人工恢复**构成交界：
  续跑不捞它，**人工**才捞。
- **幂等要量计数不要看状态**：「重建后没重跑」若只看最终状态串，一次静默重跑也能判绿；
  量 `attempt` 不动 + 契约交付数仍为 1 才是直接读数。

## 怎么做与复现

- **先读入口的代数**：`rebuild_and_resume` → `resume_rebuilt` → `_remaining_specs`
  （跳过 `SUCCEEDED`）+ `assert_semantics_frozen`；`rebuild_readiness` 给记录够不够重建。
- **区分 run 级与 task 级**：`run_resume` 只管 run；租约过期是**任务级**
  （`recover_expired_leases`）；两者不要混成一句"恢复"。
- **接线边界要写明**：守护线程那一例用「durable 行重建上下文 → `resume_rebuilt`」两步接
  `rebuild` 面（与 `services/api/app.py::_rebuild` 同形）；`run_resume` 的**来源解析层**
  需要完整 `ApiDeps`，由 `tests/api/test_run_source_and_rebuild_api.py` 覆盖。
- 复现：`uv run --frozen --no-sync python -B -m pytest
  tests/e2e/test_research_continuity_coverage_matrix.py -q` ⇒ 4 passed；
  反证 `uv run --frozen --no-sync python -B scratch/goal032-cycle3-press.py`
  （把 `_remaining_specs` 的跳过条件改成 `if False` ⇒ 幂等判据判红）。

## 适用边界

- 本仓的 **run 级续跑 / 重排派发 / 租约过期**面适用；**跨进程**重启的取证在本轮是
  「本进程 pass + 替身替换来源解析层」（`W-1`），真正的跨进程产品路径由
  `tests/api/test_run_source_and_rebuild_api.py` 承载。
- 「不处理」清单**有界**：本轮没做穷尽的状态组合分类（`W-4`）；死信是代表，不是全部。
- **死信恢复与 run 级续跑的自动协同不存在**（`W-2`）：恢复任务后若要 run 继续，
  仍需人工 `POST /runs/{id}/resume`。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261007-307-goal-032-ec03-research-continuity-coverage.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261007-308-goal-032-ec03-research-continuity-coverage.md`
- 判据：`tests/e2e/test_research_continuity_coverage_matrix.py`（新增）+
  `tests/e2e/test_restart_rebuild_resume.py` / `test_retry_park_and_resume.py` /
  `test_workflow_restart_recovery.py`（既有，引用）
- 实现：`services/api/run_resume.py`、`packages/application/run_orchestration/service.py`
  （`_remaining_specs` / `resume_rebuilt`）、`services/api/scheduler.py`（`RetryDispatchScheduler`）
