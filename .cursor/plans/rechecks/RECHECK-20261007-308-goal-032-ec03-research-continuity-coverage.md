---
id: RECHECK-20261007-308
slug: goal-032-ec03-research-continuity-coverage
title: 复检：GOAL-032 EC-03 研究连续性覆盖度矩阵（四条边界读数 + 幂等 + 反证）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-07
updated_at: 2026-10-07
plan_id: PLAN-20261007-307
reviewer: root-agent
parent_goal: GOAL-20261007-032
verify_paths:
  - >-
    uv run --frozen --no-sync python -B -m pytest
    tests/e2e/test_research_continuity_coverage_matrix.py -q ⇒ 4 passed（新文件）
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/e2e/test_restart_rebuild_resume.py
    tests/e2e/test_retry_park_and_resume.py tests/e2e/test_workflow_restart_recovery.py
    tests/e2e/test_retry_dispatch_full_loop.py -q ⇒ 全绿（既有四文件；本 PLAN 一字未改）
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261007-032 的 EC-03。**不新建机制**（只把既有机制的覆盖度落成判据）；
    **不改既有判据**；**不得**宣称 exactly-once（**明确否认**）。
---

# RECHECK-20261007-308：GOAL-032 EC-03 研究连续性覆盖度

## 覆盖度逐条（处理 / 不处理；都为**实测**读数）

| 情形 | 判定 | 证据 |
| --- | --- | --- |
| run 级重建（有冻结正文 ⇒ **自包含**，不碰外部来源） | **处理** | `test_restart_rebuild_resume.py::test_a_rebuild_from_the_frozen_body_finishes_the_remaining_work`（既有，引用） |
| 无冻结正文 ⇒ 依赖来源仍可解析 | **处理** | 同文件 `::test_a_restarted_process_finishes_a_parked_run_from_its_recorded_source`（既有） |
| 旧 run（无来源登记）⇒ 早退拒绝 | **处理（点名拒绝）** | `test_rebuild_readiness.py`（既有，分类器读数） |
| 冻结 digest 不符 / 语义漂移 ⇒ 拒绝 | **处理（点名拒绝）** | `test_restart_rebuild_resume.py::test_a_rebuild_rejects_a_frozen_digest_that_does_not_match` / `::test_a_drifted_catalog_is_rejected_by_the_semantic_check`（既有） |
| **重启后重排到期 ⇒ 自动派发** | **处理** | **本 PLAN 新增** `::test_a_parked_run_is_actually_finished_by_the_retry_dispatch_pass`（跑 `RetryDispatchScheduler.run_once` ⇒ `dispatched == 1` 且 run 收敛 `SUCCEEDED`、`execution_attempts == 2`） |
| **租约过期** | **处理**（任务级，**不属** `rebuild_and_resume`） | **本 PLAN 新增** `::test_an_expired_lease_is_recovered_to_queued_and_redeliverable`（`recover_expired_leases() == 1` ⇒ `QUEUED` ⇒ 再交付同一 task_id） |
| **死信任务** | **不处理**（点名拒绝） | **本 PLAN 新增** `::test_a_dead_letter_is_not_recovered_by_the_resume_path`（续跑必经的 `acquire_lease` 抛 `InvalidInputError` 且消息含 `terminal`；`requeue` 之后才可交付 —— 与 EC-01 的交界） |
| **已成功任务** | **不重跑**（幂等） | **本 PLAN 新增** `::test_a_rebuild_does_not_deliver_already_finished_work`（重建前后 `attempt == 1` 不变、`runtime.contract_of.count("sort_analysis_execution") == 1`） |

## 检查结果

五条 AC 逐条实测：

1. **覆盖度矩阵（AC-1）**：上表八行逐条有证据；处理面的四项**引用**既有判据（不重复实现），
   不处理面的四项由**本 PLAN 新增**的四条边界读数承载 ⇒ 两文件**互补而非重复**
   （既有判据判"这条路走得通"，本文件判"边界在哪"）。
2. **幂等读数（AC-2）**：判据量的是 **`attempt` 与契约交付计数**这两个直接读数
   （不是只看状态串）——「零第二次副作用」的机械形态。
3. **反证（AC-3）**：`SCRATCH` 反证把 `_remaining_specs` 的「已 `SUCCEEDED` ⇒ 跳过」
   改成 `if False` ⇒ `PRESS_RED 1 failed`（幂等判据判红：已完成任务被再交付）⇒
   `RESTORED True` / `FINAL_MATCHES_BASELINE True`。留档 CR=0。
4. **不凑数（AC-4）**：见下「残余」。
5. **门（AC-5）**：`ruff check` / `ruff format --check` / `mypy` / 规模门 **1131 passed**；
   本 PLAN 未触碰既有四个连续性判据文件（`git status --short` 逐条核对）。

**接线边界（如实写明）**：守护线程那一例用「durable 行重建上下文 → `resume_rebuilt`」两步
接 `rebuild` 面（与 `services/api/app.py` 的 `_rebuild` 同形）；`run_resume` 的**来源解析层**
（冻结正文/路径/草稿）需要完整 `ApiDeps`，由 `tests/api/test_run_source_and_rebuild_api.py`
覆盖（本文件不重复）。

## 警告（如实登记）

- **`W-1`｜守护线程的自动派发只在**单进程**里取证**：`RetryDispatchScheduler` 的 pass 在
  本进程内跑（真 SQLite + 注入时钟）。**跨进程**的「重启后无人值守」由
  `has_paused_context` 缺席 + `_can_rebuild`（run 行有来源）两支共同决定 —— 后者的
  **产品路径**（真 `ApiDeps` 的来源解析）在本文件里被替身替换（见「接线边界」）。
- **`W-2`｜死信恢复与 run 级续跑的**自动协同**不存在**：`requeue` 只把**任务**放回可交付面；
  若 run 已停在 `FAILED`（终态），要它继续跑仍需**人工** `POST /runs/{id}/resume`。
  这条协同属**新机制**，本轮**只登记**（GOAL 的「下一轮输入」列）。
- **`W-3`｜`recover_expired_leases` 的 LOST-worker 支**未在本文件覆盖：本文件只测
  「租约过期」这一支；LOST-worker 支由 `tests/distributed/` 与 PG 侧既有判据承载
  （M16 面，不在 EC-03 射程）。
- **`W-4`｜「不处理」清单是有界的**：上表只列了建档勘察与既有判据覆盖到的情形；
  真正的穷尽需要一份**分类面**（哪些 task/run 状态组合可被续跑捞回），本轮**没有**做那个
  穷尽枚举（`_remaining_specs` 只跳过 `SUCCEEDED` 一条 ⇒ 结构上其余状态都进 `remaining`
  并交给 `acquire_lease` 判 —— 本文件用死信作为那个形态的代表，**不是**枚举全部）。
- **`R-M1` 未收口**（不得宣称项目安全）；**投递语义仍非 exactly-once**（**明确否认**；
  口径只能是 at-least-once + idempotency + deduplication —— 本条同时是
  `test_delivery_semantics_wording.py` 的规则文本面要求）。

## 结论

`PASS_WITH_WARNINGS`。五条 AC 全 PASS；`W-1`…`W-4` 如实登记。**未**新建机制；
**未**改既有判据；**不得**宣称投递语义为「恰好一次」（**明确否认**；
口径只能是 at-least-once + idempotency + deduplication）。
