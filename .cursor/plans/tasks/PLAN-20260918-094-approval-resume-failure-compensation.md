---
id: PLAN-20260918-094
slug: approval-resume-failure-compensation
title: 审批通过后续跑失败的补偿：不放任悬空 RUNNING（EC-02）
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-005
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-005 cycle 2 = EC-02（GOAL-004 收口结论表第 2 项 / RECHECK-090 W-1）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-005 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-094-approval-resume-failure-compensation.md
memory_entries:
  - MEM-20260918-068
---

# PLAN-20260918-094 — 审批通过后续跑失败的补偿（GOAL-005 cycle 2 = EC-02）

## 目标

GOAL-004 EC-06 把 `resume_paused` 的失败补偿收口成「失败即补偿 + 可观测 + 可重入 +
反证」。当时如实登记了**同形缺口**（RECHECK-090 W-1）：审批通过后的续跑
（`resume_after_approval`）同样是"先 pop 暂存上下文再执行"，失败不补偿。

本 PLAN 按同一判据把它收口。

**先反向搜索确认真实缺口**（不照抄 W-1 的描述）：W-1 写的是「run 停在
`WAITING_FOR_APPROVAL`」，实测**不是**——`decide` 端点在续跑前就把 run 按状态机落成
`RUNNING`（`WAITING_FOR_APPROVAL --APPROVAL_GRANTED--> RUNNING`），`_resume_after_approval`
只捕 `InvalidInputError`、其余异常冒给端点。所以失败后的 canonical 事实是
**悬空 `RUNNING`**（没有执行者、`_waiting` 已被 pop、`PAUSED → RUNNING` 那条重入路也
走不到，因为状态已经是 `RUNNING`）——比 W-1 描述的更糟，且与 EC-06 要消灭的缺陷同形。

## 口径

- **不改测试断言、不改门禁**；补偿走**既有域迁移**（`RUNNING --PAUSE--> PAUSED`，与
  `POST /runs/{id}/pause` 同一条路径）⇒ 不新增 canonical 状态/迁移，不触
  `escalation_triggers` 的 Canonical State 边界。
- **两条入口共用一个补偿实现**（`compensate_failed_resume`），本 PLAN 只加调用点，
  不改补偿动作本身。
- **反证是交付的一部分**：去掉补偿 ⇒ 对应用例必须变红（本 PLAN 实跑）。

## 验收条件

- AC-01 审批通过后续跑失败 ⇒ canonical run 行是 `PAUSED`（**不是** `RUNNING`）；
  裁决本身仍如实返回 `APPROVED`（失败的是续跑，不是裁决）。
- AC-02 原因可从 canonical 事实读到：事件链有 `run.resume_failed`
  （`failure_type` / `message` / `compensated_to`）。
- AC-03 可重入：补偿后 run 回停车态 ⇒ 后续 `POST /runs/{id}/resume` 不被 409 挡住，
  且能真的续起来（`continuation=RESUMED`）。
- AC-04 既有语义不变：正常续跑不记失败事件；上下文竞态（`InvalidInputError`）仍是
  既有 no-op（此时 `RUNNING` 是正确状态——另一个入口正在跑）。
- AC-05 反证：暂时去掉补偿 ⇒ AC-01/AC-03 的用例变红（判据有判别力）。
- AC-06 文档同源：`docs/api/CONTROL_PLANE_API.md` 写明 approve 续跑失败的结局口径
  与"只有一个入口"的事实。
- AC-07 记录链完整（PLAN / RECHECK / MEM / ALL_PLAN / GOAL）+ 治理 validator 绿 +
  本地 m0 全绿 + CI 六 job 终态如实记录。

## 实施清单

### WP-A — 补偿接线（已完成）

- `services/api/routers/approvals.py::_resume_after_approval`：`InvalidInputError` 之外的
  失败 ⇒ `save_run(deps, deps.runs.compensate_failed_resume(granted, exc))`（放回 `PAUSED`
  + `run.resume_failed`），不再把异常冒给端点。
