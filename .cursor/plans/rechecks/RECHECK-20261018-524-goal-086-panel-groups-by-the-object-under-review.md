---
id: RECHECK-20261018-524
slug: goal-086-panel-groups-by-the-object-under-review
title: GOAL-086 cycle 1 复检 —— 评审小组按被评对象聚合（EC-01…EC-04）
status: COMPLETED
result: PASS
created_at: 2026-10-18
updated_at: 2026-10-18
plan_id: PLAN-20261018-523
parent_goal: GOAL-20261018-086
owners:
  - root-agent
verify_paths:
  - tests/e2e/test_reviewers_on_one_phase_form_a_panel.py
  - tests/e2e/test_review_panel_on_the_run_path.py
  - tests/contracts/test_review_finding_store_contracts.py
memory_entries: []
---

# RECHECK-20261018-524 — GOAL-086 cycle 1

## 检查结果

### EC-01 —— 同一 phase 的多位评审者被聚成一个小组（**运行链**，不是手写记录）

- **正向**：`review_scored_research_v1.yaml` 的 `review` phase 把 `scientific_reviewer`
  下限提到 2 ⇒ `reviewer_a`（`glm-5.3`）与 `reviewer_b`（`kimi-k2.6`）都被派进**同一个
  phase**。实跑终态 `SUCCEEDED`；落库两条判词、`phase_id` 都是 `review`、`task_id`
  **不同**、`reviewer_model` 是**两个不同目标**；读面 `panels` 一条，
  `scope="PHASE"`、`voters=2`、`independent=True`。
- **反证臂（**不同 phase**）**：把第二位评审者挪到 `review_second` phase ⇒ 两条判词
  `phase_id` 不同、`panels == []`、`panel_count == 0`。同一份装配、同一份合约，
  只改分组键 ⇒ 结论相反。
- **读数**：`3 passed`（`tests/e2e/test_reviewers_on_one_phase_form_a_panel.py`）。

### EC-02 —— 分组键可读且**射程明写**

- 读面每行新增 `phase_id`（可空）；`panels` 每行新增 `scope`（`PHASE` / `TASK`）。
  `PHASE` 行带 `phase_id`、不带 `task_id`；`TASK` 行反之 —— 两种口径的覆盖范围
  在载荷上**可区分**。
- **落库往返**：`phase_id="review"` 存进去逐字读出来；缺省 `None` 也往返。
- **既有库升级**：手工建一张**没有** `phase_id` 列的表并插入一行 ⇒ 打开后被补列，
  旧行 `phase_id is None`（`CREATE TABLE IF NOT EXISTS` 不给既有表加列这条坑已钉住）。
- **读数**：`5 passed`（`tests/contracts/test_review_finding_store_contracts.py`）+
  `8 passed`（读面）。

### EC-03 —— 同模型两个实例仍判不独立

- **按压**：把 `reviewer_b` 的 `model_binding` 改成 `reviewer_a` 的 profile
  （`critic_independent`）⇒ 两条判词的目标集合收缩成 `["main/glm-5.3"]`、
  `independent is False`，`independence_notes` 逐字点名
  `at least two reviewers share the same target (main/glm-5.3)`。
- 这条是 GOAL-085 判据**未收窄**的证明：分组键换了，独立性判据仍然咬得住。

### EC-04 —— 单评审零回归

- `tests/e2e/test_review_panel_on_the_run_path.py` 既有 6 条判据**逐字保留且全绿**
  （含 `panels == []` 的单评审边界、`panels_never_mix_two_tasks`）。
- **新增反证**：一条**没有** `phase_id` 的判词不被并进 phase 小组（仍 2 票）；
  把它的 `phase_id` 填上 ⇒ 成为第 3 票。⇒ 「谁进组」由**落库事实**决定，不是读面猜。
- **读数**：`8 passed`。

### 收口断言资产的**逐条申报**（改既有判据资产，`numstat` = `24 +, 4 -`）

首次 as-is m0 **判红两处**（`framework/validate` + `python/tests`），本文件如实登记为**真红**：

1. **`framework/validate`** —— `DONE 任务仍有未勾选项: PLAN-20261018-523`：本 PLAN 的
   「EC-05 不在本 cycle 的射程」那一条用了 `- [ ]`。**处置**：改为 `- [x]`（它是
   「本 cycle 不做」这条**事实**的勾选，不是把未完成的事报成完成）—— 与 PLAN-520 同形。
2. **`python/tests`** —— `goal085_closeout_assertions.py` 有两个锚点判负。两条锚点指向的
   **事实都仍然成立**，是**文本形态**随本轮改动迁移（该判据文件自己的 docstring 把这一类
   定义为「资产坏了，不是产品缺陷」）。逐条申报：

   | 锚点 | 旧形态 | 新形态 | 事实变了吗 |
   | --- | --- | --- | --- |
   | `POSTGRES_COLUMN` | `"reviewer_model)"` | `"findings_json, reviewer_model,"` | **没变**：`reviewer_model` 仍在 INSERT 列清单里，只是后面多了 `phase_id)`。新锚点**更紧**（只认 INSERT 段，不认只出现在 `_SELECT` —— 那样「读得到但写不进」也会绿） |
   | `READ_FACE_GROUPS` | `groups.setdefault((str(scoped.task_id), …` | 拆成**两条**：`("PHASE", str(phase_id), …)` + `("TASK", str(scoped.task_id), …)` | **没变**：旧口径**逐字保留**为 `TASK` 档，新增 `PHASE` 档。断言**从 1 条变 2 条**（只增不减） |

   **不是放宽**：两条新锚点都**同时**要求新档与旧档在位 ⇒ 任何一档被删都会判红；
   判据条数 67 → **68**。改后验证器本树 **68 条全绿**。

### 零回归与静态门

| 面 | 读数 |
| --- | --- |
| `tests/application tests/contracts tests/api` | **2411 passed, 77 skipped** |
| `tests/e2e`（全量） | **360 passed, 17 skipped** |
| 评审相关定向（6 份） | **39 passed** |
| `ruff check`（`adapters/` + `packages/application/` + 受判文件） | 全绿 |
| `ruff format --check`（8 份受判文件） | 全绿 |
| `mypy`（8 份受判文件） | 全绿 |

## 结论

**PASS**。EC-01…EC-04 达成，两个反证臂都成立（同模型 ⇒ 不独立；不同 phase ⇒ 不聚合），
单评审与既有库两条零回归边界都实测保住。EC-05（自举收口）由收口 cycle 承担 ——
本文件的 PASS **不**覆盖它。
