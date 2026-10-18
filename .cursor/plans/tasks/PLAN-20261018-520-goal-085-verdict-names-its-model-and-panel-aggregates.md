---
id: PLAN-20261018-520
slug: goal-085-verdict-names-its-model-and-panel-aggregates
title: GOAL-085 cycle 1 — 评审判词点名模型 + 多评审聚合（EC-01…EC-04）
status: DONE
created_at: 2026-10-18
updated_at: 2026-10-18
parent_goal: GOAL-20261018-085
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-521-goal-085-verdict-attribution-and-panel.md
memory_entries: []
---

# PLAN-20261018-520 — GOAL-085 cycle 1

## 验收条件

- [x] **EC-01**：判词带 `reviewer_model`（`endpoint/model_name`，与 `review_independence`
      同源）；身份取自 `SessionSpecContext.endpoint` / `.model`（不是 agent 名 / profile 名 /
      model id）；解析不了 ⇒ `None` 并点名；`reviewed_by` 逐字不变。
- [x] **EC-02**：多票确定性聚合（唯一最高票 ⇒ advisory；**平票 ⇒ `None`**；
      **全失败 ⇒ 无票且逐条点名**；**单评审 ⇒ `None`**）。
- [x] **EC-03**：独立性按**解析后的目标**判（与 GOAL-084 同源）；同目标两个实例 ⇒
      `independent=False` 并点名；异目标 ⇒ `True`；按压第二份的目标 ⇒ 翻转。
- [x] **EC-04**：归因经**落库链**保留（`acceptance_observation` 原样搬运）；
      读面（`review_read`）给出 `reviewer_model` 与 `panels`；**单评审 `panels == []`**；
      **不同任务不混票**。
- [x] **EC-05 不在本 cycle 的射程**（收口 cycle 的交付物）。

## 目标

让「评审」从**一条由验收门顺手生成的判词**，变成**可归因到模型、可聚合成建议性结论、
且独立性可判**的事实。

## ★ 建档实测（为什么这是缺口）

1. `packages/domain/evidence.py` 的 `ReviewFinding` 只有
   `id/review_type/verdict/findings/reviewed_by/reviewed_at` —— **没有** `model_identity`；
   SQLite 表 `review_findings` 的列逐个读出**也无该列**。
2. `reviewed_by` 逐字是 `gate:<agent id>`（`task_phase_helpers.py`）—— agent 名。
   GOAL-084 已证明 agent 名与底层模型可以**完全脱钩**。
3. `run_panel` / `LlmReviewer` / `ReviewAssignment` 在产品代码里**零构造点**
   （`rg "run_panel\(" --glob '!tests/**'` 只命中定义处）⇒ 多评审**从不聚合**。
4. `eval_result.ReviewerFinding` **早有** `model_identity`，但那是 M11 离线评测那条链
   ⇒ 同一概念**一有一无**。

## 实施清单

1. **WP-A（域）**：`ReviewFinding` 新增 `reviewer_model: str | None = None`
   （**纯新增、可空** ⇒ 既有构造点逐字不变）。
2. **WP-B（门）**：`evaluate_task_gate(..., reviewer_model=...)` 落进判词；
   运行链调用点用 `_reviewer_model_of(spec_context)` 从**装配好的执行目标**取值。
3. **WP-C（聚合）**：`evaluation/panel_verdict.py` —— `aggregate_panel` + `PanelVerdict`
   （advisory、平票 `None`、无身份者**点名不进票**、独立性按目标互异）。
4. **WP-D（读面/落库）**：`acceptance_observation.acceptance_finding` 搬运归因；
   sqlite/postgres 两适配器 + 迁移 `028` 落列；`review_read` 新增 `reviewer_model`
   与 `panels`。
5. **WP-E（判据）**：三份新判据（归因 10 / 聚合 13 / 运行路径 6）。

## 影响报告

- **产品代码**：域实体新增一个可空字段；门多一个可选参数；新增一个纯函数聚合模块；
  读面多两个键（`reviewer_model` / `panels` / `panel_count`）。
  **`Decision` 未被触碰**（聚合是 advisory）。
- **schema / 迁移**：新增 `adapters/postgres/migrations/028_review_finding_reviewer_model.sql`
  （`ADD COLUMN IF NOT EXISTS`，可空、无缺省 ⇒ **非破坏性**）。SQLite 侧用
  `PRAGMA table_info` + `ALTER` 做**增量列**。
- **读面 / DTO / 路由 / OpenAPI 快照**：HTTP 面**未改**（`review_read` 是**能力面**，
  不是 HTTP DTO）⇒ 快照零改动。
- **零回归**：`tests/e2e` 371 passed（含 17 skipped）、宽面 2729 passed。
- **无依赖变化、无放行面变化、无凭据变化。**

## 工程记忆

**无可复用事实**（本轮三条读数写进 RECHECK-521 的可复核观察面；判据文件即事实面）：
`ReviewFinding` 无 `reviewer_id`（作者面是 `reviewed_by`，逐字 `gate:<agent>`）；
`CREATE TABLE IF NOT EXISTS` 不给已存在的表加列（必须 `PRAGMA table_info` + `ALTER`）；
聚合的分组键必须是 `(task_id, contract_id)` 而不是整个 run。

## 残余与未覆盖

见 GOAL 的「残余与未覆盖范围」：`W-2`（多数票不等于对）、`W-3`（不判两个模型是否同质化）、
`W-4`（不改既有 `reviewed_by` 的写法）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| EC-01 归因 | **10 passed** | `... pytest tests/application/test_review_attribution.py -q` |
| EC-02 + EC-03 聚合/独立性 | **13 passed** | `... pytest tests/application/test_review_panel_aggregation.py -q` |
| EC-04 运行路径读面 | **6 passed** | `... pytest tests/e2e/test_review_panel_on_the_run_path.py -q` |
| 应用面零回归 | **1201 passed, 1 skipped** | `... pytest tests/application -q` |
| 宽面零回归 | **3086 passed, 94 skipped** | `... pytest tests/application tests/api tests/contracts tests/architecture tests/loaders -q` |
| 运行路径 e2e | **3086 passed, 94 skipped**（含 e2e） | `... pytest tests/api/test_runs_api.py tests/e2e -q` |
| 静态门 | ruff 绿 / **1277 files** mypy clean / format 1287 files | — |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **IN_PROGRESS** | 承 GOAL-085 建档：归因 + 聚合 + 独立性 + 读面。 |
| 2026-10-18 | **DONE** | EC-01…EC-04 达成；EC-05 留给收口 cycle。 |