- 复用 GOAL-004 cycle 7 的 `compensate_failed_resume`（`run_terminals.py`），
  **不新增**事件类型、不新增 payload 键、不动 canonical 状态机。

verify：新用例 4 条（见 WP-B）+ 既有 `tests/api/test_resume_compensation_api.py` 不回退。

### WP-B — 用例与反证（已完成）

`tests/api/test_approval_resume_compensation_api.py`（失败注入用实例级替身：只替换执行侧
`has_waiting_context` / `resume_after_approval`，补偿跑真实现）：

1. 失败 ⇒ store 里是 `PAUSED` + 1 条 `run.resume_failed`（`failure_type=RuntimeError`、
   `message` 原文、`compensated_to=PAUSED`）；
2. 可重入 ⇒ `POST /runs/{id}/resume` 200 + `continuation=RESUMED`（不被 409 挡）；
3. 正常路径 ⇒ `RUNNING` 且**无**失败事件；
4. 竞态（`InvalidInputError`）⇒ 既有 no-op，`RUNNING` 不变、无失败事件。

反证（实跑）：把补偿换成 `raise exc` ⇒ **2 failed / 2 passed**（正是断言补偿的那两条红）。

verify：`uv run --frozen --no-sync python -B -m pytest tests/api/test_approval_resume_compensation_api.py`
⇒ **4 passed**；反证跑见「证据」。

### WP-C — 文档与记录（已完成）

- `docs/api/CONTROL_PLANE_API.md` 的 Tasks / Approvals 节补「approve 续跑失败的结局」段。
- 写 RECHECK-20260918-094、MEM-20260918-068、PLAN DONE、`ALL_PLAN` 行、GOAL-005 回写。

verify：治理 validator 绿；m0 全量；CI 六 job 记账。

## 证据

- **反证（实跑）**：补偿替换为 `raise exc` ⇒
  `2 failed, 2 passed in 2.66s`，红的两条 =
  `test_a_failed_approval_resume_is_compensated_and_the_reason_is_canonical` 与
  `test_the_compensated_approval_run_is_not_bricked` ⇒ 判据不是"永远绿"的断言。
- **定向套件**（DSN pin 配方）：
  `tests/api tests/application tests/contracts tests/domain tests/e2e`
  ⇒ **1997 passed / 4 skipped**（271.89s）。
- **新用例**：`tests/api/test_approval_resume_compensation_api.py` **4 passed**；
  与既有 `test_resume_compensation_api.py` + `test_approvals_api.py` 合并跑 **18 passed**。
- **既有行为对照**：`test_decide_approve_resumes_run`（approve → RUNNING）未改，仍绿。

## 状态历史

- 2026-09-18 建档（GOAL-20260918-005 cycle 2 = EC-02，driver=client-goal /
  owner=root-agent）：先反向搜索确认真实缺口（W-1 描述的"停在 WAITING_FOR_APPROVAL"
  与实测不符，实为悬空 `RUNNING`）；`status: IN_PROGRESS`。
- 2026-09-18 收口：WP-A/WP-B/WP-C 完成；反证 2 红（仅补偿相关用例）；定向
  **1997 passed / 4 skipped**；`status: DONE`。

## 影响报告

- **Domain / API / schema**：**无 schema 变更**；`POST /approvals/{id}/decide` 的响应体
  不变（仍 200 + `APPROVED`），变化在 canonical 结局（失败 ⇒ `PAUSED` + 事件）与
  事件链内容。
- **持久化 / 迁移**：无迁移；补偿写 run 行（`PAUSED`）与事件（与 EC-06 同一条路径）。
- **安全 / 凭据**：无凭据面变化。
- **兼容性 / 迁移风险**：低。唯一行为变化是"approve 续跑失败不再 500、run 不再悬空
  RUNNING"。调用方若依赖 500 判失败，需改读 canonical 状态/事件（文档已写明）。
- **上游版本影响**：无（未新增依赖）。
- **下一项任务**：GOAL-005 cycle 3 = EC-03（声明未消费项清账）。
