---
id: PLAN-20260918-101
slug: validation-failure-consumption-adr
title: 验收门拒收的处置：ADR 草案 + 权威登记 + 声明面同源收敛（EC-02 (b)）
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-006
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-006 cycle 2 = EC-02（GOAL-005 收口结论第 3 项 / RECHECK-095 W-2：`DEAD_LETTER` 消费）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-006 并自动化循环推进、无需逐轮确认）。push-to-main-for-CI 授权沿用 GOAL-001…005 批准口径（只推 main、不 force、不重写历史、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-101-validation-failure-consumption-adr.md
memory_entries:
  - MEM-20260918-074
---

# PLAN-20260918-101 — 验收门拒收的处置（GOAL-006 cycle 2 = EC-02 (b)）

## 目标

EC-02 要求 `DEAD_LETTER` 消费拿到**二选一终态**：(a) 在**既有 canonical 边界内**实现按声明
处置；或 (b) **ADR 草案 + 权威登记 + 声明/文档同源收敛**。本 PLAN 走 **(b)**，
理由是 (a) 被既有边界挡住（见下）。

## 先探明再动手（只读勘察，逐条可复核）

1. **拒收发生在 durable 成功之后**：`task_executor._attempt_once` 先
   `engine.complete(live, TaskCompletion(outcome="SUCCEEDED"))`（durable 终态 + 释放租约），
   之后 `task_phase_helpers.register_and_gate` 才跑验收门；门不过 ⇒
   `failure_step(..., "task ... rejected by acceptance gate", False)`。
2. **拒收只落在 run 级**：`failure_step` 的两个分支要么 `deps.fail(run_id, message, False)`
   ⇒ `run_terminals.publish_failed_run` 发 `run.failed`（message 含 "rejected by acceptance
   gate"，RunOutcome `FAILED`），要么（`on_task_failure: CONTINUE`）返回 `tolerated_failure`
   ⇒ 最终 `run.degraded`（`tolerated_failures[].message` 同样带这句话）。**任务行不动**。
3. **(a) 不可行**：`ResearchTaskState._TRANSITIONS` 里 `SUCCEEDED` 是**终态**、没有任何
   从它出发的迁移；`DEAD_LETTER` 只能从 `RETRY_SCHEDULED` 到达。要按声明把一条已
   `SUCCEEDED` 的任务行改写回 `DEAD_LETTER`，就必须新增"从终态出发的迁移"或新增状态
   ⇒ **canonical 状态机改动**，命中 GOAL-006 的 `escalation_triggers`
   （"需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界"）与 GOAL-006
   「不进入循环 / 需人工拍板」第 3 项的同类决策面 ⇒ 循环内**不自行扩大边界**。
4. **声明面现状**（反向搜索 `on_validation_failure`，产品/文档/示例命中逐处）：
   - `packages/domain/failure_policy.py` 模块 docstring：写明它进 `unhonored`、消费需
     canonical 决策、属后继入口；
   - `docs/architecture/TASK_HANDOFF.md` §2.1：写明同一件事 + 拒收在 durable `SUCCEEDED`
     之后；
   - `examples/contracts/task_contracts.yaml`：注释说明示例只声明被消费的键；
   - 用例（`tests/domain/test_failure_policy_view.py`、
     `tests/application/run_orchestration/test_failure_policy_consumer.py`）：钉住
     "声明它不改变任何判定"。
   ⇒ 边界**已被如实登记**，但**没有权威决策记录**（ADR）可指：三处各自表述，没有一处
   是"这就是待拍板的决策本身（含选项、代价、触发条件）"。
5. **无 ADR 门禁约束**：`governance-check` 不校验 ADR；`docs_consistency_check` 只校验
   INDEX/roadmap/反引号路径可解析 ⇒ 新增一条 `Status: Proposed` 的 ADR 不触任何门禁，
   也不修改任何 Accepted ADR。

## 口径

- **(a) 不做**：不新增 canonical 状态、不新增迁移、不修改 Accepted ADR、不改
  `task_state.py` / `examples/contracts/task_contracts.yaml` 的声明面语义。
- **(b) 的三件交付**：
  1. **ADR 草案**（`docs/adr/ADR-0030-validation-failure-consumption.md`，
     `Status: Proposed`）：问题、**选项 A–E 与逐个代价/收益**、为何本轮不做、
     触发条件（何时必须拍板）、影响面（谁在读这条任务行/这条 run）。
  2. **权威登记**：`docs/INDEX.md` 的 ADR 列表加一条（Proposed），使"待拍板"有唯一入口。
  3. **声明/文档同源收敛**：`failure_policy.py` / `TASK_HANDOFF.md` §2.1 /
     `examples/contracts/task_contracts.yaml` 三处**指向同一份 ADR**（同一句话 + 同一 id），
     不再各自表述。
- **不得只改文案充数**（EC-02 原文）：同源收敛必须有**可判定的判据** —— 新增
  `tests/tooling/test_pending_validation_failure_registration.py`，读真实文件断言
  ①ADR 在树且 `Status: Proposed`；②`docs/INDEX.md` 登记了它；③三处声明面各自同时出现
  `on_validation_failure` 与 ADR id；④`on_validation_failure` 仍**不改变判定**
  （`failure_policy_view().unhonored` 点名，行为按缺省）——即"未消费"是**声明**而不是
  悄悄实现了一半。
- **不改判据语义**：既有用例（声明不改变行为）保持绿，不改断言。

