---
id: MEM-20260923-108
title: "两条失败收敛路径必须同步（实测缺口）：执行期抛 ValueError 的路径从事件链补回冻结引用，**优雅**收敛（任务结果登记失败 / 验收门拒收）的路径不补 ⇒ 冻结过的 run 被判成「从未冻结」"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.95
review_after: 2027-09-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260922-138-real-experiment-chain-via-m12.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-139-goal-011-closeout-recheck.md
supersedes: []
tags:
  - canonical-state
  - failure-path
  - run-read-face
---

# 冻结引用在两条失败路径上必须一致（GOAL-011 cycle 10 修复）

## 做了什么

`services/api/run_execution.py::run_from_execution` 此前只在 `except ValueError` 分支里
从事件链补回冻结引用（`frozen_manifest_refs_of(...).apply(...)`）。**优雅**收敛——任务结果登记
失败（`register_and_gate` 返回字符串）、验收门拒收（`failure_step(system_failure=False)`）——走的是
`deps.fail(...)`（`PhaseRunner.fail` / `PackageRunService._fail_run`）直接返回 `RunOutcome`，
**只带语义 digest、不带字节 digest** ⇒ canonical 行的 `manifest_digest` 是 `None`。

现在统一：结局行缺字节 digest 就从**同一份事件链记录**补回（`_with_frozen_refs`），
未冻结的 run（preflight 被拒）拿到空引用 ⇒ 两个 digest 保持 `None`（不伪造）。

## 为什么这样做

- **读面把两者讲成同一句话**：`rebuild.status = REFUSED` + `missing=[manifest_digest]`
  与 `assert_semantics_frozen` 的「frozen manifest lacks a semantic digest」都读成
  「这条 run 没冻结过」——而它**冻结过**（`manifest.frozen` 事件就在链上）。AGENTS §6
  canonical state 要求行就是真相，缺它不是「更保守」，是**记错**。
- **判据是成对写的**：`tests/api/test_failed_run_semantic_digest_api.py` 里
  「冻结过 ⇒ 带两个 digest」与「从没冻结 ⇒ 两个都是 None」是成对的；修复必须让这两条**同时**成立。

## 怎么做与复现

1. 复现（修前）：本机 `run_ready_client` + `real_retrieval_research_v1.yaml` 起一条 run
   ⇒ `state=FAILED`、`manifest_digest=None`、`manifest_semantic_digest=sha256:…`、
   `rebuild={'status':'REFUSED','missing':['manifest_digest']}`。
2. 判据：`tests/api/test_failed_run_semantic_digest_api.py::test_a_graceful_failure_still_carries_the_frozen_refs`
   （**先红后绿**已实测：暂存修复 ⇒ 只有这条红、其余 9 条仍绿 ⇒ 修复射程恰好是优雅收敛路径）。
3. 判据要用**产品缝**（`run_ready_client` 起真实 run），不要手搓 `RunOutcome`——否则钉的是
   自己拼的字段，不是那条路径。

## 适用边界

- 修的是**行**（canonical），不改变任何**行为**：终态、判词、预留释放（`_fail_run` 仍然释放）
  都不变——所以它**不**能让「失败 run 预留可见」那类夹具重新变绿（那是另一件事）。
- 50 行函数上限会咬人：这次的改法是抽 `_digest_or_none`（两处三元收敛成一行）+
  `_with_frozen_refs`（一句话的调用点），把 `run_from_execution` 从 57 行压回 50 以内。

## 来源

- `services/api/run_execution.py`（`_digest_or_none` / `_with_frozen_refs`）；
  `RECHECK-20260922-139`；对偶见 [[fixture-failure-shape-is-a-contract]]。
