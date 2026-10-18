---
id: PLAN-20261018-523
slug: goal-086-ec01-04-panel-groups-by-the-object-under-review
title: GOAL-086 cycle 1 — 评审小组按被评对象聚合 + phase 身份可读（EC-01…EC-04）
status: DONE
created_at: 2026-10-18
updated_at: 2026-10-18
parent_goal: GOAL-20261018-086
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-524-goal-086-panel-groups-by-the-object-under-review.md
memory_entries: []
---

# PLAN-20261018-523 — GOAL-086 cycle 1

## 验收条件

- [x] **EC-01**：多评审 phase 上，评审者的判词按**被评对象**（phase × 合约）聚合；
      运行链上 `panels` **非空**且 `voters` = 该 phase 上可归因的评审者数。
      反证：不同 phase ⇒ 不聚合。
- [x] **EC-02**：落库的评审结论带 `phase_id`（可空新列 + 迁移）；读面逐条露出；
      无 `phase_id` 的记录**不参与聚合且被点名**（不并组、不丢弃）。
- [x] **EC-03**：同 phase 上两位评审者落在**同一**执行目标 ⇒ `independent=False` 并点名；
      不同目标 ⇒ `True`；按压 ⇒ 翻转。
- [x] **EC-04**：单评审 `panels == []`（既有 6 条判据逐字保留）；`phase_id is None` 的
      既有记录读面只多出这个可空键。
- [x] **EC-05 不在本 cycle 的射程**（收口 cycle 的交付物）。

## 目标

让阶梯「复检」的下一格（「两个模型在同一个上游产物上给出不同判词」）**先具备前提**：
同一 phase 的两位评审者**真的被聚成一个小队**。

## ★ 建档实测（为什么这是缺口）

1. `adapters/canonical/review_read.py` 的 `_panel_rows` 按 `(task_id, contract_id)` 分组。
2. `session_resolution.py:192-197` 对**每个**评审 agent 各生成一条 `ResearchTask`，
   幂等键 `{run}:{phase}:{agent_id}` ⇒ 同 phase 两评审 = 两个不同 `task_id`。
3. `evaluation_gate.py:217` 判词 id 逐字 `finding:{task_id}:gate` ⇒ 一个任务至多一条判词
   ⇒ 该分组下 `len(findings) < 2` ⇒ `aggregate_panel` 返回 `None`。
4. **实测**：两条判词分挂 `task:reviewer_a` / `task:reviewer_b` ⇒ `count: 2, panels: 0`。
5. 多评审 phase 在出厂目录里真实存在（`ai_ml_research_v0_4_0.yaml:66` 的 `min_instances: 2`；
   `team_templates.yaml` 的 `standard`；`project.yaml` 的 `team_template: standard`）。

## 实施清单

1. **WP-A（域/端口）**：`ScopedReviewFinding` 新增 `phase_id: str | None = None`
   （**纯新增、可空** ⇒ 既有构造点逐字不变）；`acceptance_finding` 从
   `spec_context.phase_id` 取并搬运。
2. **WP-B（读面分组）**：`_panel_rows` 改用**被评对象**分组 ——
   `(phase_id, contract_id)`；`phase_id` 为 `None` 的记录**不进任何组**，
   由读面新增的 `unattributed` 键**逐条点名**（判词 id + 理由）。
3. **WP-C（落库）**：sqlite `phase_id TEXT` 增量列（`PRAGMA table_info` + `ALTER`）；
   postgres `_SELECT` / insert / decode 加列 + 迁移 `029_review_finding_phase_id.sql`
   （`ADD COLUMN IF NOT EXISTS`，可空）。
4. **WP-D（判据）**：新增 `tests/e2e/test_reviewers_on_one_phase_form_a_panel.py`
   （走**运行链**，不是手写 `ScopedReviewFinding`）；`tests/application` 侧补
   `phase_id` 分组的两向用例；既有 6 条面板判据**逐字保留**。

## 影响报告

- **域 / 端口**：`ScopedReviewFinding` 新增一个**可空**字段 `phase_id`（纯新增 ⇒
  既有构造点逐字不变；两适配器的 `decode` 与 `put` 已同步）。
- **应用层**：`acceptance_finding(..., phase_id=...)` 从 `SessionSpecContext.phase_id`
  搬运（空串视同缺席 ⇒ 落 `None`）；`record_acceptance_evaluation` 是唯一调用点。
- **读面**：`review_read` 的每行新增 `phase_id`，每行 `panels` 新增 `scope`
  （`PHASE` / `TASK`）—— 两种聚合口径的射程**不同**，载荷必须可区分。
  既有 `reviews` 形态只多一个可空键；`panels` 在单评审时仍为 `[]`。
- **落库 / 迁移**：SQLite 增量列 `phase_id TEXT`（`PRAGMA table_info` + `ALTER`，
  既有库实测补列成功、旧行保持 `NULL`）；Postgres 新增
  `adapters/postgres/migrations/029_review_finding_phase_id.sql`
  （`ADD COLUMN IF NOT EXISTS`，可空、无缺省 ⇒ **非破坏性**）。
- **HTTP 面 / DTO / OpenAPI**：**未改**（`review.read` 是能力面，不是 HTTP DTO）
  ⇒ 快照零改动。
- **零回归**：application + api + contracts **2411 passed / 77 skipped**；
  评审相关定向套件 **39 passed**。
- **无依赖变化、无放行面变化、无凭据变化。**

## 工程记忆

**无可复用事实**（本轮读数是判据文件本身，不是可外推的工程结论）：
「分组键是被评对象而非任务」这条形态与 `resolve_sessions` 的逐 agent 展开耦合，
写在 `review_read._panel_rows` 的 docstring 里；`CREATE TABLE IF NOT EXISTS`
不给既有表加列这点已由 GOAL-085 记录过，本轮的增量是**升级后的旧库**也要能读。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| EC-01 + EC-03 运行链 | **3 passed** | `... pytest tests/e2e/test_reviewers_on_one_phase_form_a_panel.py -q` |
| EC-02 + EC-04 读面 | **8 passed** | `... pytest tests/e2e/test_review_panel_on_the_run_path.py -q` |
| EC-02 落库往返（sqlite） | **5 passed** | `... pytest tests/contracts/test_review_finding_store_contracts.py -q` |
| 评审相关定向合计 | **39 passed** | 上面四份 + `test_review_panel_aggregation` / `test_review_attribution` |
| 应用面零回归 | **2411 passed, 77 skipped** | `... pytest tests/application tests/contracts tests/api -q` |
| 静态门 | ruff 绿 / format 绿 / mypy 绿 | — |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **IN_PROGRESS** | 承 GOAL-086 建档：按被评对象聚合 + phase 身份落库与可读。 |
| 2026-10-18 | **DONE** | EC-01…EC-04 达成。运行链读数：两位评审者同 phase ⇒ `panels` 一条、`voters == 2`、`scope == "PHASE"`、`independent is True`；按压同模型 ⇒ `independent is False` 并点名 `main/glm-5.3`；不同 phase ⇒ `panels == []`。落库：`phase_id` 往返（含既有库补列）。零回归：application+api+contracts **2411 passed / 77 skipped**、e2e **360 passed / 17 skipped**。**EC-05 留给收口 cycle。** |
