---
id: PLAN-20261007-307
slug: goal-032-ec03-research-continuity-coverage
title: GOAL-032 cycle 3（EC-03）：研究连续性覆盖度矩阵 —— `rebuild_and_resume` 处理/不处理逐条实测 + 幂等读数 + 反证
status: DONE
created_at: 2026-10-07
updated_at: 2026-10-07
latest_recheck: .cursor/plans/rechecks/RECHECK-20261007-308-goal-032-ec03-research-continuity-coverage.md
memory_entries:
  - continuity-coverage-is-a-matrix-not-a-claim
parent_goal: GOAL-20261007-032
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261007-032 的 **EC-03**（研究连续性）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**不新建机制**（只把既有机制的**覆盖度**
    落成判据；需要新机制的部分如实登记为下一轮输入）；**不改既有判据**
    （`test_restart_rebuild_resume.py` / `test_retry_park_and_resume.py` /
    `test_workflow_restart_recovery.py` 一字未动 —— 本 PLAN 只**新增**一个互补文件）；
    **不得**宣称 exactly-once（口径只能是 at-least-once + idempotency + deduplication）。
objective: >-
    把 `services/api/run_resume.py::rebuild_and_resume` 的**真实覆盖度**从建档勘察的
    散文读数推进到**判据**：① 处理面（自包含重建 / 来源依赖重建 / 两类早退拒绝 /
    preflight 与语义漂移拒绝）引用既有判据；② 本文件补上既有判据没有的四种**边界**读数
    —— 重启后重排到期的自动派发（守护线程 pass 真跑到终态）、租约过期（任务级恢复 ⇒
    `QUEUED` ⇒ 可再交付）、**死信不被续跑捞回**（点名拒绝 ⇒ 人工恢复才可交付）、
    已成功任务**不重跑**（attempt 与契约交付计数的直接读数）；③ 反证：把「已成功 ⇒
    跳过」的判据条件改坏 ⇒ 判红。
exit_criteria:
  - id: AC-1
    criterion: >-
      **覆盖度矩阵逐条**：① 处理面（四项）由既有判据承载（本 PLAN **只引用**，逐条点名
      文件与用例名）；② 本文件新增四条边界读数（自动派发 / 租约过期 / 死信不捞 /
      已成功不重跑），每条都是**实测**（真 SQLite + 真编排 + 注入时钟）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_research_continuity_coverage_matrix.py
      tests/e2e/test_restart_rebuild_resume.py tests/e2e/test_retry_park_and_resume.py
      tests/e2e/test_workflow_restart_recovery.py tests/e2e/test_retry_dispatch_full_loop.py -q`
      ⇒ 全绿（新文件 4 例；既有四文件一字未改）。
    status: PASS
  - id: AC-2
    criterion: >-
      **幂等读数（不重跑）**：重建续跑前后，已成功任务的 `attempt` **不动**、该契约的
      交付次数**仍为 1**（不是只看最终状态）。
    verify: >-
      新文件的 `test_a_rebuild_does_not_deliver_already_finished_work`。
    status: PASS
  - id: AC-3
    criterion: >-
      **反证**：把 `_remaining_specs` 的「已 `SUCCEEDED` ⇒ 跳过」条件改坏（`if False`）⇒
      幂等判据判红；复原后 raw `sha256` 回到基线。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal032-cycle3-press.py` ⇒
      `PRESS_RED 1 failed` / `RESTORED True` / `FINAL_MATCHES_BASELINE True`；
      留档 `scratch/goal032-cycle3/press-matrix.log`（CR=0）。
    status: PASS
  - id: AC-4
    criterion: >-
      **不凑数**：需要新机制的部分（死信恢复后 run 的**自动**继续；task 级与 run 级
      入口的自动协同）**如实登记为下一轮输入**，本轮不实现。
    verify: >-
      本文件与 `RECHECK-20261007-308` 的「残余」节；GOAL 的「下一轮输入」列。
    status: PASS
  - id: AC-5
    criterion: >-
      **门与既有判据不动**：`ruff check` / `ruff format --check` / `mypy` / 规模门绿；
      `git diff --numstat` 对本 PLAN 涉及的文件**只新增**（零改动既有判据文件）。
    verify: >-
      四道门读数 + `git status --short` 读数。
    status: PASS
---

# PLAN-20261007-307 — GOAL-032 cycle 3（EC-03）：研究连续性覆盖度矩阵

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-5）。

## 实施清单

| # | 项 | 交付 |
| --- | --- | --- |
| WP-1 | 边界判据（新增） | `tests/e2e/test_research_continuity_coverage_matrix.py`（4 例） |
| WP-2 | 反证 | `scratch/goal032-cycle3-press.py` + 留档（`service.py` 的跳过条件改坏） |
| WP-3 | 覆盖度表 | 本文件与 RECHECK 的「覆盖度逐条」节（处理/不处理两面） |

## 证据

- **判据读数**：新文件 **4 passed**；与既有四个连续性套件合跑全绿（读数见 RECHECK）。
- **反证留档**：`scratch/goal032-cycle3/press-matrix.log`（175 B、CR=0）：
  `GUARD 1 passed` / `PRESS_RED 1 failed` / `RESTORED True` / `FINAL_MATCHES_BASELINE True`。
- **门**：`ruff check` = `All checks passed!`；`ruff format --check` = 干净；规模门 **1131 passed**。
- **既有判据零改动**：本 PLAN 未触碰四个既有连续性判据文件。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-07 | IN_PROGRESS | cycle 3 开工：按建档勘察的覆盖度表写边界判据。 |
| 2026-10-07 | DONE | 五条 AC 全 PASS（`RECHECK-20261007-308` = PASS_WITH_WARNINGS）。 |

## 影响报告

- **Domain/API/schema**：零改动（只新增判据与记录）。
- **安全/凭据**：零影响。
- **兼容性/迁移**：零影响。
- **上游版本**：零影响。
- **下一项任务**：cycle 4 = EC-04（自举收口）。