## 验收条件

- **AC-01 ADR 草案在位且实质**：`docs/adr/ADR-0030-validation-failure-consumption.md`
  存在，`Status: Proposed`，含 `## Context` / `## Options`（≥4 个选项，逐个代价与收益）/
  `## Decision needed` / `## Why not now` / `## Trigger` / `## Consequences`；
  事实段与本节「先探明再动手」的 4 条一致（可对照 `task_state.py` / `task_executor.py` /
  `task_phase_helpers.py` / `run_terminals.py`）。
- **AC-02 权威登记**：`docs/INDEX.md` 出现该 ADR 的条目（含 `Proposed` 字样）。
- **AC-03 同源收敛**：三处声明面各自指向 ADR-0030，且彼此口径一致（同一句"待拍板"）。
- **AC-04 可判定判据**：新用例覆盖 AC-01…AC-03 + "未消费仍是声明"；**反证**：把任一处的
  ADR 指针删掉 ⇒ 对应用例红。
- **AC-05 门禁**：规模门禁 / 文档门 / 定向套件 / m0 全量 23 项 / CI 六 job 到终态并记账。

## 实施清单

### WP-A — ADR 草案（`docs/adr/ADR-0030-validation-failure-consumption.md`）

- [x] 写 `Status: Proposed` 的 ADR：Context（4 条事实 + 差距）、Decision needed、
      Options A–E（逐个代价/收益）、Why not now（escalation 命中面）、Trigger、Consequences。
- [x] 选项里必须包含：A 从终态出发的新迁移、B 新终态、C 维持 run 级 + 读面点名、
      D 把门挪到 durable 完成之前（非终态出发的迁移）、E 不做（现状）。

### WP-B — 权威登记（`docs/INDEX.md`）

- [x] ADR 列表加 `ADR-0030-validation-failure-consumption.md — 验收门拒收的处置（Proposed）`。

### WP-C — 声明面同源收敛

- [x] `packages/domain/failure_policy.py` 模块 docstring：指向 ADR-0030。
- [x] `docs/architecture/TASK_HANDOFF.md` §2.1：指向 ADR-0030。
- [x] `examples/contracts/task_contracts.yaml` 注释：指向 ADR-0030。

### WP-D — 判据用例

- [x] `tests/tooling/test_pending_validation_failure_registration.py`：四处断言
      （ADR 在树 + Proposed / INDEX 登记 / 三处指针 / 未消费仍是声明）。
- [x] **反证实跑**：删掉一处 ADR 指针 ⇒ 第 3 条红；ADR 改 `Accepted` ⇒ 第 1 条红；
      两次还原 ⇒ 4 passed。

### WP-E — 记录与回写

- [x] RECHECK-20260918-101、MEM-20260918-074、PLAN/RECHECK/ALL_PLAN/`memory/INDEX.md`、
      GOAL-006 回写（EC-02 状态 / 迭代日志 / child_plans / 状态历史）。

## 证据

- **反证实跑**：
  - ① 删 `examples/contracts/task_contracts.yaml` 的 ADR 指针 ⇒
    `test_every_declaration_surface_points_at_the_same_record` **failed**
    （`task_contracts.yaml 必须指向同一份决策记录（同源收敛）`，1 failed / 3 passed）；
    还原 ⇒ **4 passed**。
  - ② ADR 的 `Status: Proposed` → `Accepted` ⇒
    `test_the_decision_record_is_a_proposal_not_a_decision` **failed**
    （`草案必须是 Proposed：它还没被人工拍板`，1 failed / 3 passed）；还原 ⇒ **4 passed**。
- **判据用例**：`tests/tooling/test_pending_validation_failure_registration.py` ⇒ **4 passed**（0.03s）。
- **定向**：`tests/domain tests/loaders tests/tooling tests/application/run_orchestration` ⇒
  **1537 passed**（9.65s）。
- **风格/类型**：`ruff format --check` **938 already formatted**；`ruff check` **All checks passed**；
  `mypy` **Success: no issues found in 928 source files**。
- **文档门**：`tools/docs_consistency_check.py` ⇒ **DOCS-CHECK PASS: 6 deterministic checks**。
- **m0 全量**：见「状态历史」。

## 状态历史

- 2026-09-18 建档（GOAL-006 cycle 2 = EC-02，driver=client-goal / owner=root-agent）：
  只读勘察判定 (a) 被 canonical 终态边界挡住（`SUCCEEDED` 无出边），选 (b)；
  `status: IN_PROGRESS`。
- 2026-09-18 执行与收口：WP-A…WP-E 完成；两次反证各红一条（指针 / 状态）并还原；
  定向 **1537 passed**；风格/类型/文档门全绿；`status: DONE`
  （RECHECK-20260918-101 = PASS_WITH_WARNINGS，W-1…W-5）。**零产品行为改动**：
  不新增 canonical 状态/迁移、不改 Accepted ADR、不改示例契约的声明语义。

## 影响报告

- **Domain / API / schema**：Domain 与 API **零变化**（本 PLAN 不动产品行为）；
  canonical 状态机**不动**。
- **持久化 / 迁移**：无。
- **安全 / 凭据**：无凭据面变化；无新增出网/依赖。
- **兼容性 / 迁移风险**：无（纯记录 + 文档 + 一条新用例）。
- **上游版本影响**：无。
- **下一项任务**：GOAL-006 cycle 3 = EC-03（前端消费 `rebuild` 读面 + stub/live e2e）。
