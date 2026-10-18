---
id: RECHECK-20261018-527
slug: goal-087-a-rejecting-reviewer-does-not-cancel-the-panel
title: GOAL-087 cycle 1 复检 —— 判负不取消同批评审（EC-01…EC-04）
status: COMPLETED
result: PASS
created_at: 2026-10-18
updated_at: 2026-10-18
plan_id: PLAN-20261018-526
parent_goal: GOAL-20261018-087
owners:
  - root-agent
verify_paths:
  - tests/e2e/test_a_rejecting_reviewer_does_not_cancel_the_panel.py
  - tests/application/run_orchestration/test_failure_policy_consumer.py
  - tests/application/test_review_panel_aggregation.py
memory_entries: []
---

# RECHECK-20261018-527 — GOAL-087 cycle 1

## 检查结果

### EC-01 —— 判负不再取消同批评审（**运行链**）

- **正向**：`review` phase 放宽到两位评审者、两位都交付 `score: 0.5` ⇒ 落库 **2 条**判词
  （`gate:reviewer_a` + `gate:reviewer_b`）、`panels` 一条且 `voters == 2`、
  `votes == {"REJECT": 2}`；run 终态**仍是 `FAILED`**（判负没被吞掉）。
- **点名**：失败消息逐字含 `main/glm-5.3=REJECT` 与 `main/kimi-k2.6=REJECT`
  —— 不是笼统的「gate rejected」。
- **对照（建档时的读数）**：未声明时同一场景是 `records: 1`、`panels: []` —— 第二位
  评审者从未运行。

### EC-02 —— 语义只对**显式声明**生效

- **反证臂**：同一份协议、同一批交付物，只去掉 `review_panel: COMPLETE_THEN_JUDGE`
  ⇒ `records == 1`、`panels == []`、消息是既有的 `rejected by acceptance gate` 形态，
  **不含** `review panel rejected`。⇒ 声明是**承诺**，不是默认。

### EC-03 —— 分歧可读且**按压翻转**

- **一负一过**：`votes == {"PASS": 1, "REJECT": 1}`、`advisory is None`（平票不猜）、
  `dissent == ["gate:reviewer_a:REJECT", "gate:reviewer_b:PASS"]`。
- **按压（两位都判负）**：`advisory == "REJECT"`、`dissent == []` —— 分歧消失，读数随之变。

### 连带修掉的一处真缺口（如实登记）

- **平票时 `dissent == []`**：`panel_verdict._dissent` 原先只在 `advisory is not None` 时记录
  ⇒ **分歧最大的那一刻反而读不到分歧**。现在平票 ⇒ 每票都列（没有多数，就都是少数）。
- **不是放宽**：既有的平票判据只断言 `advisory is None` 与 `decided is False`，
  **没有**断言 `dissent`；新增行为只让载荷多出内容，**没有削弱任何断言**。

### 首轮抓到的一处**真回归**（如实登记，不掩盖）

- 组末判定起初把 `on_task_failure: CONTINUE` 的**被容忍失败**也算成判负 ⇒
  `test_failure_policy_consumer.py` 的**三处**既有用例同时变红
  （`runs == 2`（应为 3）、`FAILED`（应为 `DEGRADED`）、`degraded` 为空）。
- **处置**：组末判定只认**本模块记账的**判负（`failure_policy is COMPLETE_THEN_JUDGE`）——
  两个声明面互不越界。修后该文件 **9 passed**。

### 零回归与静态门

| 面 | 读数 |
| --- | --- |
| `tests/application tests/contracts tests/api` | **2411 passed, 77 skipped** |
| `tests/e2e`（全量） | **363 passed, 17 skipped** |
| 评审面板定向（4 份） | **27 passed** |
| `ruff check` / `ruff format --check` / `mypy`（58 文件） | 全绿 |

## 结论

**PASS**。EC-01…EC-04 达成，两个方向都实测（声明 ⇒ 全体评完且仍判负；未声明 ⇒ 既有
fail-fast），按压使三处读数同时翻转，连带修掉 `dissent` 的平票盲区，并修回溯出的一处真回归。
EC-05（自举收口）由收口 cycle 承担 —— 本文件的 PASS **不**覆盖它。
