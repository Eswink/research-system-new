---
id: PLAN-20261018-526
slug: goal-087-ec01-04-a-rejecting-reviewer-does-not-cancel-the-panel
title: GOAL-087 cycle 1 — 判负不取消同批评审 + 全体判完再判（EC-01…EC-04）
status: DONE
created_at: 2026-10-18
updated_at: 2026-10-18
parent_goal: GOAL-20261018-087
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-527-goal-087-a-rejecting-reviewer-does-not-cancel-the-panel.md
memory_entries: []
---

# PLAN-20261018-526 — GOAL-087 cycle 1

## 验收条件

- [x] **EC-01**：两位评审者一负一过 ⇒ 两条判词都落库、`panels` 一条且 `voters == 2`、
      `dissent` 点名少数意见的目标与 verdict；run 终态仍 `FAILED`。
- [x] **EC-02**：该语义**只在显式声明时**生效；未声明 ⇒ `records == 1`、`panels == []`
      （与今天逐字相同）。
- [x] **EC-03**：失败消息逐条点名每位评审者的目标与 verdict；全体判过 ⇒ `SUCCEEDED` 且
      advisory 是多数票。按压：第二位也判负 ⇒ `dissent == []`、`advisory == "REJECT"`。
- [x] **EC-04**：`tests/e2e` 与 `tests/application` 全量零回归；既有面板判据逐字保留。
- [x] **EC-05 不在本 cycle 的射程**（收口 cycle 的交付物）。

## 目标

让「分歧」在产品上**有可能发生**：先让全体评审者各自评完并落库，再按全体结论判定 run。

## ★ 建档实测（为什么这是缺口）

1. `phase_runner._run_group_task` 在 `step.failure is not None` 时**立即**返回失败
   ⇒ 同组后续任务不执行（run 级 fail-fast 的既有语义）。
2. 实测：`review` phase 放宽到两位评审者、两位都交 `score: 0.5` ⇒
   `state: FAILED`、`records: 1`（只有 `gate:reviewer_a`）、`panels: []`。
3. `on_task_failure: CONTINUE` 存在但语义不同：它让 run 收敛 `DEGRADED`
   （判负变成「被容忍的失败」）；本 GOAL 要判负仍 `FAILED`。

## 实施清单

1. **WP-A（领域声明面）**：`TaskContract.failure_policy` 新增**并列键**
   `review_panel: COMPLETE_THEN_JUDGE`（缺省不出现 ⇒ 既有语义逐字不变），
   进 `KNOWN_KEYS` 与 `FailurePolicyView`。
2. **WP-B（执行面）**：组内任务失败时，若**该 phase 全体任务都声明了**该键 ⇒
   **记账并继续同组**（`TaskOutcome` 记 `FAILED` 与 verdict），组末按「全体结论」失败；
   否则逐字回到既有 fail-fast。
3. **WP-C（可见性）**：组末失败消息逐条点名每位评审者的 `endpoint/model_name` 与 verdict；
   全体通过 ⇒ 照常 `SUCCEEDED`（`panels` 的 advisory 由既有读面给）。
4. **WP-D（判据）**：新增
   `tests/e2e/test_a_rejecting_reviewer_does_not_cancel_the_panel.py`（3 条以上，含成对与按压）。

## 影响报告

- **域**：`failure_policy` 新增**并列键** `review_panel`（唯一取值 `COMPLETE_THEN_JUDGE`），
  进 `KNOWN_KEYS` 与 `FailurePolicyView`；`on_task_failure` 的两个取值与消费方式**逐字不变**。
- **应用层**：新增 `review_panel_judging`（组级判定：先评完再判、组末点名全体票型）；
  `phase_runner` 在两条失败路径上各加一个分支（声明了 ⇒ 记账继续；未声明 ⇒ 既有 fail-fast）。
  `failure_step` 多一个**可选** `verdict` 参数（缺省 `None` ⇒ 既有调用点逐字不变），
  两处「验收门拒收」把门的裁决一并交回。
- **聚合面（连带修一处真缺口）**：`panel_verdict` 的 `dissent` 原先只在 `advisory is not None`
  时才记录 ⇒ **平票时 `dissent == []`**（分歧最大的那一刻反而读不到分歧）。现在平票 ⇒
  每票都列。既有判据**没有**断言平票的 `dissent`（只断言 `advisory is None` / `decided is False`）
  ⇒ 这是纯新增信息，**不放宽任何既断言**。
- **schema / 迁移**：无（不落库新列）。
- **HTTP 面 / DTO / OpenAPI**：未改。
- **零回归**：application + api + contracts **2411 passed / 77 skipped**；e2e
  **363 passed / 17 skipped**（新增 3 条）。
- **无依赖变化、无放行面变化、无凭据变化。**

## 工程记忆

**无可复用事实**（本轮读数是判据文件本身）：两个失败声明面（`on_task_failure` 与
`review_panel`）必须互不越界 —— 组末判定只认**本模块记账的**判负，否则会把
`CONTINUE` 的容忍语义悄悄改成判负（首轮实测到的真回归，三处既有用例同时变红）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| EC-01/02/03 运行链 | **3 passed** | `... pytest tests/e2e/test_a_rejecting_reviewer_does_not_cancel_the_panel.py -q` |
| 评审面板定向合计 | **27 passed** | 上面 + `test_review_panel_on_the_run_path` + `test_reviewers_on_one_phase...` + `test_review_panel_aggregation` |
| 应用面零回归 | **2411 passed, 77 skipped** | `... pytest tests/application tests/contracts tests/api -q` |
| e2e 零回归 | **363 passed, 17 skipped** | `... pytest tests/e2e -q` |
| 静态门 | ruff 绿 / format 绿 / mypy（58 文件）绿 | — |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **IN_PROGRESS** | 承 GOAL-087 建档：判负不取消同批评审 + 全体判完再判。 |
| 2026-10-18 | **DONE** | EC-01…EC-04 达成。**首轮抓到一处真回归**：组末判定起初把 `on_task_failure: CONTINUE` 的容忍失败也算成判负 ⇒ 三处既有用例同时变红；已按「只认本模块记账的判负」修正。另连带修了 `dissent` 平票为空的老缺口。**EC-05 留给收口 cycle。** |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **IN_PROGRESS** | 承 GOAL-087 建档：判负不取消同批评审 + 全体判完再判。 |
